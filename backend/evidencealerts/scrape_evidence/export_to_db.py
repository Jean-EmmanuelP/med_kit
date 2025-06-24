import os
import json
import argparse
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import re # Import regex for more robust splitting

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("Error: SUPABASE_URL and SUPABASE_KEY must be set in the .env file.")
    exit(1)

# --- Cache for Disciplines ---
# { "discipline_name": discipline_id }
discipline_cache = {}
cache_loaded = False

# --- Database Interaction ---

def load_disciplines_cache(supabase: Client):
    """Fetches all disciplines and populates the local cache."""
    global discipline_cache, cache_loaded
    if cache_loaded:
        return True
    try:
        logging.info("Loading disciplines from database...")
        response = supabase.table('disciplines').select('id, name').execute()
        if response.data:
            for discipline in response.data:
                discipline_cache[discipline['name']] = discipline['id']
            cache_loaded = True
            logging.info(f"Successfully loaded {len(discipline_cache)} disciplines into cache.")
            return True
        else:
             # Handle potential errors in response format
            error_message = "Unknown error fetching disciplines."
            if hasattr(response, 'error') and response.error:
                 error_message = response.error.message if hasattr(response.error, 'message') else str(response.error)
            logging.error(f"Failed to load disciplines: {error_message}")
            return False
    except Exception as e:
        logging.error(f"Exception while loading disciplines cache: {e}")
        return False

def get_discipline_id(discipline_name: str) -> int | None:
    """Gets discipline ID from the cache."""
    discipline_id = discipline_cache.get(discipline_name)
    if discipline_id is None:
        logging.warning(f"Discipline name '{discipline_name}' not found in cache (or database).")
    return discipline_id

def check_link_exists(supabase: Client, link: str) -> bool:
    """Checks if an article with the given link already exists."""
    if not link:
        logging.warning("Skipping check for empty link.")
        return False

    try:
        response = supabase.table('articles').select('id', count='exact').eq('link', link).limit(1).execute()
        if response.count is not None and response.count > 0:
            return True
        elif hasattr(response, 'data') and response.data:
             logging.warning(f"Query for link '{link}' returned data but count was {response.count}. Assuming exists.")
             return True
        return False
    except Exception as e:
        logging.error(f"Error checking link '{link}' in Supabase: {e}")
        return True # Safer to assume it exists if check fails

def clean_content(content: str) -> str:
    """Removes '## Revue' and '## Référence' sections from the content."""
    if not content:
        return ""
    # Use regex to split reliably, handling potential whitespace variations
    # Split at '## Revue' or '## Référence' that start on a new line (possibly preceded by whitespace)
    parts = re.split(r'^\s*##\s+(Revue|Référence)\s*$', content, flags=re.MULTILINE | re.IGNORECASE)
    return parts[0].strip() # Take the first part (before the split) and remove leading/trailing whitespace

def insert_article(supabase: Client, article_data: dict) -> int | None:
    """
    Inserts a new article into the Supabase table.
    Returns the new article's ID on success, None on failure.
    """
    original_content = article_data.get('content', '')
    cleaned_content = clean_content(original_content)

    data_to_insert = {
        'title': article_data.get('title', 'No Title Provided'),
        'content': cleaned_content, # Use cleaned content
        'published_at': article_data.get('published_at'),
        'link': article_data.get('link'),
        'journal': article_data.get('journal', 'Inconnu'),
        'grade': article_data.get('grade', 'A')
    }

    if not data_to_insert['title'] or not data_to_insert['content'] or not data_to_insert['link']:
       logging.warning(f"Skipping insertion due to missing essential data (title, content, or link) in source file.")
       return None

    try:
        # Use returning='minimal' if you don't need the full row back,
        # but default often includes the ID which we need.
        response = supabase.table('articles').insert(data_to_insert).execute()

        if response.data and len(response.data) > 0 and 'id' in response.data[0]:
            article_id = response.data[0]['id']
            logging.info(f"Successfully inserted article with link: {data_to_insert['link']} (ID: {article_id})")
            return article_id # Return the ID
        else:
            error_message = "Unknown insertion error or ID missing in response."
            if hasattr(response, 'error') and response.error:
                error_message = response.error.message if hasattr(response.error, 'message') else str(response.error)
            elif hasattr(response, 'status_code') and response.status_code >= 400:
                 error_message = f"HTTP Status {response.status_code}"
                 if hasattr(response, 'json') and callable(response.json):
                     try:
                         error_details = response.json()
                         error_message += f": {error_details.get('message', '')} {error_details.get('details', '')}"
                     except Exception: pass # Ignore if response body isn't JSON
            logging.error(f"Failed to insert article with link {data_to_insert['link']}. Response: {error_message}")
            return None # Indicate failure

    except Exception as e:
        logging.error(f"Exception during article insertion for link {data_to_insert['link']}: {e}")
        return None # Indicate failure

def link_article_to_discipline(supabase: Client, article_id: int, discipline_id: int):
    """Inserts a record into the article_disciplines table."""
    if not article_id or not discipline_id:
        logging.warning(f"Skipping linking: Invalid article_id ({article_id}) or discipline_id ({discipline_id})")
        return False

    data_to_insert = {
        'article_id': article_id,
        'discipline_id': discipline_id
    }
    try:
        # Check if link already exists (optional, but good practice)
        # Note: This adds an extra query per link. Consider removing if performance is critical
        # and duplicate errors are acceptable/handled.
        check_response = supabase.table('article_disciplines').select('article_id', count='exact').match(data_to_insert).execute()
        if check_response.count is not None and check_response.count > 0:
            logging.info(f"Link between article {article_id} and discipline {discipline_id} already exists. Skipping.")
            return True # Considered success as the link exists

        # Insert the link
        response = supabase.table('article_disciplines').insert(data_to_insert).execute()

        if response.data:
            logging.info(f"Successfully linked article {article_id} to discipline {discipline_id}.")
            return True
        else:
            error_message = "Unknown error linking article and discipline."
            if hasattr(response, 'error') and response.error:
                 error_message = response.error.message if hasattr(response.error, 'message') else str(response.error)
                 # Check specifically for duplicate key violation (code 23505)
                 if hasattr(response.error, 'code') and response.error.code == '23505':
                     logging.warning(f"Attempted to insert duplicate link for article {article_id} and discipline {discipline_id}. Ignoring.")
                     return True # Treat duplicate as non-fatal for this operation
            logging.error(f"Failed to link article {article_id} to discipline {discipline_id}. Response: {error_message}")
            return False

    except Exception as e:
        logging.error(f"Exception during linking article {article_id} to discipline {discipline_id}: {e}")
        return False


# --- File Processing ---

def process_directory(dir_path: str, supabase: Client):
    """Processes all .json files in the given directory."""
    if not os.path.isdir(dir_path):
        logging.error(f"Error: Provided path '{dir_path}' is not a valid directory.")
        return

    # --- Load discipline cache first ---
    if not load_disciplines_cache(supabase):
         logging.error("Failed to load discipline cache. Cannot proceed with discipline linking.")
         # Decide if you want to exit or just continue without linking
         # exit(1) # Option to exit
         # Fall through to continue without linking if cache fails

    logging.info(f"Processing directory: {dir_path}")
    article_inserted_count = 0
    article_skipped_count = 0
    article_error_count = 0
    discipline_linked_count = 0
    discipline_link_failed_count = 0
    processed_files = 0

    for filename in os.listdir(dir_path):
        if filename.lower().endswith(".json"):
            file_path = os.path.join(dir_path, filename)
            logging.info(f"--- Processing file: {filename} ---")
            processed_files += 1
            new_article_id = None # Reset for each file

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    try:
                        article_data = json.load(f)
                    except json.JSONDecodeError as json_e:
                        logging.error(f"Error decoding JSON from file {filename}: {json_e}")
                        article_error_count += 1
                        continue # Skip to next file

                # === Article Insertion ===
                link = article_data.get('link')
                if not link:
                    logging.warning(f"Skipping file {filename}: 'link' field is missing or empty in the JSON.")
                    article_skipped_count += 1
                    continue

                if check_link_exists(supabase, link):
                    logging.info(f"Skipping file {filename}: Link '{link}' already exists in the database.")
                    article_skipped_count += 1
                else:
                    new_article_id = insert_article(supabase, article_data) # Attempt insert
                    if new_article_id:
                        article_inserted_count += 1
                    else:
                        article_error_count += 1 # Error logged in insert_article

                # === Discipline Linking (only if article was newly inserted) ===
                if new_article_id and cache_loaded: # Only proceed if insert succeeded AND cache is loaded
                    categories = article_data.get('categories', [])
                    if isinstance(categories, list) and categories:
                        logging.info(f"Attempting to link disciplines for article ID {new_article_id}...")
                        for category_name in categories:
                            if not isinstance(category_name, str) or not category_name.strip():
                                logging.warning(f"Skipping invalid category name: {category_name}")
                                continue

                            discipline_id = get_discipline_id(category_name.strip()) # Use cached lookup
                            if discipline_id:
                                if link_article_to_discipline(supabase, new_article_id, discipline_id):
                                    discipline_linked_count += 1
                                else:
                                    discipline_link_failed_count += 1
                            else:
                                # Warning already logged by get_discipline_id
                                discipline_link_failed_count += 1 # Count as failed if discipline not found
                    elif categories:
                         logging.warning(f"Categories field in {filename} is not a list or is empty. Skipping discipline linking.")
                    # else: # No categories field, which is fine.
                    #    logging.debug(f"No categories found in {filename} for article {new_article_id}.")


            except IOError as io_e:
                logging.error(f"Error reading file {filename}: {io_e}")
                article_error_count += 1
            except KeyError as key_e:
                 logging.error(f"Missing expected key '{key_e}' in file {filename}.")
                 article_error_count += 1
            except Exception as e:
                logging.error(f"An unexpected error occurred processing file {filename}: {e}")
                article_error_count += 1
            finally:
                logging.info(f"--- Finished processing file: {filename} ---")


    logging.info("=" * 30)
    logging.info("Processing Summary:")
    logging.info(f"Total JSON files processed: {processed_files}")
    logging.info(f"Articles inserted:        {article_inserted_count}")
    logging.info(f"Articles skipped (exists):  {article_skipped_count}")
    logging.info(f"Article processing errors: {article_error_count}")
    if cache_loaded:
        logging.info(f"Discipline links created: {discipline_linked_count}")
        logging.info(f"Discipline links failed:  {discipline_link_failed_count} (includes missing disciplines)")
    else:
        logging.warning("Discipline cache failed to load; linking was skipped.")
    logging.info("=" * 30)

# --- Main Execution ---

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export JSON files from a directory to Supabase 'articles' and 'article_disciplines' tables.")
    parser.add_argument("directory", help="Path to the directory containing the .json files.")
    args = parser.parse_args()

    try:
        logging.info("Connecting to Supabase...")
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test connection (optional but recommended)
        try:
             supabase.table('articles').select('id').limit(1).execute()
             logging.info("Supabase connection successful.")
        except Exception as conn_e:
             logging.error(f"Supabase connection test failed: {conn_e}")
             exit(1)

        process_directory(args.directory, supabase)
    except Exception as e:
        logging.error(f"Failed to connect to Supabase or critical error: {e}")
        exit(1)

    logging.info("Script finished.")