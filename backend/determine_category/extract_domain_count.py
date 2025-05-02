import os
import json
import logging
import argparse
import time
import re
from collections import Counter
from typing import List, Dict, Optional, Set, Any
from urllib.parse import urlparse

# Third-party libraries
import requests
from bs4 import BeautifulSoup, Tag
from requests.exceptions import RequestException

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Constants ---
OUTPUT_DIR = "output"
DOMAIN_COUNTS_FILENAME = os.path.join(OUTPUT_DIR, "full_text_domain_counts.json")
REQUESTS_TIMEOUT = 20 # seconds for HTTP requests
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# --- PubMed Selectors ---
# Selector for the container div holding the list of full-text links
FULL_TEXT_LIST_SELECTOR = "div.full-text-links-list"
# Selector for individual link items within that list
FULL_TEXT_LINK_ITEM_SELECTOR = "a.link-item"

# --- Helper Functions ---

def load_existing_counts(filename: str) -> Counter:
    """Loads existing domain counts from the JSON file."""
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    if isinstance(data, dict):
                         # Convert loaded dict to Counter
                        logger.info(f"Loaded {len(data)} existing domain counts from {filename}.")
                        return Counter(data)
                    else:
                         logger.warning(f"File {filename} does not contain a valid JSON dictionary. Starting fresh.")
                else:
                    logger.info(f"File {filename} is empty. Starting fresh.")
        except json.JSONDecodeError:
            logger.warning(f"Could not decode JSON from {filename}. Starting fresh.")
        except Exception as e:
            logger.error(f"Error loading counts from {filename}: {e}. Starting fresh.")
    else:
        logger.info(f"Output file {filename} not found. Starting fresh.")
    return Counter()

def save_counts(filename: str, counts: Counter):
    """Saves the domain counts to the JSON file, sorted by count."""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        # Sort by count descending for readability
        sorted_counts = dict(counts.most_common())
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(sorted_counts, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved {len(counts)} domain counts to {filename}.")
    except IOError as e:
        logger.error(f"Failed to write counts to {filename}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error saving counts to {filename}: {e}")

def get_domain(url: str) -> Optional[str]:
    """Extracts the domain (netloc) from a URL."""
    if not url:
        return None
    try:
        parsed_uri = urlparse(url)
        # netloc contains the domain name, lowercased for consistency
        domain = parsed_uri.netloc.lower()
        # Remove www. prefix if present for better grouping
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain if domain else None
    except Exception as e:
        logger.warning(f"Could not parse domain from URL '{url}': {e}")
        return None

def extract_full_text_links(pubmed_url: str) -> List[str]:
    """Fetches PubMed page and extracts URLs from the 'Full text links' section."""
    if not pubmed_url or not pubmed_url.startswith("http"):
        logger.warning(f"Invalid PubMed URL provided: {pubmed_url}")
        return []

    logger.debug(f"Requesting PubMed page: {pubmed_url}")
    headers = {'User-Agent': USER_AGENT}
    extracted_links = []

    try:
        response = requests.get(pubmed_url, headers=headers, timeout=REQUESTS_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the container for the full-text links
        links_list_div = soup.select_one(FULL_TEXT_LIST_SELECTOR)
        if not links_list_div:
            logger.debug(f"No 'full-text-links-list' div found on {pubmed_url}")
            return []

        # Find all link items within the container
        link_tags = links_list_div.select(FULL_TEXT_LINK_ITEM_SELECTOR)
        if not link_tags:
            logger.debug(f"No 'a.link-item' tags found within the list div on {pubmed_url}")
            return []

        for tag in link_tags:
            href = tag.get('href')
            if href:
                extracted_links.append(href)
                logger.debug(f"  Found link: {href}")

        logger.info(f"Found {len(extracted_links)} full-text link(s) on {pubmed_url}")
        return extracted_links

    except RequestException as e:
        logger.error(f"HTTP request error for {pubmed_url}: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing page {pubmed_url}: {e}", exc_info=False)
        return []

def load_articles_from_json(filepath: str) -> List[Dict]:
    """Loads article data (expecting at least 'id' and 'link') from a JSON file."""
    articles = []
    if not os.path.exists(filepath):
        logger.warning(f"Input file not found: {filepath}. Skipping.")
        return []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                logger.info(f"Input file is empty: {filepath}. Skipping.")
                return []
            data = json.loads(content)
        if not isinstance(data, list):
            logger.error(f"Input JSON file {filepath} does not contain a list.")
            return []

        # Validate entries slightly
        for i, item in enumerate(data):
             if isinstance(item, dict) and item.get('id') is not None and item.get('link'):
                 articles.append(item)
             else:
                 logger.warning(f"Skipping invalid entry #{i+1} in {filepath}: {item}")

        logger.info(f"Successfully loaded {len(articles)} valid articles from {filepath}")
        return articles
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding source JSON file {filepath}: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred loading {filepath}: {e}")
        return []

# --- Main Execution ---
def main(input_files: List[str], output_file: str):
    """Main function to extract and count full-text link domains."""
    logger.info("--- Starting Full-Text Link Domain Extractor ---")
    logger.info(f"Input files: {', '.join(input_files)}")
    logger.info(f"Output file: {output_file}")

    domain_counts = load_existing_counts(output_file)
    processed_article_ids_in_run: Set[int] = set() # Track IDs processed in this specific run
    total_articles_processed = 0
    total_links_found = 0
    total_errors = 0

    for input_filepath in input_files:
        logger.info(f"--- Processing input file: {input_filepath} ---")
        articles = load_articles_from_json(input_filepath)

        if not articles:
            continue

        for article in articles:
            article_id = article.get('id')
            pubmed_link = article.get('link')

            # Ensure ID is valid and not already processed in this run
            try:
                article_id_int = int(article_id) # Convert to int for set comparison
            except (ValueError, TypeError):
                 logger.warning(f"Invalid article ID '{article_id}' found in {input_filepath}. Skipping.")
                 continue

            if article_id_int in processed_article_ids_in_run:
                logger.debug(f"Article ID {article_id_int} already processed in this run. Skipping.")
                continue

            if not pubmed_link:
                logger.warning(f"Article ID {article_id_int} missing 'link'. Skipping.")
                processed_article_ids_in_run.add(article_id_int) # Mark as processed even if skipped
                continue

            logger.info(f"Processing Article ID: {article_id_int} (Link: {pubmed_link})")
            total_articles_processed += 1
            processed_article_ids_in_run.add(article_id_int) # Mark as processed for this run

            # Extract links
            full_text_urls = extract_full_text_links(pubmed_link)

            if not full_text_urls:
                # If no links found, it's not necessarily an error, just note it.
                logger.info(f"No full-text links found for Article ID {article_id_int}.")
            else:
                total_links_found += len(full_text_urls)
                for ft_url in full_text_urls:
                    domain = get_domain(ft_url)
                    if domain:
                        domain_counts[domain] += 1
                        logger.debug(f"  Counted domain: {domain}")
                    else:
                        logger.warning(f"  Could not extract domain from: {ft_url}")

            # Add a small delay to avoid overwhelming PubMed
            time.sleep(0.3) # Shorter delay might be acceptable here

        logger.info(f"--- Finished processing file: {input_filepath} ---")

    # Save the final counts
    save_counts(output_file, domain_counts)

    # --- Final Summary ---
    logger.info("--- Domain Extraction Finished ---")
    logger.info(f"Total unique articles processed in this run: {total_articles_processed}")
    logger.info(f"Total full-text links found across articles: {total_links_found}")
    logger.info(f"Total unique domains found: {len(domain_counts)}")
    logger.info(f"Domain counts saved to: {output_file}")
    if domain_counts:
        logger.info("Top 5 domains:")
        for domain, count in domain_counts.most_common(5):
            logger.info(f"  {domain}: {count}")
    logger.info("--- End of Script ---")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract and count domains from 'Full text links' on PubMed pages listed in input JSON files.")
    parser.add_argument(
        "input_files",
        nargs='+', # Accepts one or more input files
        help="Path(s) to the input JSON file(s) containing article data (must have 'id' and 'link'). You can use wildcards like 'output/*.json'."
    )
    parser.add_argument(
        "--output-file",
        default=DOMAIN_COUNTS_FILENAME,
        help=f"Path to the output JSON file to store domain counts (default: {DOMAIN_COUNTS_FILENAME})"
    )
    args = parser.parse_args()

    main(args.input_files, args.output_file)