import os
import json
import logging
import argparse
import time
import re
from urllib.parse import urlparse
from datetime import datetime, timezone
from typing import List, Dict, Optional, Set, Any

# Third-party libraries
from dotenv import load_dotenv
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup, Tag
from requests.exceptions import RequestException
from readability import Document # For readability-lxml
from dateutil.parser import parse as dateutil_parse
from google.api_core.exceptions import GoogleAPIError

# --- Selenium Imports ---
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import WebDriverException, TimeoutException # Import TimeoutException

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
INPUT_FILENAME = os.path.join("output", "category_1_recommendations.json")
OUTPUT_DIR = os.path.join("output", "recommendation_summaries")
PROMPT_FILE = "recommendation_prompt.txt"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL_NAME = "gemini-1.5-flash"

REQUESTS_TIMEOUT = 25
SELENIUM_PAGE_LOAD_TIMEOUT = 45 # Timeout for Selenium page loads
API_RETRY_DELAY = 7
API_MAX_RETRIES = 3
MIN_CONTENT_LENGTH = 300
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# --- PubMed Selectors (for requests part) ---
PUBMED_TITLE_SELECTOR = "h1.heading-title"
PUBMED_JOURNAL_SELECTOR = "#full-view-journal-trigger"
PUBMED_DATE_SELECTOR = 'meta[name="citation_date"]'
PUBMED_FULL_TEXT_LIST_SELECTOR = "div.full-text-links-list"
PUBMED_FULL_TEXT_LINK_ITEM_SELECTOR = "a.link-item"

# --- Helper Functions ---

def setup_gemini() -> Optional[genai.GenerativeModel]:
    """Initializes and returns the Gemini client."""
    if not GOOGLE_API_KEY:
        logger.error("Google API Key not found in environment variables.")
        return None
    try:
        logger.info(f"Configuring Google AI with model: {GEMINI_MODEL_NAME}")
        genai.configure(api_key=GOOGLE_API_KEY)
        generation_config = genai.GenerationConfig(
            temperature=0.4,
            max_output_tokens=1500
        )
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        model = genai.GenerativeModel(
            GEMINI_MODEL_NAME,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        logger.info("Google AI Model initialized.")
        return model
    except Exception as e:
        logger.error(f"Failed to initialize Google AI Model: {e}")
        return None

def setup_selenium() -> Optional[webdriver.Chrome]:
    """Initializes and returns the Selenium WebDriver (NOT headless)."""
    try:
        logger.info("Setting up Selenium WebDriver (visible browser)...")
        options = ChromeOptions()
        # options.add_argument("--headless") # <-- REMOVED for visible browser
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu") # Still useful even if not headless
        options.add_argument(f"user-agent={USER_AGENT}")
        # Optional: Start maximized
        # options.add_argument("--start-maximized")

        # Use webdriver-manager
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(SELENIUM_PAGE_LOAD_TIMEOUT) # Set timeout for page loads
        logger.info("Selenium WebDriver initialized.")
        return driver
    except Exception as e:
        logger.error(f"Failed to initialize Selenium WebDriver: {e}")
        return None

def load_processed_ids_from_output_dir(output_dir: str) -> Set[int]:
    """Loads processed article IDs by checking for existing .json files in the output directory."""
    processed_ids: Set[int] = set()
    if not os.path.isdir(output_dir):
        logger.info(f"Output directory {output_dir} not found. Assuming no IDs processed.")
        return processed_ids
    for filename in os.listdir(output_dir):
        if filename.lower().endswith(".json"):
            try:
                article_id_str = os.path.splitext(filename)[0]
                article_id = int(article_id_str)
                processed_ids.add(article_id)
            except (ValueError, TypeError):
                logger.warning(f"Could not parse article ID from filename: {filename}")
    logger.info(f"Loaded {len(processed_ids)} processed article IDs from output directory: {output_dir}")
    return processed_ids

def save_summary(output_dir: str, article_id: int, summary: str):
    """Saves the summary text to a JSON file named after the article ID."""
    output_filepath = os.path.join(output_dir, f"{article_id}.json")
    output_data = {
        "id": article_id,
        "summary": summary
    }
    try:
        os.makedirs(output_dir, exist_ok=True)
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Successfully saved summary for ID {article_id} to {output_filepath}")
    except IOError as e:
        logger.error(f"Failed to write summary for ID {article_id} to {output_filepath}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error saving summary for ID {article_id}: {e}")

def fetch_html(url: str) -> Optional[str]:
    """Fetches HTML content from a URL using requests (used for PubMed)."""
    logger.debug(f"Fetching HTML from: {url} (using requests)")
    headers = {'User-Agent': USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.text
    except RequestException as e:
        logger.error(f"HTTP request error fetching {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return None

def format_publication_date(date_str: Optional[str]) -> str:
    """Attempts to parse date and format as DD/MM/YYYY. Returns 'Date inconnue' on failure."""
    if not date_str:
        return "Date inconnue"
    try:
        dt = dateutil_parse(date_str)
        return dt.strftime('%d/%m/%Y')
    except (ValueError, TypeError, OverflowError):
        logger.warning(f"Could not parse date '{date_str}' into DD/MM/YYYY format.")
        common_formats = ["%Y/%m/%d", "%Y-%m-%d", "%b %d, %Y", "%d %b %Y"]
        for fmt in common_formats:
             try:
                 dt = datetime.strptime(date_str, fmt)
                 return dt.strftime('%d/%m/%Y')
             except ValueError:
                 continue
        logger.error(f"Completely unable to parse date: '{date_str}'. Returning 'Date inconnue'.")
        return "Date inconnue"
    except Exception as e:
         logger.error(f"Unexpected error parsing date '{date_str}': {e}")
         return "Date inconnue"

def extract_pubmed_metadata_and_ft_link(pubmed_url: str) -> Optional[Dict[str, Any]]:
    """Fetches PubMed page (using requests), extracts metadata, and finds the first full-text link."""
    logger.info(f"Extracting metadata and full-text link from: {pubmed_url} (using requests)")
    html_content = fetch_html(pubmed_url)
    if not html_content:
        return None

    soup = BeautifulSoup(html_content, 'html.parser')
    metadata = {"title": None, "journal": None, "pub_date_raw": None, "full_text_url": None}

    try:
        # Metadata extraction remains the same (using BeautifulSoup)
        title_tag = soup.select_one(PUBMED_TITLE_SELECTOR)
        if title_tag: metadata["title"] = title_tag.get_text(strip=True)

        journal_tag = soup.select_one(PUBMED_JOURNAL_SELECTOR)
        if journal_tag: metadata["journal"] = journal_tag.get_text(strip=True)
        else:
            journal_meta = soup.select_one('meta[name="citation_journal_title"]')
            if journal_meta and journal_meta.get('content'): metadata["journal"] = journal_meta['content'].strip()

        date_meta = soup.select_one(PUBMED_DATE_SELECTOR)
        if date_meta and date_meta.get('content'): metadata["pub_date_raw"] = date_meta['content'].strip()

        # Extract First Full-Text Link
        links_list_div = soup.select_one(PUBMED_FULL_TEXT_LIST_SELECTOR)
        if links_list_div:
            first_link_tag = links_list_div.select_one(PUBMED_FULL_TEXT_LINK_ITEM_SELECTOR)
            if first_link_tag and first_link_tag.get('href'):
                metadata["full_text_url"] = first_link_tag['href']
                logger.info(f"  Identified full-text link: {metadata['full_text_url']}")
            else: logger.warning(f"  Found FT div, but no link item inside for {pubmed_url}")
        else: logger.warning(f"  Could not find FT links div for {pubmed_url}")

        # Validation
        if not metadata["title"] or not metadata["journal"] or not metadata["pub_date_raw"]:
             logger.warning(f"Missing essential metadata from {pubmed_url}")
        if not metadata["full_text_url"]:
             logger.error(f"Could not find any full-text link for {pubmed_url}. Cannot proceed with this article.")
             return None

        return metadata

    except Exception as e:
        logger.error(f"Error parsing metadata/FT link from {pubmed_url}: {e}", exc_info=False)
        return None


def extract_readable_content(driver: webdriver.Chrome, url: str) -> Optional[str]:
    """Fetches a URL using Selenium (visible browser) and uses readability to extract content."""
    logger.info(f"Attempting to extract readable content from: {url} (using Selenium)")
    html_content = None
    try:
        # Use Selenium to get the page source
        logger.debug(f"Navigating to {url} with Selenium...")
        driver.get(url)
        # Optional: Add a small explicit wait for a common element like body or a specific content div if needed
        # time.sleep(5) # Simple pause (adjust as needed)
        # WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body"))) # Wait for body tag

        html_content = driver.page_source
        logger.debug(f"Page source obtained (length: {len(html_content)})")

    except TimeoutException:
         logger.error(f"Selenium timed out loading page: {url}")
         return None
    except WebDriverException as e:
        logger.error(f"Selenium WebDriver error fetching {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected Selenium error fetching {url}: {e}")
        return None

    if not html_content:
        logger.error("Failed to get page source via Selenium.")
        return None

    try:
        # Process the source with readability
        doc = Document(html_content)
        readable_html = doc.summary()
        soup = BeautifulSoup(readable_html, 'html.parser')
        content_text = soup.get_text(separator='\n', strip=True)
        cleaned_text = re.sub(r'\n{3,}', '\n\n', content_text).strip()

        if len(cleaned_text) < MIN_CONTENT_LENGTH:
             logger.warning(f"Extracted content from {url} is too short ({len(cleaned_text)} chars). May be incomplete or paywalled.")
             # Decide whether to proceed or return None
             # return None # Option: Treat short content as failure

        logger.info(f"Successfully extracted readable content (length: {len(cleaned_text)} chars).")
        return cleaned_text

    except Exception as e:
        logger.error(f"Error using readability or parsing content from {url} (fetched via Selenium): {e}", exc_info=False)
        return None


def call_gemini_summarizer(model: genai.GenerativeModel, prompt_template: str, metadata: Dict[str, Any], article_text: str) -> Optional[str]:
    """Calls Gemini API to summarize the article text."""
    formatted_date = format_publication_date(metadata.get("pub_date_raw"))
    try:
        prompt = prompt_template.format(
            JOURNAL=metadata.get("journal", "Journal inconnu"),
            DATE_PUBLICATION=formatted_date,
            URL_ARTICLE_ORIGINAL=metadata.get("full_text_url", "URL inconnue"),
            TEXTE_ARTICLE=article_text
        )
    except KeyError as e:
        logger.critical(f"KeyError during prompt formatting: {e}. Check prompt file placeholders.")
        return None

    retries = 0
    while retries < API_MAX_RETRIES:
        try:
            logger.info("Sending summarization request to Gemini...")
            response = model.generate_content(prompt)

            if response.text:
                summary = response.text.strip()
                # Basic format check
                if f"Publié le {formatted_date}" not in summary or "Accéder à l'article original" not in summary:
                     logger.warning("Gemini response might not follow the requested format.")
                logger.info(f"Gemini generated summary (length: {len(summary)}).")
                return summary
            elif response.prompt_feedback and response.prompt_feedback.block_reason:
                 logger.error(f"Gemini request blocked. Reason: {response.prompt_feedback.block_reason}")
                 return None
            else:
                 finish_reason = getattr(response.candidates[0], 'finish_reason', 'UNKNOWN').name if response.candidates else 'UNKNOWN'
                 logger.warning(f"Gemini returned empty response (no text). Finish reason: {finish_reason}")
                 if finish_reason == "SAFETY": return None
                 retries += 1
                 logger.warning(f"Retrying ({retries}/{API_MAX_RETRIES})...")
                 time.sleep(API_RETRY_DELAY * (retries))
                 continue

        except (GoogleAPIError, Exception) as e:
            retries += 1
            error_type = type(e).__name__
            logger.warning(f"Gemini API call failed (Attempt {retries}/{API_MAX_RETRIES}): {error_type} - {e}")
            if retries >= API_MAX_RETRIES:
                logger.error("Max retries reached for Gemini API call.")
                return None
            logger.info(f"Retrying Gemini call in {API_RETRY_DELAY * (retries)} seconds...")
            time.sleep(API_RETRY_DELAY * (retries))

    return None

def load_input_articles(filepath: str) -> List[Dict]:
    """Loads article data (expecting 'id' and 'link') from the input JSON file."""
    if not os.path.exists(filepath):
        logger.error(f"Input file not found: {filepath}")
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content: return []
            data = json.loads(content)
        if not isinstance(data, list):
            logger.error(f"Input JSON file {filepath} does not contain a list.")
            return []
        valid_articles = [item for item in data if isinstance(item, dict) and item.get('id') is not None and item.get('link')]
        invalid_count = len(data) - len(valid_articles)
        if invalid_count > 0: logger.warning(f"Skipped {invalid_count} invalid entries from {filepath}.")
        logger.info(f"Found {len(valid_articles)} valid articles in {filepath}")
        return valid_articles
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding source JSON file {filepath}: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred loading {filepath}: {e}")
        return []

# --- Main Execution ---
def main(input_file: str, output_dir: str):
    """Main function to process recommendations and generate summaries."""
    logger.info("--- Starting Recommendation Summarization Script (Selenium for content) ---")
    logger.info(f"Input file: {input_file}")
    logger.info(f"Output directory: {output_dir}")

    # --- Setup ---
    gemini_model = setup_gemini()
    driver = setup_selenium() # Initialize Selenium driver

    if not gemini_model or not driver: # Check both
        logger.critical("Failed to initialize Gemini or Selenium. Exiting.")
        if driver: driver.quit() # Quit driver if it was initialized
        return

    # --- Load Prompt ---
    try:
        with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        logger.info(f"Successfully loaded prompt template from {PROMPT_FILE}")
    except FileNotFoundError:
        logger.critical(f"Prompt file '{PROMPT_FILE}' not found. Exiting.")
        driver.quit()
        return
    except Exception as e:
        logger.critical(f"Error reading prompt file '{PROMPT_FILE}': {e}. Exiting.")
        driver.quit()
        return

    # --- Create Output Dir & Load Processed IDs ---
    os.makedirs(output_dir, exist_ok=True)
    processed_ids = load_processed_ids_from_output_dir(output_dir)

    # --- Load Input Articles ---
    articles_to_process = load_input_articles(input_file)
    if not articles_to_process:
        logger.info("No valid articles found in the input file to process.")
        driver.quit()
        return

    # --- Processing Loop ---
    total_processed_in_run = 0
    total_summarized = 0
    total_skipped_metadata_fail = 0
    total_skipped_content_fail = 0
    total_skipped_gemini_fail = 0

    try:
        for article in articles_to_process:
            article_id = article.get('id')
            pubmed_link = article.get('link')

            try: article_id_int = int(article_id)
            except (ValueError, TypeError):
                 logger.warning(f"Invalid article ID '{article_id}'. Skipping.")
                 continue

            if article_id_int in processed_ids:
                continue

            logger.info(f"--- Processing Article ID: {article_id_int} ---")
            total_processed_in_run += 1

            # 1. Get Metadata & FT Link (using requests)
            metadata = extract_pubmed_metadata_and_ft_link(pubmed_link)
            if not metadata or not metadata.get("full_text_url"):
                logger.error(f"Failed to get metadata/FT link for Article ID {article_id_int} from {pubmed_link}. Skipping.")
                total_skipped_metadata_fail += 1
                time.sleep(0.5)
                continue

            # 2. Extract Content (using Selenium)
            article_text = extract_readable_content(driver, metadata["full_text_url"]) # Pass driver
            if not article_text:
                logger.error(f"Failed to extract content for Article ID {article_id_int} from {metadata['full_text_url']}. Skipping.")
                total_skipped_content_fail += 1
                # Consider adding ID to processed_ids here if content extraction fails consistently
                # processed_ids.add(article_id_int)
                time.sleep(0.5)
                continue

            # 3. Summarize with Gemini
            summary = call_gemini_summarizer(gemini_model, prompt_template, metadata, article_text)
            if not summary:
                logger.error(f"Failed to generate summary for Article ID {article_id_int}. Skipping.")
                total_skipped_gemini_fail += 1
                # processed_ids.add(article_id_int) # Consider adding ID here too
                time.sleep(0.5)
                continue

            # 4. Save the Summary
            save_summary(output_dir, article_id_int, summary)
            processed_ids.add(article_id_int)
            total_summarized += 1

            time.sleep(1.5) # Delay between successful API calls

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down gracefully.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred during the main processing loop: {e}", exc_info=True)
    finally:
        # --- Cleanup Selenium Driver ---
        if driver:
            logger.info("Closing Selenium WebDriver...")
            driver.quit()
            logger.info("WebDriver closed.")

        # --- Final Summary ---
        logger.info("--- Recommendation Summarization Finished ---")
        logger.info(f"Total articles attempted in this run: {total_processed_in_run}")
        logger.info(f"Successfully summarized and saved: {total_summarized}")
        logger.info(f"Skipped (Metadata/FT Link failure): {total_skipped_metadata_fail}")
        logger.info(f"Skipped (Content extraction failure): {total_skipped_content_fail}")
        logger.info(f"Skipped (Gemini summarization failure): {total_skipped_gemini_fail}")
        logger.info(f"Summaries saved in '{output_dir}' directory.")
        logger.info("--- End of Script ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate clinical summaries for medical recommendations listed in a JSON file.")
    parser.add_argument("--input-file", default=INPUT_FILENAME, help=f"Path to the input JSON file (default: {INPUT_FILENAME})")
    parser.add_argument("--output-dir", default=OUTPUT_DIR, help=f"Directory to save the output summary JSON files (default: {OUTPUT_DIR})")
    args = parser.parse_args()
    main(args.input_file, args.output_dir)