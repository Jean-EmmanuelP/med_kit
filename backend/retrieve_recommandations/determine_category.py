import os
import json
import logging
import time
import re
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any, Set

from dotenv import load_dotenv
from supabase import create_client, Client
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup, Tag
from requests.exceptions import RequestException
from google.api_core.exceptions import GoogleAPIError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

GEMINI_MODEL_NAME = "gemini-2.0-flash"
PROMPT_FILE = "prompts.txt"
OUTPUT_DIR = "output_new"
RECOMMENDATIONS_OUTPUT_FILE = os.path.join(OUTPUT_DIR, "recommendation_links.json")

API_CALL_LIMIT = 1000
ARTICLE_BATCH_SIZE = 50
API_RETRY_DELAY = 20
API_MAX_RETRIES = 3
REQUESTS_TIMEOUT = 25

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

PUBMED_TITLE_SELECTOR = "h1.heading-title"
PUBMED_ABSTRACT_SELECTOR = "div.abstract-content"
PUBMED_AUTHORS_CONTAINER_SELECTOR = "div.authors-list"
PUBMED_AUTHOR_LINK_SELECTOR = "a.full-name"
PUBMED_JOURNAL_SELECTOR = "#full-view-journal-trigger"
PUBMED_TITLE_META = 'meta[name="citation_title"]'
PUBMED_ABSTRACT_META = 'meta[name="citation_abstract"]'
PUBMED_AUTHORS_META = 'meta[name="citation_author"]'
PUBMED_JOURNAL_META = 'meta[name="citation_journal_title"]'


def setup_supabase() -> Optional[Client]:
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

def load_existing_recommendations(filename: str) -> Set[str]:
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    if not os.path.exists(filename):
        logger.info(f"Recommendations file '{filename}' not found. A new one will be created.")
        return set()
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                logger.info(f"Recommendations file '{filename}' is empty. Starting with an empty set.")
                return set()
            
            data = json.loads(content)
            if isinstance(data, list):
                # Using a set to automatically handle duplicates
                existing_links = set(data)
                logger.info(f"Successfully loaded {len(existing_links)} existing unique recommendation links from '{filename}'.")
                return existing_links
            else:
                logger.warning(f"Content of '{filename}' is not a valid JSON list. Starting with an empty set to prevent corruption.")
                return set()
    except json.JSONDecodeError:
        logger.warning(f"Could not decode JSON from '{filename}'. File may be corrupt. Starting with an empty set.")
        return set()
    except Exception as e:
        logger.error(f"An unexpected error occurred loading recommendations from '{filename}': {e}. Starting with an empty set.")
        return set()

def scrape_pubmed_details(url: str) -> Optional[Dict[str, Any]]:
    if not url or not url.startswith("http"):
        logger.warning(f"Invalid URL provided for scraping: {url}")
        return None

    logger.info(f"Requesting PubMed URL: {url}")
    headers = {'User-Agent': USER_AGENT}
    details = {"title": None, "abstract": None, "authors": None, "journal": None}

    try:
        response = requests.get(url, headers=headers, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        title_meta_tag = soup.select_one(PUBMED_TITLE_META)
        if title_meta_tag and title_meta_tag.get('content'):
            details["title"] = title_meta_tag['content'].strip()
        else:
            title_h1_tag = soup.select_one(PUBMED_TITLE_SELECTOR)
            if title_h1_tag:
                details["title"] = title_h1_tag.get_text(strip=True)

        abstract_div = soup.select_one(PUBMED_ABSTRACT_SELECTOR)
        if abstract_div:
             details["abstract"] = abstract_div.get_text(separator='\n', strip=True)
             if details["abstract"]:
                 details["abstract"] = re.sub(r'\n{3,}', '\n\n', details["abstract"])
        elif not details["abstract"]:
            abstract_meta_tag = soup.select_one(PUBMED_ABSTRACT_META)
            if abstract_meta_tag and abstract_meta_tag.get('content'):
                details["abstract"] = abstract_meta_tag['content'].strip()

        author_meta_tags = soup.select(PUBMED_AUTHORS_META)
        if author_meta_tags:
            authors_list = [tag['content'].strip() for tag in author_meta_tags if tag.get('content')]
            if authors_list:
                details["authors"] = "; ".join(authors_list)
        if not details["authors"]:
            authors_container = soup.select_one(PUBMED_AUTHORS_CONTAINER_SELECTOR)
            if authors_container:
                 author_links = authors_container.select(PUBMED_AUTHOR_LINK_SELECTOR)
                 author_names = [link.get_text(strip=True) for link in author_links]
                 if author_names:
                     details["authors"] = "; ".join(author_names)

        journal_meta_tag = soup.select_one(PUBMED_JOURNAL_META)
        if journal_meta_tag and journal_meta_tag.get('content'):
            details["journal"] = journal_meta_tag['content'].strip()
        else:
            journal_button = soup.select_one(PUBMED_JOURNAL_SELECTOR)
            if journal_button:
                details["journal"] = journal_button.get_text(strip=True)

        logger.info(f"Scraped Title: {'Found' if details['title'] else 'Not Found'}")
        logger.info(f"Scraped Abstract: {'Found' if details.get('abstract') else 'Not Found'}")
        
        if not details["title"]:
            logger.error(f"CRITICAL: Title could not be scraped from {url}. Cannot proceed.")
            return None
        
        return details

    except RequestException as e:
        logger.error(f"HTTP request error scraping {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error scraping PubMed URL {url}: {e}", exc_info=False)
        return None

def call_gemini_classifier(model: genai.GenerativeModel, prompt_template: str, pubmed_data: Dict[str, Any]) -> Optional[int]:
    if not pubmed_data or not pubmed_data.get("title") or not pubmed_data.get("abstract"):
        logger.error("call_gemini_classifier called with missing title or abstract.")
        return None

    try:
        prompt = prompt_template.format(
            TITLE=pubmed_data.get("title", "N/A"),
            AUTHORS=pubmed_data.get("authors", "N/A"),
            JOURNAL=pubmed_data.get("journal", "N/A"),
            ABSTRACT=pubmed_data.get("abstract", "N/A")
        )
    except KeyError as e:
        logger.critical(f"KeyError during prompt formatting: {e}. Check prompts.txt for unexpected {{key}}.")
        return None

    retries = 0
    while retries < API_MAX_RETRIES:
        try:
            logger.info(f"Sending classification request to Gemini (Attempt {retries + 1}/{API_MAX_RETRIES})...")
            response = model.generate_content(prompt)
            
            if response.parts:
                try:
                    response_text = response.text
                    cleaned_response_text = re.sub(r'^```(json)?\s*|\s*```$', '', response_text).strip()

                    if not cleaned_response_text:
                        logger.warning("Gemini response text is empty after cleaning.")
                        retries += 1
                        time.sleep(API_RETRY_DELAY)
                        continue
                    
                    result = json.loads(cleaned_response_text)
                    if isinstance(result, dict) and 'category' in result and result['category'] in [1, 2]:
                        logger.info(f"Gemini classified article as: Category {result['category']}")
                        return result['category']
                    else:
                        logger.error(f"Gemini response JSON invalid: {result}")
                        return None
                except (json.JSONDecodeError, ValueError) as e:
                    logger.error(f"Failed to decode or access Gemini response: {e}. Response text: '{response.text}'")
                    return None
            else:
                 if response.prompt_feedback and response.prompt_feedback.block_reason:
                     logger.error(f"Gemini request blocked. Reason: {response.prompt_feedback.block_reason}")
                 else:
                     logger.error(f"Gemini returned no response parts. Response: {response}")
                 return None

        except (GoogleAPIError, Exception) as e:
            retries += 1
            logger.warning(f"Gemini API call failed (Attempt {retries}/{API_MAX_RETRIES}): {type(e).__name__} - {e}")

            if retries >= API_MAX_RETRIES:
                logger.error("Max retries reached for Gemini API call. Article will be skipped for this run.")
                return None
            
            if retries == API_MAX_RETRIES - 1:
                delay = 21
                logger.warning(f"This is the second failure. Waiting for a longer period ({delay} seconds) before the final attempt.")
            else:
                delay = API_RETRY_DELAY
                logger.info(f"Retrying Gemini call in {delay} seconds...")
            
            time.sleep(delay)

    return None

def get_articles_batch(supabase: Client, batch_size: int) -> List[Dict]:
    try:
        logger.info(f"Fetching next batch of articles from Supabase (check_recommandation = false)...")
        response = supabase.table('articles') \
            .select('id, link') \
            .eq('check_recommandation', False) \
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
                 logger.info("No more articles to process with check_recommandation = false.")
            return []
    except Exception as e:
        logger.error(f"Exception fetching articles batch from Supabase: {e}")
        return []

def update_article_status(supabase: Client, article_id: int):
    try:
        supabase.table('articles') \
            .update({'check_recommandation': True}) \
            .eq('id', article_id) \
            .execute()
        logger.info(f"Successfully marked article ID {article_id} as processed (check_recommandation = true).")
    except Exception as e:
        logger.error(f"Failed to update 'check_recommandation' for article ID {article_id}: {e}")

def main():
    logger.info("--- Starting Article Recommendation Classification Script ---")

    supabase = setup_supabase()
    gemini_model = setup_gemini()

    if not supabase or not gemini_model:
        logger.critical("Failed to initialize Supabase or Gemini. Exiting.")
        return

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

    recommendation_links_set = load_existing_recommendations(RECOMMENDATIONS_OUTPUT_FILE)
    
    api_call_counter = 0
    new_recommendations_count = 0
    total_processed_in_run = 0
    total_missing_abstract = 0
    total_errors = 0

    try:
        while api_call_counter < API_CALL_LIMIT:
            remaining_calls = API_CALL_LIMIT - api_call_counter
            current_batch_size = min(ARTICLE_BATCH_SIZE, remaining_calls)

            if current_batch_size <= 0:
                logger.info("API call limit reached. Stopping.")
                break

            articles_batch = get_articles_batch(supabase, current_batch_size)

            if not articles_batch:
                logger.info("No more articles to process.")
                break

            logger.info(f"--- Processing Batch of up to {len(articles_batch)} articles ---")

            for article in articles_batch:
                if api_call_counter >= API_CALL_LIMIT:
                    logger.info("API call limit reached mid-batch. Halting processing.")
                    break

                article_id = article.get('id')
                article_link = article.get('link')

                if not article_id or not article_link:
                    logger.warning(f"Skipping article entry due to missing ID or Link: {article}")
                    continue

                logger.info(f"--- Processing Article ID: {article_id} ---")
                total_processed_in_run += 1
                
                pubmed_data = scrape_pubmed_details(article_link)

                if pubmed_data is None:
                    logger.error(f"Failed to scrape essential data for article {article_id}. Marking as processed.")
                    total_errors += 1
                    update_article_status(supabase, article_id)
                    continue

                if not pubmed_data.get("abstract"):
                    logger.warning(f"Abstract missing for article {article_id}. Marking as processed.")
                    total_missing_abstract += 1
                    update_article_status(supabase, article_id)
                    continue
                
                api_call_counter += 1
                logger.info(f"API Call Count: {api_call_counter}/{API_CALL_LIMIT}")
                category = call_gemini_classifier(gemini_model, prompt_template, pubmed_data)
                
                if category is None:
                    logger.error(f"Failed to classify article {article_id} after all retries. The article's status will NOT be changed and it will be attempted again in a future run.")
                    total_errors += 1
                    continue
                
                if category == 1:
                    if article_link not in recommendation_links_set:
                        recommendation_links_set.add(article_link)
                        new_recommendations_count += 1
                        logger.info(f"Article ID {article_id} is a NEW Recommendation. Link captured.")
                    else:
                        logger.info(f"Article ID {article_id} is a Recommendation, but was already in the list.")
                
                update_article_status(supabase, article_id)
                time.sleep(0.75)
            
            if api_call_counter >= API_CALL_LIMIT:
                break

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down gracefully.")
    except Exception as e:
        logger.critical(f"An unexpected error occurred during the main processing loop: {e}", exc_info=True)
    finally:
        logger.info("--- Saving collected recommendation links ---")
        try:
            with open(RECOMMENDATIONS_OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # Convert the set to a list for JSON serialization
                sorted_links = sorted(list(recommendation_links_set))
                json.dump(sorted_links, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully saved a total of {len(sorted_links)} unique recommendation links to {RECOMMENDATIONS_OUTPUT_FILE}")
        except IOError as e:
            logger.error(f"Failed to write final recommendations file: {e}")

        logger.info("--- Classification Script Finished ---")
        logger.info(f"Total articles processed in this run: {total_processed_in_run}")
        logger.info(f"Total API calls made to Gemini: {api_call_counter}/{API_CALL_LIMIT}")
        logger.info(f"NEW recommendations found in this run: {new_recommendations_count}")
        logger.info(f"Articles skipped (missing Abstract): {total_missing_abstract}")
        logger.info(f"Articles with errors (classify): {total_errors}")
        logger.info("--- End of Script ---")

if __name__ == "__main__":
    main()