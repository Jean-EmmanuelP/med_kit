import os
import requests
import re
import json
import time
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from typing import List, Dict, Optional, Set, Any
# Import Supabase/Postgrest exceptions if needed for more specific handling
# from postgrest import APIError as PostgrestAPIError

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
google_api_key = os.environ.get("GOOGLE_API_KEY")

BATCH_SIZE = 50 # Reduced batch size for testing local saving
ARTICLES_TABLE = "articles"
ARTICLE_DISCIPLINES_TABLE = "article_disciplines"
ARTICLE_SUB_DISCIPLINES_TABLE = "article_sub_disciplines" # Still needed for table name ref
DISCIPLINES_TABLE = "disciplines"
SUB_DISCIPLINES_TABLE = "sub_disciplines"

SUBDISCIPLINE_PROMPT_FILE = "subdiscipline_prompt.txt"
SUBDISCIPLINE_ARBITRATION_PROMPT_FILE = "subdiscipline_arbitration_prompt.txt"
GEMINI_MODEL = "gemini-2.0-flash"
RETRY_DELAY_SECONDS = 20
MAX_RETRIES_GEMINI = 5
AUTRES_SUBDISCIPLINE_NAME = "Autres"
SAVE_DIR = "saved_results" # Directory to save JSON results

# --- Helper Functions ---

# fetch_html, get_abstract_text, load_prompt_template remain the same...
def fetch_html(url: str) -> Optional[str]:
    """Fetches HTML content from a URL."""
    if not url or not url.startswith(('http://', 'https://')):
        logging.warning(f"Invalid URL provided: {url}")
        return None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        logging.info(f"Fetching HTML from: {url}")
        response = requests.get(url, headers=headers, timeout=30) # Increased timeout slightly
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        if 'text/html' not in content_type and not content_type.startswith('application/xhtml'):
             logging.warning(f"Content-Type is not explicitly HTML for {url} ({content_type}). Attempting to parse anyway...")
        return response.text
    except requests.exceptions.Timeout:
        logging.error(f"Timeout error fetching URL {url}")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        logging.error(f"An unexpected error occurred during fetch for {url}: {e}")
        return None

def get_abstract_text(html_content: str) -> Optional[str]:
    """Extracts plain text from the abstract HTML (adapted for PubMed)."""
    if not html_content:
        logging.warning("No HTML content provided to extract abstract.")
        return None
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        abstract_div = soup.find('div', {'id': 'abstract', 'class': 'abstract'})

        if not abstract_div:
             # Fallback: Look for common abstract patterns if the primary ID fails
            possible_abstract_parents = soup.find_all(['div', 'section'], {'class': lambda x: x and 'abstract' in x.lower()})
            if possible_abstract_parents:
                abstract_div = possible_abstract_parents[0] # Take the first likely candidate
            else:
                logging.warning("Could not find a standard abstract container (id='abstract' or class containing 'abstract').")
                # Attempt to get general text content if specific container fails
                main_content = soup.find('main') or soup.find('article') or soup.body
                if main_content:
                    return main_content.get_text(separator=' ', strip=True)
                else:
                     return soup.get_text(separator=' ', strip=True) # Last resort


        # --- Standard PubMed Structure Extraction ---
        abstract_content_div = abstract_div.find('div', class_='abstract-content')
        if abstract_content_div:
            # Extract text from common paragraph/div tags within the content div
            # Look for paragraphs or divs directly under abstract-content
            text_parts = [p.get_text(separator=' ', strip=True)
                          for p in abstract_content_div.find_all(['p', 'div'], recursive=False)
                          if p.get_text(strip=True)] # Ensure part has content

            # Handle structured abstracts (e.g., BACKGROUND:, METHODS:, etc.) often in <strong> tags
            structured_parts = abstract_content_div.find_all(['strong', 'h3', 'h4'], recursive=True) # Look deeper for headers
            if structured_parts and not text_parts: # If only structured parts found
                 # Try getting text around these headers
                 text_parts = [elem.parent.get_text(separator=' ', strip=True) for elem in structured_parts]


            if not text_parts: # Fallback if the direct child approach fails
                 abstract_text = abstract_content_div.get_text(separator=' ', strip=True)
            else:
                 abstract_text = "\n\n".join(part for part in text_parts if part) # Join non-empty parts

            return abstract_text.strip() if abstract_text else None

        # Fallback if abstract-content div is not found within the main abstract div
        return abstract_div.get_text(separator=' ', strip=True)

    except Exception as e:
        logging.error(f"Error parsing HTML or extracting abstract text: {e}", exc_info=True)
        return None

def load_prompt_template(filepath: str) -> Optional[str]:
    """Loads the prompt template from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logging.error(f"Prompt file not found: {filepath}")
        return None
    except Exception as e:
        logging.error(f"Error reading prompt file {filepath}: {e}")
        return None

# get_gemini_classification_single, get_validated_subdisciplines remain the same...
def get_gemini_classification_single(formatted_prompt: str, model: genai.GenerativeModel) -> Optional[List[str]]:
    """
    Gets a classification (list of strings) from Gemini, handles retries and JSON parsing.
    """
    if not formatted_prompt or not model:
        logging.warning("Missing formatted prompt or model for classification.")
        return None

    attempts = 0
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    while attempts < MAX_RETRIES_GEMINI:
        attempts += 1
        try:
            logging.info(f"Sending request to Gemini for classification (Attempt {attempts}/{MAX_RETRIES_GEMINI})...")
            response = model.generate_content(formatted_prompt, safety_settings=safety_settings)

            # --- Successful Response Processing ---
            if not response.parts:
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    logging.error(f"Gemini request blocked. Reason: {response.prompt_feedback.block_reason}")
                else:
                    logging.error("Gemini response was empty or incomplete.")
                return None # Don't retry for blocks or empty responses

            raw_text = response.text.strip()
            logging.debug(f"Raw Gemini response: '{raw_text}'")

            # Attempt to parse the response as JSON
            try:
                # Clean potential markdown code block fences
                cleaned_text = re.sub(r'^```json\s*', '', raw_text, flags=re.IGNORECASE | re.MULTILINE)
                cleaned_text = re.sub(r'\s*```$', '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
                cleaned_text = cleaned_text.strip()

                result = json.loads(cleaned_text)

                # Validate the parsed result
                if isinstance(result, list) and all(isinstance(item, str) for item in result):
                    logging.info(f"Successfully parsed classification result: {result}")
                    return result # Success!
                else:
                    logging.warning(f"Parsed JSON is not a list of strings: {result}")
                    return None # Invalid format

            except json.JSONDecodeError as json_e:
                logging.warning(f"Failed to parse Gemini response as JSON: {json_e}. Response text: '{raw_text}'")
                # Consider if a retry makes sense here, maybe not if format is consistently wrong
                return None # Parsing failed

        # --- Error Handling ---
        except google_exceptions.ResourceExhausted as e:
            logging.warning(f"Gemini API rate limit exceeded (429): {e}")
            if attempts == MAX_RETRIES_GEMINI:
                logging.error("Max retries reached after rate limit error. Failing classification.")
                return None
            logging.info(f"Waiting for {RETRY_DELAY_SECONDS} seconds before retrying...")
            time.sleep(RETRY_DELAY_SECONDS)
            # Continue loop for retry

        except Exception as e:
            logging.error(f"Error during Gemini API call (Attempt {attempts}): {e}", exc_info=True)
            return None # Don't retry for other errors

    logging.error("Exited retry loop without success due to persistent errors.")
    return None

def get_validated_subdisciplines(abstract_text: str, candidate_list_string: str, model: genai.GenerativeModel, base_prompt_template: str, arbitration_prompt_template: str) -> Optional[List[str]]:
    """Performs double-check and arbitration to get a validated list of subdisciplines."""
    if not all([abstract_text, candidate_list_string, model, base_prompt_template, arbitration_prompt_template]):
        logging.error("Missing required inputs for validated classification.")
        return None

    # --- First Call ---
    logging.info("Requesting first classification...")
    prompt1 = base_prompt_template.format(abstract_text=abstract_text, sub_discipline_list=candidate_list_string)
    result1 = get_gemini_classification_single(prompt1, model)
    if result1 is None:
        logging.error("Failed to get first classification.")
        # It could be an empty list [] which is valid, so check for None explicitly
        return None
    logging.info(f"First classification received: {result1}")

    # --- Second Call (with slight prompt variation - less critical here than grading) ---
    logging.info("Requesting second classification...")
    # Minimal variation, perhaps just changing a preamble word
    prompt_variation = base_prompt_template.replace("Abstract to Analyze:", "Abstract for Second Review:")
    prompt2 = prompt_variation.format(abstract_text=abstract_text, sub_discipline_list=candidate_list_string)
    time.sleep(1) # Small delay between distinct API calls
    result2 = get_gemini_classification_single(prompt2, model)
    if result2 is None:
        logging.error("Failed to get second classification.")
        return None
    logging.info(f"Second classification received: {result2}")

    # --- Comparison ---
    # Compare sets for order independence
    if set(result1) == set(result2):
        logging.info(f"Classifications match: {result1}. Validation successful.")
        return result1 # Return the first list (or second, they are equivalent)
    else:
        logging.warning(f"Classifications differ: Result 1={result1}, Result 2={result2}. Proceeding to arbitration.")

        # --- Third Call (Arbitration) ---
        logging.info("Requesting arbitration classification...")
        arbitration_prompt_formatted = arbitration_prompt_template.format(
            abstract_text=abstract_text,
            sub_discipline_list=candidate_list_string,
            result1=json.dumps(result1), # Pass results as JSON strings for the prompt
            result2=json.dumps(result2)
        )
        time.sleep(1) # Small delay before arbitration call
        final_result = get_gemini_classification_single(arbitration_prompt_formatted, model)

        if final_result is None:
            logging.error("Failed to obtain arbitration classification. Validation failed.")
            return None

        logging.info(f"Arbitration completed. Final classification determined: {final_result}")
        return final_result

# MODIFIED: Function to only GET existing "Autres" ID
def get_existing_autres_subdiscipline_id(supabase_client: Client, discipline_id: int) -> Optional[int]:
    """Gets the ID of the 'Autres' subdiscipline for a given discipline IF IT EXISTS."""
    if not supabase_client:
        logging.error("Supabase client not available for get_existing_autres_id.")
        return None

    try:
        # Check if 'Autres' exists for this discipline using execute() and handle potential errors
        select_response = supabase_client.table(SUB_DISCIPLINES_TABLE)\
            .select("id")\
            .eq("discipline_id", discipline_id)\
            .eq("name", AUTRES_SUBDISCIPLINE_NAME)\
            .limit(1)\
            .execute()

        # Check the response data after successful execution
        if select_response.data:
            autres_id = select_response.data[0]['id']
            logging.info(f"Found existing '{AUTRES_SUBDISCIPLINE_NAME}' sub-discipline (ID: {autres_id}) for discipline {discipline_id}.")
            return autres_id
        else:
            # Not found is not an error in this context
            logging.info(f"'{AUTRES_SUBDISCIPLINE_NAME}' sub-discipline does not exist for discipline {discipline_id}.")
            return None

    except Exception as e: # Catch potential exceptions from .execute()
         # Log the specific Supabase error
         logging.error(f"Supabase error checking for '{AUTRES_SUBDISCIPLINE_NAME}' for discipline {discipline_id}: {e}")
         return None

# REMOVED: update_article_classification_status function

# NEW: Function to save results to a file
def save_result_to_file(data: Dict[str, Any], save_dir: str):
    """Saves the classification result data to a JSON file."""
    article_id = data.get("article_id", "unknown_article")
    filename = f"{article_id}.json"
    filepath = os.path.join(save_dir, filename)

    try:
        os.makedirs(save_dir, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Successfully saved classification result for article {article_id} to {filepath}")
    except OSError as e:
        logging.error(f"Error creating directory {save_dir}: {e}")
    except IOError as e:
        logging.error(f"Error writing result to file {filepath}: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred saving result for article {article_id}: {e}", exc_info=True)


# --- Main Execution ---
if __name__ == "__main__":
    # --- Initialize ---
    if not all([supabase_url, supabase_key, google_api_key]):
        logging.error("Error: Supabase URL/Key or Google API Key missing in .env file.")
        exit(1)

    supabase: Optional[Client] = None
    gemini_model: Optional[genai.GenerativeModel] = None
    subdiscipline_prompt: Optional[str] = None
    arbitration_prompt: Optional[str] = None

    # Ensure SAVE_DIR exists
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        logging.info(f"Results will be saved in: {os.path.abspath(SAVE_DIR)}")
    except OSError as e:
        logging.error(f"Could not create save directory '{SAVE_DIR}': {e}. Exiting.")
        exit(1)

    try:
        logging.info("Initializing Supabase client...")
        supabase = create_client(supabase_url, supabase_key)
        logging.info("Supabase client initialized.")

        logging.info("Configuring Google AI...")
        genai.configure(api_key=google_api_key)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        logging.info(f"Google AI configured with model: {GEMINI_MODEL}")

        logging.info(f"Loading base prompt from {SUBDISCIPLINE_PROMPT_FILE}...")
        subdiscipline_prompt = load_prompt_template(SUBDISCIPLINE_PROMPT_FILE)
        if not subdiscipline_prompt: exit(1)

        logging.info(f"Loading arbitration prompt from {SUBDISCIPLINE_ARBITRATION_PROMPT_FILE}...")
        arbitration_prompt = load_prompt_template(SUBDISCIPLINE_ARBITRATION_PROMPT_FILE)
        if not arbitration_prompt: exit(1)

    except Exception as e:
        logging.error(f"Error during initialization: {e}", exc_info=True)
        exit(1)

    if not all([supabase, gemini_model, subdiscipline_prompt, arbitration_prompt]):
         logging.error("Critical component(s) failed to initialize. Exiting.")
         exit(1)

    # --- Fetch Articles ---
    logging.info(f"Attempting to fetch next batch of up to {BATCH_SIZE} articles (for local saving test)...")
    articles_to_process = []
    try:
        # First get all article IDs
        id_response = supabase.table(ARTICLES_TABLE)\
                            .select("id")\
                            .not_.is_("link", None)\
                            .execute()
        
        if not id_response.data:
            logging.info("No articles found to process.")
            exit(0)
            
        # Get random sample of IDs
        import random
        all_ids = [article['id'] for article in id_response.data]
        random_ids = random.sample(all_ids, min(BATCH_SIZE, len(all_ids)))
        
        # Fetch the full article data for the random IDs
        response = supabase.table(ARTICLES_TABLE)\
                           .select("id, link")\
                           .in_("id", random_ids)\
                           .execute()
        
        articles_to_process = response.data
        logging.info(f"Successfully fetched {len(articles_to_process)} articles to process.")

        # Shuffle the results after fetching
        import random
        random.shuffle(articles_to_process)

    except Exception as e: # Catch potential exceptions from .execute()
        logging.exception(f"Supabase error fetching articles: {e}")
        exit(1) # Exit if we can't even query the DB initially

    # --- Process Articles ---
    processed_count = 0
    error_in_processing = 0 # Track articles that had errors during processing

    for article in articles_to_process:
        article_id = article.get('id')
        article_link = article.get('link')
        result_data = { # Prepare data structure for saving
            "article_id": article_id,
            "article_link": article_link,
            "status": "ERROR", # Default status
            "error_message": None,
            "llm_chosen_names": None,
            "assigned_sub_discipline_ids": [],
            "parent_discipline_ids": [],
            "candidate_subdiscipline_names": []
        }

        logging.info(f"--- Processing Article ID: {article_id} (Link: {article_link}) ---")

        try:
            # 1. Fetch and Extract Abstract
            html_content = fetch_html(article_link)
            if not html_content:
                result_data["error_message"] = "Could not fetch HTML"
                logging.warning(f"{result_data['error_message']} for article {article_id}.")
                error_in_processing += 1
                save_result_to_file(result_data, SAVE_DIR) # Save error state
                continue

            abstract_text = get_abstract_text(html_content)
            if not abstract_text:
                result_data["error_message"] = "Could not extract abstract text"
                logging.warning(f"{result_data['error_message']} for article {article_id}.")
                error_in_processing += 1
                save_result_to_file(result_data, SAVE_DIR) # Save error state
                continue
            logging.info(f"Abstract extracted successfully for article {article_id} (length: {len(abstract_text)} chars).")


            # 2. Get Associated Disciplines
            parent_discipline_ids = [] # Initialize
            try:
                discipline_response = supabase.table(ARTICLE_DISCIPLINES_TABLE)\
                                            .select("discipline_id")\
                                            .eq("article_id", article_id)\
                                            .execute()
                # Check data after successful execution
                if not discipline_response.data:
                    result_data["error_message"] = "Article not associated with any disciplines."
                    logging.warning(f"{result_data['error_message']} for article {article_id}.")
                    error_in_processing += 1
                    save_result_to_file(result_data, SAVE_DIR)
                    continue

                parent_discipline_ids = [d['discipline_id'] for d in discipline_response.data]
                result_data["parent_discipline_ids"] = parent_discipline_ids
                logging.info(f"Article {article_id} belongs to disciplines: {parent_discipline_ids}")

            except Exception as e: # Catch potential exceptions from .execute()
                result_data["error_message"] = f"Supabase error fetching disciplines: {str(e)}"
                logging.error(f"Supabase error fetching disciplines for article {article_id}: {e}")
                error_in_processing += 1
                save_result_to_file(result_data, SAVE_DIR)
                continue


            # 3. Get Candidate Sub-disciplines (excluding 'Autres')
            candidates_by_discipline: Dict[int, List[Dict[str, Any]]] = {}
            all_candidate_subdisciplines: List[Dict[str, Any]] = []
            sub_name_to_details_lower: Dict[str, Dict[str, Any]] = {}

            try:
                sub_response = supabase.table(SUB_DISCIPLINES_TABLE)\
                                    .select("id, name, discipline_id")\
                                    .in_("discipline_id", parent_discipline_ids)\
                                    .neq("name", AUTRES_SUBDISCIPLINE_NAME)\
                                    .execute()
                # Process data after successful execution
                if sub_response.data:
                    all_candidate_subdisciplines = sub_response.data
                    for sub in all_candidate_subdisciplines:
                        d_id = sub['discipline_id']
                        if d_id not in candidates_by_discipline:
                            candidates_by_discipline[d_id] = []
                        candidates_by_discipline[d_id].append({"id": sub['id'], "name": sub['name']})
                        sub_name_to_details_lower[sub['name'].lower()] = {"id": sub['id'], "discipline_id": d_id}

                if not all_candidate_subdisciplines:
                    logging.warning(f"No specific sub-disciplines (excluding '{AUTRES_SUBDISCIPLINE_NAME}') found for the disciplines {parent_discipline_ids} associated with article {article_id}.")

                candidate_names = sorted([sub['name'] for sub in all_candidate_subdisciplines])
                result_data["candidate_subdiscipline_names"] = candidate_names
                candidate_list_string = ", ".join(candidate_names)
                logging.info(f"Candidate sub-disciplines for LLM: [{candidate_list_string}]")

            except Exception as e: # Catch potential exceptions from .execute()
                result_data["error_message"] = f"Supabase error fetching candidates: {str(e)}"
                logging.error(f"Supabase error fetching candidate sub-disciplines for article {article_id}: {e}")
                error_in_processing += 1
                save_result_to_file(result_data, SAVE_DIR)
                continue


            # 4. Pre-Classification Cleanup - REMOVED DB DELETE


            # 5. Get Validated Classification from LLM
            validated_chosen_names = get_validated_subdisciplines(
                abstract_text,
                candidate_list_string,
                gemini_model,
                subdiscipline_prompt,
                arbitration_prompt
            )
            result_data["llm_chosen_names"] = validated_chosen_names # Store LLM output regardless of success

            if validated_chosen_names is None:
                result_data["error_message"] = "Failed to get validated classification from LLM."
                logging.error(f"{result_data['error_message']} for article {article_id}.")
                error_in_processing += 1
                save_result_to_file(result_data, SAVE_DIR)
                continue

            logging.info(f"LLM validation successful for article {article_id}. Chosen names: {validated_chosen_names}")


            # 6. Process LLM Result & Assign "Autres"
            sub_discipline_ids_to_insert: Set[int] = set()
            chosen_names_set_lower = set(name.lower() for name in validated_chosen_names)
            assigned_specific_sub = False

            for disc_id in parent_discipline_ids:
                found_match_in_this_discipline = False
                # Check if any *specific* sub chosen belongs to *this* discipline using lowercase lookup
                for chosen_name_lower in chosen_names_set_lower:
                    details = sub_name_to_details_lower.get(chosen_name_lower) # Use the lowercase dict
                    if details and details['discipline_id'] == disc_id:
                         sub_discipline_ids_to_insert.add(details['id'])
                         found_match_in_this_discipline = True
                         assigned_specific_sub = True # Mark that at least one specific sub was assigned overall

                # If no *specific* sub for *this* discipline was chosen by the LLM
                if not found_match_in_this_discipline:
                    logging.info(f"No specific sub-discipline chosen for discipline {disc_id}. Checking for existing '{AUTRES_SUBDISCIPLINE_NAME}'.")
                    # Use the modified function that ONLY GETS the ID
                    autres_id = get_existing_autres_subdiscipline_id(supabase, disc_id)
                    if autres_id is not None:
                        sub_discipline_ids_to_insert.add(autres_id)
                    else:
                        logging.warning(f"Existing '{AUTRES_SUBDISCIPLINE_NAME}' sub-discipline not found for discipline {disc_id}. It won't be assigned.")

            result_data["assigned_sub_discipline_ids"] = sorted(list(sub_discipline_ids_to_insert))
            result_data["status"] = "SUCCESS" # Assume success if we got this far
            processed_count += 1

        except Exception as e:
            logging.exception(f"An unexpected critical error occurred processing article ID {article_id}.")
            result_data["status"] = "CRITICAL_ERROR"
            result_data["error_message"] = str(e)
            error_in_processing += 1
            # Save the error state even if loop breaks
            save_result_to_file(result_data, SAVE_DIR)
            continue # Continue to next article after saving critical error state

        # 7. Save Result to File (only if no critical error occurred above)
        save_result_to_file(result_data, SAVE_DIR)

        print("-" * 80) # Separator
        time.sleep(0.5) # Reduced delay slightly for local testing

    logging.info(f"Script finished processing batch.")
    logging.info(f"Articles processed (attempted): {len(articles_to_process)}")
    logging.info(f"Results saved successfully (status='SUCCESS'): {processed_count}")
    logging.info(f"Articles with processing errors (check saved files/logs): {error_in_processing}")