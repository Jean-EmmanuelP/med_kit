# update_recommandations.py

import os
import json
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
OUTPUT_DIR = 'output'
# ---------------------


def format_recommandation_to_markdown(item: dict | list | str, level: int = 1) -> str:
    """
    Recursively formats a recommendation object into a Markdown string.
    This is a corrected, direct Python translation of the provided JavaScript logic.

    Args:
        item: The dictionary, list, or string to format.
        level: The current heading level for Markdown (e.g., 1 for #, 2 for ##).

    Returns:
        A Markdown formatted string, preserving trailing newlines for proper spacing.
    """
    markdown_str = ""

    if isinstance(item, dict):
        # Handle objects with 'titre' and 'contenu'
        if 'titre' in item:
            heading_prefix = '#' * level
            markdown_str += f"{heading_prefix} {item['titre']}\n\n"

        if 'contenu' in item:
            contenu = item['contenu']
            if isinstance(contenu, list):
                # If 'contenu' is a list, iterate through its elements
                for sub_item in contenu:
                    # For sub-items, increase the level for sub-headings
                    markdown_str += format_recommandation_to_markdown(sub_item, level + 1)
            elif isinstance(contenu, str):
                # If 'contenu' is a string, treat it as a paragraph
                markdown_str += f"{contenu}\n\n"
    
    elif isinstance(item, str):
        # This handles cases where a simple string might be in a 'contenu' array
        markdown_str += f"{item}\n\n"

    # The original JS implicitly returns the string with trailing newlines.
    # We will do the same by not stripping the string.
    return markdown_str


def main():
    """
    Main function to process JSON files and update the Supabase database.
    """
    # 1. Load environment variables from .env file
    load_dotenv()
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logging.error("Missing SUPABASE_URL or SUPABASE_KEY in the .env file. Exiting.")
        return

    # 2. Initialize Supabase client
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logging.info("Successfully connected to Supabase.")
    except Exception as e:
        logging.error(f"Failed to initialize Supabase client: {e}")
        return

    # 3. Check if the output directory exists
    if not os.path.isdir(OUTPUT_DIR):
        logging.error(f"Directory '{OUTPUT_DIR}' not found. Please create it and add your JSON files.")
        return
        
    # 4. Iterate through all .json files in the output directory
    json_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.json')]
    if not json_files:
        logging.warning(f"No .json files found in the '{OUTPUT_DIR}' directory.")
        return
        
    logging.info(f"Found {len(json_files)} JSON files to process.")
    
    successful_updates = 0
    failed_updates = 0

    for filename in json_files:
        file_path = os.path.join(OUTPUT_DIR, filename)
        logging.info(f"--- Processing file: {filename} ---")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # 5. Extract link and recommendation data
            link = data.get('link')
            reco_data = data.get('recommandation')

            if not link or not reco_data:
                logging.warning(f"Skipping {filename}: missing 'link' or 'recommandation' key.")
                failed_updates += 1
                continue

            # 6. Format the content to Markdown using the corrected function
            # The initial call starts at level 1, which the function default handles correctly.
            formatted_content = format_recommandation_to_markdown(reco_data, 1)
            
            # 7. Prepare the data for the update
            update_payload = {
                'is_recommandation': True,
                'content': formatted_content.strip() # Strip only at the very end before DB insert
            }
            
            # 8. Execute the update query in Supabase
            logging.info(f"Attempting to update article with link: {link}")
            response = supabase.table('articles').update(update_payload).eq('link', link).execute()

            if response.data:
                logging.info(f"✅ Successfully updated article for link: {link}")
                # Delete the processed file after successful update
                try:
                    os.remove(file_path)
                    logging.info(f"🗑️ Deleted processed file: {filename}")
                except Exception as delete_error:
                    logging.warning(f"⚠️ Could not delete file {filename}: {delete_error}")
                successful_updates += 1
            else:
                logging.warning(f"⚠️ No article found with link: {link}. No update was performed.")
                failed_updates += 1

        except json.JSONDecodeError:
            logging.error(f"❌ Failed to parse JSON from {filename}. Please check its format.")
            failed_updates += 1
        except Exception as e:
            logging.error(f"❌ An unexpected error occurred while processing {filename}: {e}")
            failed_updates += 1

    logging.info("\n--- Processing Complete ---")
    logging.info(f"✅ Successful updates: {successful_updates}")
    logging.info(f"❌ Failed or skipped files: {failed_updates}")
    logging.info("-------------------------")


if __name__ == "__main__":
    main()