import os
import json
import logging
import argparse
import time
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set, Any

# Third-party libraries
from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup, Tag # Added Tag for type hinting
from requests.exceptions import RequestException

from google.api_core.exceptions import GoogleAPIError

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Constants ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = "gemini-2.0-flash"
PROMPT_FILE = "prompts.txt"
OUTPUT_DIR = "output"
CAT1_FILENAME = os.path.join(OUTPUT_DIR, "category_1_recommendations.json")
CAT2_FILENAME = os.path.join(OUTPUT_DIR, "category_2_classic_articles.json")
MISSING_ABSTRACT_FILENAME = os.path.join(OUTPUT_DIR, "missing_abstract_articles.json") # <-- New File
PROCESSED_ID_FILES = [CAT1_FILENAME, CAT2_FILENAME, MISSING_ABSTRACT_FILENAME] # <-- Updated List

ARTICLE_BATCH_SIZE = 50
API_RETRY_DELAY = 5
API_MAX_RETRIES = 3
REQUESTS_TIMEOUT = 25 # Slightly increased timeout

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# --- PubMed Selectors ---
PUBMED_TITLE_SELECTOR = "h1.heading-title"
PUBMED_ABSTRACT_SELECTOR = "div.abstract-content"
# Use more specific author link selector within the list for fallback
PUBMED_AUTHORS_CONTAINER_SELECTOR = "div.authors-list"
PUBMED_AUTHOR_LINK_SELECTOR = "a.full-name"
PUBMED_JOURNAL_SELECTOR = "#full-view-journal-trigger" # Button ID
PUBMED_TITLE_META = 'meta[name="citation_title"]'
PUBMED_ABSTRACT_META = 'meta[name="citation_abstract"]'
PUBMED_AUTHORS_META = 'meta[name="citation_author"]'
PUBMED_JOURNAL_META = 'meta[name="citation_journal_title"]'

# --- Helper Functions ---

def setup_supabase() -> Optional[Client]:
    """Initializes and returns the Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("Supabase URL or Key not found in environment variables.")
        return None
    try:
        logger.info("Connecting to Supabase...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        supabase.table('articles').select('id').limit(1).execute()
        logger.info("Supabase connection successful.")
        return supabase
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return None

def setup_gemini() -> Optional[genai.GenerativeModel]:
    """Initializes and returns the Gemini client."""
    if not GOOGLE_API_KEY:
        logger.error("Google API Key not found in environment variables.")
        return None
    try:
        logger.info(f"Configuring Google AI with model: {GEMINI_MODEL_NAME}")
        genai.configure(api_key=GOOGLE_API_KEY)
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2,
            max_output_tokens=100
        )
        # Increased safety settings slightly for classification task
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        model = genai.GenerativeModel(
            GEMINI_MODEL_NAME,
            generation_config=generation_config,
            safety_settings=safety_settings # Add safety settings
        )
        logger.info("Google AI Model initialized.")
        return model
    except Exception as e:
        logger.error(f"Failed to initialize Google AI Model: {e}")
        return None


def load_processed_ids(filenames: List[str]) -> Set[int]:
    """Loads processed article IDs from the given JSON output files."""
    processed_ids: Set[int] = set()
    for filename in filenames:
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    # Handle potentially empty file
                    content = f.read().strip()
                    if not content:
                        logger.info(f"File {filename} is empty. Skipping.")
                        continue
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            # Check item type and key existence carefully
                            if isinstance(item, dict) and item.get('id') is not None:
                                try:
                                    processed_ids.add(int(item['id'])) # Ensure ID is integer
                                except (ValueError, TypeError):
                                     logger.warning(f"Found non-integer ID '{item['id']}' in {filename}. Skipping item.")
                            else:
                                logger.warning(f"Found invalid item format in {filename}: {item}. Skipping.")
                    else:
                        logger.warning(f"File {filename} does not contain a valid JSON list. Ignoring content.")
        except json.JSONDecodeError:
            logger.warning(f"Could not decode JSON from {filename}. Assuming empty or corrupted.")
        except Exception as e:
            logger.error(f"Error loading processed IDs from {filename}: {e}")
    logger.info(f"Loaded {len(processed_ids)} processed article IDs from {len(filenames)} file(s).")
    return processed_ids


def save_result(filename: str, data: Dict[str, Any]):
    """Appends a result dictionary to the specified JSON file."""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        results_list = []
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        results_list = json.loads(content)
                        if not isinstance(results_list, list):
                            logger.warning(f"Content of {filename} is not a list. Overwriting with new list.")
                            results_list = []
            except json.JSONDecodeError:
                logger.warning(f"Could not decode JSON from {filename}. Starting a new list.")
                results_list = []
            except Exception as read_err:
                 logger.error(f"Error reading {filename} before append: {read_err}. Starting new list.")
                 results_list = []

        results_list.append(data)

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results_list, f, indent=2, ensure_ascii=False)

    except IOError as e:
        logger.error(f"Failed to write result to {filename}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error saving result to {filename}: {e}")


def scrape_pubmed_details(url: str) -> Optional[Dict[str, Any]]:
    """Scrapes Title, Abstract, Authors, Journal from a PubMed URL using requests and BeautifulSoup."""
    if not url or not url.startswith("http"):
        logger.warning(f"Invalid URL provided for scraping: {url}")
        return None

    logger.info(f"Requesting PubMed URL: {url}")
    headers = {'User-Agent': USER_AGENT}
    details = {"title": None, "abstract": None, "authors": None, "journal": None}
    soup = None # Initialize soup to None

    try:
        response = requests.get(url, headers=headers, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # --- Extract Information ---

        # Title (Meta preferred)
        title_meta_tag = soup.select_one(PUBMED_TITLE_META)
        if title_meta_tag and title_meta_tag.get('content'):
            details["title"] = title_meta_tag['content'].strip()
        else:
            title_h1_tag = soup.select_one(PUBMED_TITLE_SELECTOR)
            if title_h1_tag:
                details["title"] = title_h1_tag.get_text(strip=True)

        # Abstract (Div preferred)
        abstract_div = soup.select_one(PUBMED_ABSTRACT_SELECTOR)
        if abstract_div:
             # Use get_text with a separator to preserve paragraph breaks better
             details["abstract"] = abstract_div.get_text(separator='\n', strip=True)
             # Basic clean up for potential multiple newlines
             if details["abstract"]:
                 details["abstract"] = re.sub(r'\n{3,}', '\n\n', details["abstract"])
        # Fallback to meta tag is less likely but possible
        elif not details["abstract"]:
            abstract_meta_tag = soup.select_one(PUBMED_ABSTRACT_META)
            if abstract_meta_tag and abstract_meta_tag.get('content'):
                details["abstract"] = abstract_meta_tag['content'].strip()

        # Authors (Meta tags preferred)
        author_meta_tags = soup.select(PUBMED_AUTHORS_META)
        if author_meta_tags:
            authors_list = [tag['content'].strip() for tag in author_meta_tags if tag.get('content')]
            if authors_list:
                details["authors"] = "; ".join(authors_list)
        # Fallback to scraping author links from the div
        if not details["authors"]:
            authors_container = soup.select_one(PUBMED_AUTHORS_CONTAINER_SELECTOR)
            if authors_container:
                 author_links = authors_container.select(PUBMED_AUTHOR_LINK_SELECTOR)
                 author_names = [link.get_text(strip=True) for link in author_links]
                 if author_names:
                     details["authors"] = "; ".join(author_names)

        # Journal (Meta preferred)
        journal_meta_tag = soup.select_one(PUBMED_JOURNAL_META)
        if journal_meta_tag and journal_meta_tag.get('content'):
            details["journal"] = journal_meta_tag['content'].strip()
        else:
            journal_button = soup.select_one(PUBMED_JOURNAL_SELECTOR)
            if journal_button:
                details["journal"] = journal_button.get_text(strip=True)

        # --- Logging ---
        logger.info(f"Scraped Title: {'Found' if details['title'] else 'Not Found'}")
        # Only log abstract found/not found, not the content unless debugging
        logger.info(f"Scraped Abstract: {'Found' if details.get('abstract') else 'Not Found'}")
        logger.info(f"Scraped Authors: {'Found' if details['authors'] else 'Not Found'}")
        logger.info(f"Scraped Journal: {'Found' if details['journal'] else 'Not Found'}")

        # *** Crucial Check: Title is absolutely required. Abstract is required for classification ***
        if not details["title"]:
            logger.error(f"CRITICAL: Title could not be scraped from {url}. Cannot proceed.")
            return None # Return None if title is missing

        # Note: We now return the details even if abstract is missing,
        # the main loop will handle routing to the missing abstract file.

        return details

    except RequestException as e:
        logger.error(f"HTTP request error scraping {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error scraping PubMed URL {url}: {e}", exc_info=False) # Set exc_info=False for cleaner logs unless debugging
        # Log soup content only if it exists and failed during parsing
        # if soup:
        #      logger.debug(f"Error occurred during parsing. Soup content sample: {str(soup)[:500]}")
        return None


def call_gemini_classifier(model: genai.GenerativeModel, prompt_template: str, pubmed_data: Dict[str, Any]) -> Optional[int]:
    """Calls Gemini API to classify the article based on scraped data."""
    # This check now assumes the main loop verified the abstract exists before calling
    if not pubmed_data or not pubmed_data.get("title") or not pubmed_data.get("abstract"):
        logger.error("call_gemini_classifier called with missing title or abstract.")
        return None

    # Fix the original KeyError by ensuring prompt_template doesn't contain unexpected format keys
    try:
        prompt = prompt_template.format(
            TITLE=pubmed_data.get("title", "N/A"),
            AUTHORS=pubmed_data.get("authors", "N/A"),
            JOURNAL=pubmed_data.get("journal", "N/A"),
            ABSTRACT=pubmed_data.get("abstract", "N/A")
        )
    except KeyError as e:
        logger.critical(f"KeyError during prompt formatting: {e}. This likely means your prompts.txt file contains an unexpected {{key}}. Please check prompts.txt.")
        # Log the template for easier debugging
        logger.debug(f"Prompt Template causing error:\n---\n{prompt_template}\n---")
        return None # Cannot proceed if prompt is broken

    retries = 0
    while retries < API_MAX_RETRIES:
        try:
            logger.info("Sending classification request to Gemini...")
            response = model.generate_content(prompt) # Removed stream=True

            # Check for content and safety ratings / finish reasons
            if response.parts:
                try:
                    # Access text directly if available
                    response_text = response.text
                    cleaned_response_text = re.sub(r'^```(json)?\s*|\s*```$', '', response_text).strip()

                    if not cleaned_response_text:
                        logger.warning("Gemini response text is empty after cleaning.")
                        # Check block/finish reasons more thoroughly
                        if response.prompt_feedback and response.prompt_feedback.block_reason:
                             logger.error(f"Gemini request blocked. Reason: {response.prompt_feedback.block_reason}")
                             return None # Blocked is failure
                        finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN').name if response.candidates else 'UNKNOWN'
                        if finish_reason not in ["STOP", "MAX_TOKENS"]:
                             logger.warning(f"Gemini response empty, finished unexpectedly: {finish_reason}")
                             # Decide if retry is appropriate based on finish_reason
                             if finish_reason == "SAFETY": return None # Safety block

                        retries += 1
                        logger.warning(f"Gemini returned empty valid response. Retrying ({retries}/{API_MAX_RETRIES})...")
                        time.sleep(API_RETRY_DELAY)
                        continue # Retry if empty but not blocked/error

                    # Attempt to parse JSON
                    try:
                        result = json.loads(cleaned_response_text)
                        if isinstance(result, dict) and 'category' in result and result['category'] in [1, 2]:
                            logger.info(f"Gemini classified article as: Category {result['category']}")
                            return result['category']
                        else:
                            logger.error(f"Gemini response JSON invalid: Missing 'category' or bad value: {result}")
                            return None
                    except json.JSONDecodeError:
                        logger.error(f"Failed to decode Gemini JSON response: {cleaned_response_text}")
                        return None

                except ValueError:
                    # Handle case where response.text might raise ValueError (e.g., if blocked)
                    logger.warning("Could not access response.text, potentially blocked or malformed.")
                    if response.prompt_feedback and response.prompt_feedback.block_reason:
                        logger.error(f"Gemini request blocked. Reason: {response.prompt_feedback.block_reason}")
                    else:
                        logger.error(f"Gemini response structure unexpected or empty. Response: {response}")
                    return None
            else:
                 # No parts in response, likely blocked or error
                 if response.prompt_feedback and response.prompt_feedback.block_reason:
                     logger.error(f"Gemini request blocked (no parts). Reason: {response.prompt_feedback.block_reason}")
                 else:
                     logger.error(f"Gemini returned no response parts. Response: {response}")
                 return None


        except (GoogleAPIError, Exception) as e:
            retries += 1
            error_type = type(e).__name__
            logger.warning(f"Gemini API call failed (Attempt {retries}/{API_MAX_RETRIES}): {error_type} - {e}")
            if retries >= API_MAX_RETRIES:
                logger.error("Max retries reached for Gemini API call.")
                return None
            logger.info(f"Retrying Gemini call in {API_RETRY_DELAY} seconds...")
            time.sleep(API_RETRY_DELAY)

    return None


def get_articles_batch(supabase: Client, last_processed_id: int, batch_size: int) -> List[Dict]:
    """Fetches a batch of articles from Supabase articles table."""
    try:
        logger.info(f"Fetching next batch of articles from Supabase (ID > {last_processed_id})...")
        response = supabase.table('articles') \
            .select('id, link, grade') \
            .gt('id', last_processed_id) \
            .order('id', desc=False) \
            .limit(batch_size) \
            .execute()

        if response.data:
            logger.info(f"Fetched {len(response.data)} articles.")
            return response.data
        else:
            if hasattr(response, 'error') and response.error:
                 logger.error(f"Supabase error fetching articles: {response.error}")
            else:
                 logger.info("No more articles found in Supabase.")
            return []
    except Exception as e:
        logger.error(f"Exception fetching articles batch from Supabase: {e}")
        return []

# --- Main Execution ---
def main(batch_size: int):
    """Main function to run the classification process."""
    logger.info("--- Starting Article Classification Script (requests version) ---")

    # --- Setup ---
    supabase = setup_supabase()
    gemini_model = setup_gemini()

    if not supabase or not gemini_model:
        logger.critical("Failed to initialize Supabase or Gemini. Exiting.")
        return

    # --- Load Prompt ---
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        logger.info(f"Successfully loaded prompt template from {PROMPT_FILE}")
    except FileNotFoundError:
        logger.critical(f"Prompt file '{PROMPT_FILE}' not found. Exiting.")
        return
    except Exception as e:
        logger.critical(f"Error reading prompt file '{PROMPT_FILE}': {e}. Exiting.")
        return

    # --- Load Processed IDs ---
    processed_ids = load_processed_ids(PROCESSED_ID_FILES)
    last_processed_id = max(processed_ids) if processed_ids else 0
    logger.info(f"Starting processing for articles with ID > {last_processed_id}")

    # --- Processing Loop ---
    total_processed_in_run = 0
    total_classified_cat1 = 0
    total_classified_cat2 = 0
    total_skipped_missing_data = 0 # Renamed for clarity
    total_missing_abstract = 0     # <-- New counter
    total_errors = 0

    try:
        while True:
            articles_batch = get_articles_batch(supabase, last_processed_id, batch_size)

            if not articles_batch:
                logger.info("No more articles to process.")
                break

            logger.info(f"--- Processing Batch of {len(articles_batch)} articles ---")

            for article in articles_batch:
                article_id = article.get('id')
                article_link = article.get('link')
                original_grade = article.get('grade')

                if article_id:
                     last_processed_id = max(last_processed_id, article_id)

                if not article_id or not article_link:
                    logger.warning(f"Skipping article entry due to missing ID or Link: {article}")
                    total_skipped_missing_data += 1
                    continue

                if article_id in processed_ids:
                    continue # Already processed (in any category or missing abstract)

                logger.info(f"--- Processing Article ID: {article_id} ---")
                total_processed_in_run += 1

                # --- Scrape PubMed ---
                pubmed_data = scrape_pubmed_details(article_link)

                if pubmed_data is None:
                    # This now means title was missing or fatal scrape error occurred
                    logger.error(f"Failed to scrape essential PubMed data for article {article_id} (Link: {article_link}). Skipping.")
                    total_errors += 1
                    processed_ids.add(article_id) # Mark as processed to avoid retrying fatal error
                    # Optionally save to a separate error file if needed
                    continue

                # --- Check for Abstract ---
                if not pubmed_data.get("abstract"):
                    logger.warning(f"Abstract missing for article {article_id}. Saving to missing abstract file.")
                    total_missing_abstract += 1
                    missing_data = {
                        "id": article_id,
                        "link": article_link,
                        "reason": "Abstract missing during scrape",
                        "title": pubmed_data.get("title", "Title missing too"), # Include title if available
                        "processed_at": datetime.now(timezone.utc).isoformat()
                    }
                    save_result(MISSING_ABSTRACT_FILENAME, missing_data)
                    processed_ids.add(article_id) # Mark as processed
                    continue # Skip classification

                # --- Classify with Gemini (only if abstract exists) ---
                category = call_gemini_classifier(gemini_model, prompt_template, pubmed_data)
                if category is None:
                    logger.error(f"Failed to classify article {article_id} using Gemini. Skipping.")
                    total_errors += 1
                    processed_ids.add(article_id)
                    continue

                # --- Save Result ---
                result_data = {
                    "id": article_id,
                    "link": article_link,
                    "classified_category": category,
                    "original_grade": original_grade,
                    "processed_at": datetime.now(timezone.utc).isoformat()
                }

                if category == 1:
                    save_result(CAT1_FILENAME, result_data)
                    total_classified_cat1 += 1
                    logger.info(f"Saved Article ID {article_id} to {CAT1_FILENAME}")
                elif category == 2:
                    save_result(CAT2_FILENAME, result_data)
                    total_classified_cat2 += 1
                    logger.info(f"Saved Article ID {article_id} to {CAT2_FILENAME}")

                processed_ids.add(article_id)

                time.sleep(0.75) # Slightly increased delay back

            logger.info(f"--- Finished Batch ---")

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down gracefully.")
    except Exception as e:
        # Catch the specific error from the traceback
        if isinstance(e, KeyError) and str(e) == "'\"category\"'":
             logger.critical(f"Caught KeyError: {e}. This strongly indicates an issue with your prompts.txt file structure. Please review it and remove any literal '{{'\"category\"': ...}}' examples from the main template body.", exc_info=True)
        else:
             logger.critical(f"An unexpected error occurred during the main processing loop: {e}", exc_info=True)
    finally:
        # --- Final Summary ---
        logger.info("--- Classification Script Finished ---")
        logger.info(f"Total articles processed in this run: {total_processed_in_run}")
        logger.info(f"Classified as Category 1 (Recommendations): {total_classified_cat1}")
        logger.info(f"Classified as Category 2 (Classic Articles): {total_classified_cat2}")
        logger.info(f"Articles skipped (missing DB ID/Link): {total_skipped_missing_data}")
        logger.info(f"Articles skipped (missing Abstract): {total_missing_abstract}") # <-- New Log
        logger.info(f"Articles with errors (scrape/classify): {total_errors}")
        logger.info(f"Results saved in '{OUTPUT_DIR}' directory.")
        logger.info(f"Highest Article ID processed in Supabase: {last_processed_id}")
        logger.info("--- End of Script ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classify articles from Supabase using PubMed data (via requests) and Gemini.")
    parser.add_argument(
        "--batch-size",
        type=int,
        default=ARTICLE_BATCH_SIZE,
        help=f"Number of articles to fetch from Supabase per batch (default: {ARTICLE_BATCH_SIZE})"
    )
    args = parser.parse_args()

    main(args.batch_size)