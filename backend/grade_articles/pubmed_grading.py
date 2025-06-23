import os
import requests
import re
import json # Still useful for potential future logging/debugging
import time
from bs4 import BeautifulSoup
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions # Import specific exception

# Import the specific exception for rate limiting if available
from google.api_core import exceptions as google_exceptions
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
google_api_key = os.environ.get("GOOGLE_API_KEY")

BATCH_SIZE = 2000 # Increased batch size slightly for potentially faster processing
TABLE_NAME = "articles" # Targeting the 'articles' table for updates
PROMPT_FILE = "prompt.txt"
ARBITRATION_PROMPT_FILE = "arbitration_prompt.txt"
GEMINI_MODEL = "gemini-2.0-flash"
# SAVE_DIR = "saved_grades" # Removed - no longer saving to files
RETRY_DELAY_SECONDS = 20 # User-requested delay for rate limits

# --- Helper Functions ---

def fetch_html(url: str) -> str | None:
    """Fetches HTML content from a URL."""
    if not url or not url.startswith(('http://', 'https://')):
        logging.warning(f"Invalid URL provided: {url}")
        return None
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        logging.info(f"Fetching HTML from: {url}")
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '').lower()
        # Check if content type is likely HTML
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

def extract_pubmed_abstract_html(html_content: str) -> str | None:
    """Extracts the abstract div HTML from PubMed page content."""
    if not html_content:
        logging.warning("No HTML content provided to extract abstract.")
        return None
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # PubMed uses specific IDs and classes for the abstract
        abstract_div = soup.find('div', id='abstract', class_='abstract')
        if abstract_div:
            # Return the HTML of the abstract div including tags
            return str(abstract_div) # Use str() or prettify()
        else:
            logging.warning("Abstract div with id='abstract' and class_='abstract' not found.")
            return None
    except Exception as e:
        logging.error(f"Error parsing HTML for abstract: {e}")
        return None

def get_abstract_text(html_content: str) -> str | None:
    """Extracts plain text from the abstract HTML."""
    if not html_content:
        logging.warning("No abstract HTML content provided to extract text.")
        return None
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Find the main abstract content area, often nested
        abstract_content_div = soup.find('div', class_='abstract-content')

        if abstract_content_div:
            # Extract text from common paragraph/div tags within the content div
            text_parts = [p.get_text(separator=' ', strip=True) for p in abstract_content_div.find_all(['p', 'div'], recursive=False)]
            # Some abstracts have sections, combine them
            abstract_text = "\n\n".join(text_parts).strip()
            if not abstract_text: # Fallback if the structured approach fails
                 abstract_text = abstract_content_div.get_text(separator=' ', strip=True)
            return abstract_text if abstract_text else None

        # Fallback if abstract-content div is not found (less common on PubMed)
        return soup.get_text(separator=' ', strip=True) # Gets text from the entire passed HTML snippet

    except Exception as e:
        logging.error(f"Error extracting plain text from abstract HTML: {e}")
        return None

def load_prompt_template(filepath: str) -> str | None:
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

def get_gemini_grade_single(abstract_text: str, model: genai.GenerativeModel, formatted_prompt: str) -> str | None:
    """
    Gets a single grade from Gemini based on a pre-formatted prompt.
    Includes logic to handle rate limits (429 errors) with retries.
    """
    if not abstract_text or not model or not formatted_prompt:
        logging.warning("Missing abstract text, model, or formatted prompt for grading.")
        return None

    max_retries = 5
    attempts = 0
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    }

    while attempts < max_retries: # Changed to < max_retries to perform max_retries total attempts
        attempts += 1
        try:
            logging.info(f"Sending request to Gemini (Attempt {attempts}/{max_retries})...")
            response = model.generate_content(formatted_prompt, safety_settings=safety_settings)

            # --- Successful Response Processing ---
            if not response.parts:
                 if response.prompt_feedback and response.prompt_feedback.block_reason:
                     logging.error(f"Gemini request blocked. Reason: {response.prompt_feedback.block_reason}")
                 else:
                     logging.error("Gemini response was empty or incomplete.")
                 return None # Don't retry for blocks or empty responses that aren't rate limits

            grade_text = response.text.strip()
            logging.debug(f"Raw Gemini response: '{grade_text}'") # Changed to debug, can be verbose
            match = re.search(r'\b(A|B|C|Accord d\'experts)\b', grade_text, re.IGNORECASE)

            if match:
                grade = match.group(1).strip() # Ensure no leading/trailing whitespace
                # Normalize 'Accord d\'experts' to 'Accord d\'experts' exactly (case-insensitive match but keep original if needed, here we normalize)
                grade = 'Accord d\'experts' if grade.lower() == 'accord d\'experts' else grade.upper()

                if grade in ['A', 'B', 'C', 'Accord d\'experts']:
                    logging.info(f"Extracted grade: {grade}")
                    return grade # Success! Exit the loop by returning.
                else:
                    # This path should ideally not be hit if regex matches, but kept for safety
                    logging.warning(f"Extracted text '{grade}' from match is not a valid target grade.")
                    return None # Invalid grade extracted

            else:
                logging.warning(f"Could not extract valid grade (A, B, C, Accord d'experts) from Gemini response: '{grade_text}'")
                # If the response doesn't contain a recognizable grade, consider it a failure for this call
                return None # Parsing failed - don't retry for this

        # --- Error Handling ---
        except google_exceptions.ResourceExhausted as e:
            logging.warning(f"Gemini API rate limit exceeded (429): {e}")
            if attempts == max_retries:
                logging.error("Max retries reached after rate limit error. Failing grade.")
                return None
            delay = RETRY_DELAY_SECONDS # Use user-requested delay
            logging.info(f"Waiting for {delay} seconds before retrying...")
            time.sleep(delay)
            # Continue loop for retry

        except Exception as e:
            # Catch other potential API errors (network issues, bad requests, etc.)
            logging.error(f"Error during Gemini API call (Attempt {attempts}): {e}", exc_info=True)
            # For non-rate limit errors, don't retry the API call
            return None

    # If the loop finishes without returning (only happens if all attempts fail due to rate limit)
    logging.error("Exited retry loop without success due to persistent rate limits.")
    return None


def get_validated_grade(abstract_text: str, model: genai.GenerativeModel, base_prompt_template: str, arbitration_prompt_template: str) -> str | None:
    """Performs double-check and arbitration to get a validated grade."""
    if not all([abstract_text, model, base_prompt_template, arbitration_prompt_template]):
        logging.error("Missing required inputs for validated grading.")
        return None

    # --- First Call ---
    logging.info("Requesting first grade...")
    prompt1 = base_prompt_template.format(abstract_text=abstract_text)
    grade1 = get_gemini_grade_single(abstract_text, model, prompt1)
    if grade1 is None:
        logging.error("Failed to get first grade.")
        return None
    logging.info(f"First grade received: {grade1}")

    # --- Second Call (with slight prompt variation) ---
    # Varying the prompt slightly can sometimes help avoid cached responses or biases
    logging.info("Requesting second grade...")
    prompt_variation = base_prompt_template.replace(
        "Abstract to Grade:\n---",
        "Abstract for Second Review:\n>>>"
    ).replace("---", "<<<")
    prompt2 = prompt_variation.format(abstract_text=abstract_text)
    time.sleep(1) # Small delay between distinct API calls to be polite/avoid immediate sequence issues
    grade2 = get_gemini_grade_single(abstract_text, model, prompt2)
    if grade2 is None:
        logging.error("Failed to get second grade.")
        return None
    logging.info(f"Second grade received: {grade2}")

    # --- Comparison ---
    if grade1 == grade2:
        logging.info(f"Grades match: {grade1}. Validation successful.")
        return grade1
    else:
        logging.warning(f"Grades differ: Grade 1='{grade1}', Grade 2='{grade2}'. Proceeding to arbitration.")

        # --- Third Call (Arbitration) ---
        logging.info("Requesting arbitration grade...")
        arbitration_prompt_formatted = arbitration_prompt_template.format(
            abstract_text=abstract_text,
            grade1=grade1,
            grade2=grade2
        )
        time.sleep(1) # Small delay before arbitration call
        final_grade = get_gemini_grade_single(abstract_text, model, arbitration_prompt_formatted)

        if final_grade is None:
            logging.error("Failed to obtain arbitration grade. Validation failed.")
            return None

        # Arbitration might pick one of the original grades or potentially something else
        # We trust the arbitration result as the final decision after disagreement
        logging.info(f"Arbitration completed. Final grade determined: {final_grade}")
        return final_grade

def update_article_grade_status(supabase_client: Client, article_id: int, validated_grade: str | None, status: str):
    """
    Updates the 'grade' and 'graded_yet' columns in the 'articles' table.

    Args:
        supabase_client: The initialized Supabase client.
        article_id: The ID of the article to update.
        validated_grade: The final grade string ('A', 'B', 'C', 'Accord d\'experts')
                         or None if grading failed.
        status: The status to set 'graded_yet' to ('TRUE' or 'ERROR').
    """
    if not supabase_client:
        logging.error(f"Supabase client is not initialized. Cannot update article {article_id}.")
        return

    update_data = {
        "graded_yet": status # 'TRUE' or 'ERROR'
    }

    # Map 'Accord d\'experts' to 'C' for the database
    if validated_grade is not None:
        mapped_grade = 'C' if validated_grade == 'Accord d\'experts' else validated_grade
        update_data["grade"] = mapped_grade
        logging.info(f"Mapping validated grade '{validated_grade}' to '{mapped_grade}' for DB.")
    else:
        # If grading failed, we don't update the 'grade' column, just set status to 'ERROR'
        logging.warning(f"No validated grade available for article {article_id}. Setting status to '{status}'.")


    try:
        logging.info(f"Updating article {article_id} in Supabase with grade={update_data.get('grade', 'N/A')} and graded_yet='{status}'...")
        response = supabase_client.table(TABLE_NAME)\
                                  .update(update_data)\
                                  .eq("id", article_id)\
                                  .execute()

        # Check for errors in the response
        if response.data is not None:
             logging.info(f"Successfully updated article {article_id} in Supabase.")
        else:
             # Supabase update errors can sometimes be silent if not raised as exceptions,
             # but checking response.data is a good practice.
             # Note: response.error is often the primary way to check for errors
             if response.error:
                 logging.error(f"Supabase error updating article {article_id}: {response.error}")
                 # Consider retrying the update itself if needed, but for now, log and move on
             else:
                  # This might happen if the ID wasn't found, which shouldn't happen if we queried correctly
                  logging.warning(f"Supabase update for article {article_id} completed with no data returned (ID might not exist?).")


    except Exception as e:
        logging.error(f"An unexpected error occurred during Supabase update for article {article_id}: {e}", exc_info=True)
        # Note: If the initial update fails due to connection/auth, this catches it.
        # We already set status to 'ERROR' in the main loop before calling this in failure cases,
        # but if the *update itself* fails, the status won't be set correctly.
        # A more robust system might involve a queue or more complex retry logic here.


# Removed: get_processed_ids - We now query based on 'graded_yet'
# Removed: save_grade_to_file - We now update the database

# --- Main Execution ---
if __name__ == "__main__":
    if not supabase_url or not supabase_key:
        logging.error("Error: Supabase URL or Key is missing. Set them in a .env file.")
        exit(1)
    if not google_api_key:
        logging.error("Error: GOOGLE_API_KEY is missing. Set it in the .env file.")
        exit(1)

    # --- Initialize Clients and Load Prompts ---
    supabase: Client | None = None
    gemini_model: genai.GenerativeModel | None = None
    base_prompt_template: str | None = None
    arbitration_prompt_template: str | None = None

    try:
        logging.info("Initializing Supabase client...")
        # Initialize Supabase client with the project URL and public key
        supabase: Client = create_client(supabase_url, supabase_key)
        logging.info("Supabase client initialized successfully.")

        logging.info("Configuring Google AI...")
        genai.configure(api_key=google_api_key)
        # It's good practice to check if the model exists or is available
        try:
            gemini_model = genai.GenerativeModel(GEMINI_MODEL)
            logging.info(f"Google AI configured with model: {GEMINI_MODEL}")
        except Exception as e:
             logging.error(f"Error initializing Gemini model '{GEMINI_MODEL}': {e}")
             gemini_model = None # Set to None if initialization fails


        logging.info(f"Loading base prompt template from {PROMPT_FILE}...")
        base_prompt_template = load_prompt_template(PROMPT_FILE)
        if not base_prompt_template: exit(1) # Exit if main prompt isn't loaded
        logging.info("Base prompt template loaded successfully.")

        logging.info(f"Loading arbitration prompt template from {ARBITRATION_PROMPT_FILE}...")
        arbitration_prompt_template = load_prompt_template(ARBITRATION_PROMPT_FILE)
        if not arbitration_prompt_template: exit(1) # Exit if arbitration prompt isn't loaded
        logging.info("Arbitration prompt template loaded successfully.")

    except Exception as e:
        logging.error(f"Error during initialization: {e}")
        exit(1)

    # Ensure critical resources are initialized
    if not all([supabase, gemini_model, base_prompt_template, arbitration_prompt_template]):
         logging.error("Critical component(s) failed to initialize. Exiting.")
         exit(1)


    # --- Fetch and Process Articles ---
    logging.info(f"Attempting to fetch next batch of up to {BATCH_SIZE} UNGRADED articles...")
    try:
        # Query articles where 'graded_yet' is 'FALSE' and link is not null
        response = supabase.table(TABLE_NAME).select("id, link").eq("graded_yet", "FALSE").neq("link", None).order("id", desc=False).limit(BATCH_SIZE).execute()

        if response.data:
            articles = response.data
            logging.info(f"Successfully fetched {len(articles)} new articles to process (graded_yet='FALSE').")
        elif response.error:
             logging.error(f"Supabase query error: {response.error}")
             articles = [] # No articles to process if query failed
        else:
            articles = []
            logging.info("No new unprocessed articles found matching the criteria (graded_yet='FALSE' with link).")


        for article in articles:
            article_id = article.get('id')
            article_link = article.get('link')

            if not article_link:
                logging.warning(f"Skipping article ID {article_id} due to missing link (unexpected from query).")
                # Should not happen with .neq("link", None), but safe check
                update_article_grade_status(supabase, article_id, None, "ERROR")
                continue

            logging.info(f"--- Processing Article ID: {article_id} (Link: {article_link}) ---")

            html_content = fetch_html(article_link)

            abstract_text = None # Initialize abstract_text to None

            if html_content:
                # abstract_html_pretty = extract_pubmed_abstract_html(html_content) # This is not strictly needed for the text
                abstract_text = get_abstract_text(html_content)

                if abstract_text:
                    logging.info("Abstract text extracted successfully. Starting validation process...")
                    final_grade = get_validated_grade(
                        abstract_text,
                        gemini_model,
                        base_prompt_template,
                        arbitration_prompt_template
                    )

                    if final_grade:
                        print(f"*** Final Validated Grade for Article {article_id}: {final_grade} ***")
                        # Successfully got a grade, update DB with TRUE status
                        update_article_grade_status(supabase, article_id, final_grade, "TRUE")
                    else:
                        # Grading process failed after abstract was extracted
                        print(f"*** Failed to obtain a validated grade for article {article_id}. Setting status to ERROR. ***")
                        update_article_grade_status(supabase, article_id, None, "ERROR")

                else:
                    # Could not extract abstract text from the HTML
                    logging.warning(f"Could not extract abstract text for article {article_id}. Skipping grading and setting status to ERROR.")
                    update_article_grade_status(supabase, article_id, None, "ERROR")

            else:
                # Could not fetch HTML
                logging.warning(f"Could not fetch HTML for article {article_id}. Skipping grading and setting status to ERROR.")
                update_article_grade_status(supabase, article_id, None, "ERROR")

            print("-" * (len(f"--- Processing Article ID: {article_id} (Link: {article_link}) ---"))) # Adjust separator length
            # Add a small delay between processing articles to be gentle on services
            time.sleep(0.5) # Adjust delay as needed

    except Exception as e:
        logging.exception(f"An critical error occurred during database query or processing loop")

    logging.info(f"Script finished processing batch run.")

# import os
# import requests
# import re
# import json
# import time # Import time for pausing
# from bs4 import BeautifulSoup
# from supabase import create_client, Client
# from dotenv import load_dotenv
# import logging
# import google.generativeai as genai
# # Import the specific exception for rate limiting if available
# from google.api_core import exceptions as google_exceptions
# from google.generativeai.types import HarmCategory, HarmBlockThreshold

# # --- Configuration ---
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# # Load environment variables from .env file
# load_dotenv()
# supabase_url = os.environ.get("SUPABASE_URL")
# supabase_key = os.environ.get("SUPABASE_KEY")
# google_api_key = os.environ.get("GOOGLE_API_KEY")

# BATCH_SIZE = 2
# TABLE_NAME = "articles"
# PROMPT_FILE = "prompt.txt"
# ARBITRATION_PROMPT_FILE = "arbitration_prompt.txt"
# GEMINI_MODEL = "gemini-2.0-flash"
# SAVE_DIR = "saved_grades"
# RETRY_DELAY_SECONDS = 15 # User-requested delay

# # --- Helper Functions ---

# def fetch_html(url: str) -> str | None:
#     """Fetches HTML content from a URL."""
#     if not url or not url.startswith(('http://', 'https://')):
#         logging.warning(f"Invalid URL provided: {url}")
#         return None
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#     }
#     try:
#         logging.info(f"Fetching HTML from: {url}")
#         response = requests.get(url, headers=headers, timeout=20)
#         response.raise_for_status()
#         content_type = response.headers.get('Content-Type', '').lower()
#         if 'text/html' not in content_type:
#             logging.warning(f"Content-Type is not HTML for {url} ({content_type}). Skipping parsing.")
#             return None
#         return response.text
#     except requests.exceptions.Timeout:
#         logging.error(f"Timeout error fetching URL {url}")
#         return None
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Error fetching URL {url}: {e}")
#         return None
#     except Exception as e:
#         logging.error(f"An unexpected error occurred during fetch for {url}: {e}")
#         return None

# def extract_pubmed_abstract_html(html_content: str) -> str | None:
#     """Extracts the abstract div HTML from PubMed page content."""
#     if not html_content:
#         return None
#     try:
#         soup = BeautifulSoup(html_content, 'html.parser')
#         abstract_div = soup.find('div', id='abstract', class_='abstract')
#         if abstract_div:
#             return abstract_div.prettify()
#         else:
#             logging.warning("Abstract div with id='abstract' and class_='abstract' not found.")
#             return None
#     except Exception as e:
#         logging.error(f"Error parsing HTML for abstract: {e}")
#         return None

# def get_abstract_text(html_content: str) -> str | None:
#     """Extracts plain text from the abstract HTML."""
#     if not html_content:
#         return None
#     try:
#         soup = BeautifulSoup(html_content, 'html.parser')
#         abstract_div = soup.find('div', id='abstract', class_='abstract')
#         if abstract_div:
#              content_div = abstract_div.find('div', class_='abstract-content')
#              if content_div:
#                  text_parts = [p.get_text(separator=' ', strip=True) for p in content_div.find_all(['p', 'div'], recursive=False)]
#                  return "\n".join(text_parts).strip()
#              else:
#                  return abstract_div.get_text(separator=' ', strip=True)
#         else:
#             return None
#     except Exception as e:
#         logging.error(f"Error extracting plain text from abstract HTML: {e}")
#         return None

# def load_prompt_template(filepath: str) -> str | None:
#     """Loads the prompt template from a file."""
#     try:
#         with open(filepath, 'r', encoding='utf-8') as f:
#             return f.read()
#     except FileNotFoundError:
#         logging.error(f"Prompt file not found: {filepath}")
#         return None
#     except Exception as e:
#         logging.error(f"Error reading prompt file {filepath}: {e}")
#         return None

# def get_gemini_grade_single(abstract_text: str, model: genai.GenerativeModel, formatted_prompt: str) -> str | None:
#     """
#     Gets a single grade from Gemini based on a pre-formatted prompt.
#     Includes logic to handle rate limits (429 errors) with a single retry after a delay.
#     """
#     if not abstract_text or not model or not formatted_prompt:
#         logging.warning("Missing abstract text, model, or formatted prompt for grading.")
#         return None

#     max_retries = 5 # Try original call + 1 retry
#     attempts = 0
#     safety_settings = {
#         HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
#         HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
#         HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
#         HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
#     }

#     while attempts <= max_retries:
#         attempts += 1
#         try:
#             logging.info(f"Sending request to Gemini (Attempt {attempts})...")
#             response = model.generate_content(formatted_prompt, safety_settings=safety_settings)

#             # --- Successful Response Processing ---
#             if not response.parts:
#                  if response.prompt_feedback.block_reason:
#                      logging.error(f"Gemini request blocked. Reason: {response.prompt_feedback.block_reason}")
#                  else:
#                      logging.error("Gemini response was empty or incomplete.")
#                  return None # Don't retry for blocks or empty responses

#             grade_text = response.text.strip()
#             logging.info(f"Raw Gemini response: '{grade_text}'")
#             match = re.search(r'\b(A|B|C|Accord d\'experts)\b', grade_text, re.IGNORECASE)

#             if match:
#                 grade = match.group(1)
#                 grade = 'Accord d\'experts' if grade.lower() == 'accord d\'experts' else grade.upper()
#                 if grade in ['A', 'B', 'C', 'Accord d\'experts']:
#                     logging.info(f"Extracted grade: {grade}")
#                     return grade # Success! Exit the loop.
#                 else:
#                     logging.warning(f"Extracted text '{grade}' is not a valid grade.")
#                     return None # Invalid grade extracted
#             else:
#                 logging.warning(f"Could not extract valid grade from Gemini response: '{grade_text}'")
#                 return None # Parsing failed

#         # --- Error Handling ---
#         except google_exceptions.ResourceExhausted as e:
#             logging.warning(f"Gemini API rate limit exceeded (429): {e}")
#             if attempts > max_retries:
#                 logging.error("Max retries reached after rate limit error. Failing grade.")
#                 return None
#             # Optional: Extract suggested delay from error message if needed
#             # suggested_delay_match = re.search(r'retry_delay {\s*seconds: (\d+)\s*}', str(e))
#             # delay = int(suggested_delay_match.group(1)) if suggested_delay_match else RETRY_DELAY_SECONDS
#             delay = RETRY_DELAY_SECONDS # Use user-requested delay
#             logging.info(f"Waiting for {delay} seconds before retrying...")
#             time.sleep(delay)
#             # Continue to the next iteration of the loop for retry

#         except Exception as e:
#             # Catch other potential API errors
#             logging.error(f"Error during Gemini API call: {e}", exc_info=True)
#             return None # Don't retry for other errors

#     # Should not be reached if logic is correct, but as a fallback
#     logging.error("Exited retry loop unexpectedly.")
#     return None


# def get_validated_grade(abstract_text: str, model: genai.GenerativeModel, base_prompt_template: str, arbitration_prompt_template: str) -> str | None:
#     """Performs double-check and arbitration to get a validated grade."""
#     if not all([abstract_text, model, base_prompt_template, arbitration_prompt_template]):
#         logging.error("Missing required inputs for validated grading.")
#         return None

#     # --- First Call ---
#     logging.info("Requesting first grade...")
#     prompt1 = base_prompt_template.format(abstract_text=abstract_text)
#     grade1 = get_gemini_grade_single(abstract_text, model, prompt1)
#     if grade1 is None:
#         logging.error("Failed to get first grade.")
#         return None
#     logging.info(f"First grade received: {grade1}")

#     # --- Second Call (with slight prompt variation) ---
#     logging.info("Requesting second grade...")
#     prompt_variation = base_prompt_template.replace(
#         "Abstract to Grade:\n---",
#         "Abstract for Second Review:\n>>>"
#     ).replace("---", "<<<")
#     prompt2 = prompt_variation.format(abstract_text=abstract_text)
#     # time.sleep(1) # Optional small delay between distinct calls
#     grade2 = get_gemini_grade_single(abstract_text, model, prompt2)
#     if grade2 is None:
#         logging.error("Failed to get second grade.")
#         return None
#     logging.info(f"Second grade received: {grade2}")

#     # --- Comparison ---
#     if grade1 == grade2:
#         logging.info(f"Grades match: {grade1}. Validation successful.")
#         return grade1
#     else:
#         logging.warning(f"Grades differ: Grade 1='{grade1}', Grade 2='{grade2}'. Proceeding to arbitration.")

#         # --- Third Call (Arbitration) ---
#         logging.info("Requesting arbitration grade...")
#         arbitration_prompt_formatted = arbitration_prompt_template.format(
#             abstract_text=abstract_text,
#             grade1=grade1,
#             grade2=grade2
#         )
#         # time.sleep(1) # Optional delay
#         final_grade = get_gemini_grade_single(abstract_text, model, arbitration_prompt_formatted)

#         if final_grade is None:
#             logging.error("Failed to get arbitration grade. Validation failed.")
#             return None

#         if final_grade not in [grade1, grade2]:
#              logging.warning(f"Arbitrated grade '{final_grade}' differs from both initial grades ('{grade1}', '{grade2}'). Using arbitrated grade.")
#         else:
#              logging.info(f"Arbitration successful. Final grade chosen: {final_grade}")

#         return final_grade

# def get_processed_ids(save_dir: str) -> set[int]:
#     """Scans the save directory and returns a set of article IDs that have already been processed."""
#     processed_ids = set()
#     if not os.path.isdir(save_dir):
#         logging.info(f"Save directory '{save_dir}' does not exist yet. No processed IDs found.")
#         return processed_ids
#     try:
#         for filename in os.listdir(save_dir):
#             if filename.endswith(".json"):
#                 try:
#                     article_id = int(filename.split('.')[0])
#                     processed_ids.add(article_id)
#                 except (ValueError, IndexError):
#                     logging.warning(f"Could not parse article ID from filename: {filename}")
#     except OSError as e:
#         logging.error(f"Error reading save directory '{save_dir}': {e}")
#         return set()
#     logging.info(f"Found {len(processed_ids)} previously processed article IDs in '{save_dir}'.")
#     return processed_ids

# def save_grade_to_file(article_id: int, article_link: str, grade: str, save_dir: str):
#     """Saves the validated grade and link to a JSON file."""
#     try:
#         os.makedirs(save_dir, exist_ok=True)
#         file_path = os.path.join(save_dir, f"{article_id}.json")
#         data_to_save = {
#             "article_id": article_id,
#             "article_link": article_link,
#             "validated_grade": grade
#             # "grading_method": "HAS_Anaes_2000_DoubleCheck"
#         }
#         with open(file_path, 'w', encoding='utf-8') as f:
#             json.dump(data_to_save, f, indent=4)
#         logging.info(f"Successfully saved grade and link for article {article_id} to {file_path}")
#     except OSError as e:
#         logging.error(f"Error creating directory {save_dir}: {e}")
#     except IOError as e:
#         logging.error(f"Error writing grade to file for article {article_id}: {e}")
#     except Exception as e:
#         logging.error(f"An unexpected error occurred during file saving for article {article_id}: {e}")

# # --- Main Execution ---
# if __name__ == "__main__":
#     if not supabase_url or not supabase_key:
#         logging.error("Error: Supabase URL or Key is missing. Set them in a .env file.")
#         exit(1)
#     if not google_api_key:
#         logging.error("Error: GOOGLE_API_KEY is missing. Set it in the .env file.")
#         exit(1)

#     # --- Initialize Clients and Load Prompts ---
#     supabase: Client | None = None
#     gemini_model: genai.GenerativeModel | None = None
#     base_prompt_template: str | None = None
#     arbitration_prompt_template: str | None = None

#     try:
#         logging.info("Initializing Supabase client...")
#         supabase = create_client(supabase_url, supabase_key)
#         logging.info("Supabase client initialized successfully.")

#         logging.info("Configuring Google AI...")
#         genai.configure(api_key=google_api_key)
#         gemini_model = genai.GenerativeModel(GEMINI_MODEL)
#         logging.info(f"Google AI configured with model: {GEMINI_MODEL}")

#         logging.info(f"Loading base prompt template from {PROMPT_FILE}...")
#         base_prompt_template = load_prompt_template(PROMPT_FILE)
#         if not base_prompt_template: exit(1)
#         logging.info("Base prompt template loaded successfully.")

#         logging.info(f"Loading arbitration prompt template from {ARBITRATION_PROMPT_FILE}...")
#         arbitration_prompt_template = load_prompt_template(ARBITRATION_PROMPT_FILE)
#         if not arbitration_prompt_template: exit(1)
#         logging.info("Arbitration prompt template loaded successfully.")

#     except Exception as e:
#         logging.error(f"Error during initialization: {e}")
#         exit(1)

#     # --- Get Processed IDs ---
#     processed_ids = get_processed_ids(SAVE_DIR)

#     # --- Fetch and Process Articles ---
#     logging.info(f"Attempting to fetch next batch of up to {BATCH_SIZE} UNPROCESSED articles...")
#     try:
#         if not all([supabase, gemini_model, base_prompt_template, arbitration_prompt_template]):
#              logging.error("Client or prompt templates not initialized properly. Cannot proceed.")
#              exit(1)

#         query = supabase.table(TABLE_NAME)\
#                         .select("id, link")\
#                         .neq("link", None)

#         if processed_ids:
#             logging.info(f"Excluding {len(processed_ids)} processed IDs from Supabase query.")
#             query = query.filter('id', 'not.in', f'({",".join(str(id) for id in processed_ids)})')

#         response = query.order("id", desc=False)\
#                         .limit(BATCH_SIZE)\
#                         .execute()

#         if response.data:
#             articles = response.data
#             logging.info(f"Successfully fetched {len(articles)} new articles to process.")
#         else:
#             articles = []
#             logging.info("No new unprocessed articles found matching the criteria or empty data returned.")

#         for article in articles:
#             article_id = article.get('id')
#             article_link = article.get('link')

#             if not article_link:
#                 logging.warning(f"Skipping article ID {article_id} due to missing link (unexpected).")
#                 continue

#             logging.info(f"--- Processing Article ID: {article_id} (Link: {article_link}) ---")

#             html_content = fetch_html(article_link)

#             if html_content:
#                 abstract_html_pretty = extract_pubmed_abstract_html(html_content)
#                 abstract_text = get_abstract_text(html_content)

#                 if abstract_text:
#                     logging.info("Abstract text extracted successfully. Starting validation process...")
#                     final_grade = get_validated_grade(
#                         abstract_text,
#                         gemini_model,
#                         base_prompt_template,
#                         arbitration_prompt_template
#                     )

#                     if final_grade:
#                         print(f"*** Final Validated Grade for Article {article_id}: {final_grade} ***")
#                         save_grade_to_file(article_id, article_link, final_grade, SAVE_DIR)
#                         # TODO: Update Supabase table if required (remains commented)
#                         # ...
#                     else:
#                         print(f"*** Failed to obtain a validated grade for article {article_id}. Will retry next run. ***")

#                 else:
#                     logging.warning(f"Could not extract abstract text for article {article_id}. Skipping grading.")
#             else:
#                 logging.warning(f"Could not fetch HTML for article {article_id}. Skipping grading.")

#             print("-" * (len(f"--- Processing Article ID: {article_id} (Link: {article_link}) ---") + 4))

#     except Exception as e:
#         logging.exception(f"An critical error occurred during database query or processing loop")

#     logging.info(f"Script finished processing batch run.")