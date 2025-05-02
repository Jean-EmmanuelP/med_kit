import os
import json
import logging
import argparse
from typing import Dict, List, Tuple

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Constants ---
OUTPUT_DIR = "output"
CAT1_INPUT_FILENAME = os.path.join(OUTPUT_DIR, "category_1_recommendations.json")
SUMMARIES_DIR = os.path.join(OUTPUT_DIR, "recommendation_summaries")
TOP_SUMMARIES_TXT_FILENAME = os.path.join(OUTPUT_DIR, "top_3_summaries.txt")
NUM_TOP_SUMMARIES = 3

# --- Helper Functions ---

def load_link_map(filepath: str) -> Dict[int, str]:
    """Loads the mapping from article ID to PubMed link from the Cat1 JSON."""
    link_map: Dict[int, str] = {}
    if not os.path.exists(filepath):
        logger.error(f"Input file for link mapping not found: {filepath}")
        return link_map
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.error(f"Link mapping file {filepath} is not a JSON list.")
            return link_map

        for item in data:
            if isinstance(item, dict) and item.get('id') is not None and item.get('link'):
                try:
                    article_id = int(item['id'])
                    link_map[article_id] = item['link']
                except (ValueError, TypeError):
                    logger.warning(f"Skipping invalid ID/link pair in {filepath}: {item}")
            else:
                 logger.warning(f"Skipping invalid item format in {filepath}: {item}")

        logger.info(f"Loaded link map with {len(link_map)} entries from {filepath}")
        return link_map
    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from link map file: {filepath}")
        return {}
    except Exception as e:
        logger.error(f"Error loading link map from {filepath}: {e}")
        return {}

def update_summary_file_with_link(summary_filepath: str, article_id: int, link_map: Dict[int, str]) -> bool:
    """Reads a summary JSON, adds the pubmed_link if missing, and saves it back."""
    try:
        with open(summary_filepath, 'r', encoding='utf-8') as f:
            summary_data = json.load(f)

        if not isinstance(summary_data, dict):
             logger.warning(f"Content of {summary_filepath} is not a dictionary. Skipping update.")
             return False

        if "pubmed_link" in summary_data:
            logger.debug(f"'pubmed_link' already exists in {summary_filepath}. Skipping update.")
            return True # Already done

        # Lookup link
        pubmed_link = link_map.get(article_id)
        if not pubmed_link:
            logger.warning(f"Could not find PubMed link for ID {article_id} in the map. Cannot update {summary_filepath}.")
            return False

        # Add the link and save
        summary_data["pubmed_link"] = pubmed_link
        with open(summary_filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Added 'pubmed_link' to {summary_filepath}")
        return True

    except json.JSONDecodeError:
        logger.error(f"Failed to decode JSON from {summary_filepath}. Cannot update.")
        return False
    except IOError as e:
        logger.error(f"I/O error processing {summary_filepath}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating {summary_filepath}: {e}")
        return False

def get_sorted_summary_files(summaries_dir: str) -> List[Tuple[int, str]]:
    """Gets all summary JSON files, extracts IDs, and sorts them numerically."""
    summary_files: List[Tuple[int, str]] = []
    if not os.path.isdir(summaries_dir):
        logger.error(f"Summaries directory not found: {summaries_dir}")
        return []

    for filename in os.listdir(summaries_dir):
        if filename.lower().endswith(".json"):
            try:
                article_id_str = os.path.splitext(filename)[0]
                article_id = int(article_id_str)
                full_path = os.path.join(summaries_dir, filename)
                summary_files.append((article_id, full_path))
            except (ValueError, TypeError):
                logger.warning(f"Could not parse article ID from filename: {filename}")

    # Sort by article ID (the integer)
    summary_files.sort(key=lambda x: x[0])
    return summary_files


def generate_top_summaries_txt(sorted_summary_files: List[Tuple[int, str]], num_to_take: int, output_txt_file: str):
    """Reads the top N summaries and writes them to a text file."""
    if not sorted_summary_files:
        logger.warning("No summary files found to generate TXT output.")
        return

    num_available = len(sorted_summary_files)
    num_to_process = min(num_to_take, num_available)
    logger.info(f"Generating TXT file with the top {num_to_process} summaries.")

    output_content = []

    for i in range(num_to_process):
        article_id, summary_filepath = sorted_summary_files[i]
        logger.debug(f"Processing top summary #{i+1}: ID {article_id}, File: {summary_filepath}")
        try:
            with open(summary_filepath, 'r', encoding='utf-8') as f:
                summary_data = json.load(f)

            pubmed_link = summary_data.get("pubmed_link", "Link not found")
            summary_text = summary_data.get("summary", "Summary not found")

            output_content.append(f"{pubmed_link}\n\n{summary_text}")

        except json.JSONDecodeError:
             logger.error(f"Failed to decode JSON for top summary file: {summary_filepath}. Skipping.")
        except IOError as e:
            logger.error(f"I/O error reading top summary file {summary_filepath}: {e}. Skipping.")
        except Exception as e:
             logger.error(f"Unexpected error processing top summary file {summary_filepath}: {e}. Skipping.")

    # Write the combined content to the output file
    try:
        with open(output_txt_file, 'w', encoding='utf-8') as f:
            # Join entries with a separator (e.g., a line of dashes and two newlines)
            f.write("\n\n---\n\n".join(output_content))
        logger.info(f"Successfully wrote top {num_to_process} summaries to {output_txt_file}")
    except IOError as e:
        logger.error(f"Failed to write TXT output file {output_txt_file}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error writing TXT output file {output_txt_file}: {e}")


# --- Main Execution ---
def main():
    """Main function to add links and generate TXT file."""
    logger.info("--- Starting Script: Add Links & Generate Top Summaries TXT ---")

    # 1. Load the ID -> Link map
    link_map = load_link_map(CAT1_INPUT_FILENAME)
    if not link_map:
        logger.error("Failed to load link map. Cannot proceed with updating summary files.")
        # Decide if you want to proceed to TXT generation anyway (links will be missing)
        # return # Option to stop here

    # 2. Iterate through summary files and update them
    logger.info(f"Scanning directory for summaries to update: {SUMMARIES_DIR}")
    updated_count = 0
    update_failed_count = 0
    skipped_count = 0

    if not os.path.isdir(SUMMARIES_DIR):
        logger.error(f"Summaries directory not found: {SUMMARIES_DIR}. Cannot update files or generate TXT.")
        return

    for filename in os.listdir(SUMMARIES_DIR):
        if filename.lower().endswith(".json"):
            try:
                article_id_str = os.path.splitext(filename)[0]
                article_id = int(article_id_str)
                summary_filepath = os.path.join(SUMMARIES_DIR, filename)

                # Call update function (it checks if update is needed)
                success = update_summary_file_with_link(summary_filepath, article_id, link_map)
                if success is True and "pubmed_link" not in open(summary_filepath).read(): # Re-check if it was actually updated vs already present
                     updated_count +=1
                elif success is False:
                     update_failed_count +=1
                # No explicit skipped count here as the function handles logging skips

            except (ValueError, TypeError):
                logger.warning(f"Could not parse article ID from filename during update scan: {filename}")
                update_failed_count += 1
            except Exception as e:
                 logger.error(f"Unexpected error during update scan for {filename}: {e}")
                 update_failed_count += 1

    logger.info(f"Finished updating summary files. Actual updates performed: {updated_count}, Failures/Skips: {update_failed_count}")

    # 3. Get sorted list of summary files (needed for finding the 'first' ones)
    sorted_summary_files = get_sorted_summary_files(SUMMARIES_DIR)

    # 4. Generate the TXT file for the top N summaries
    generate_top_summaries_txt(sorted_summary_files, NUM_TOP_SUMMARIES, TOP_SUMMARIES_TXT_FILENAME)

    logger.info("--- Script Finished ---")

if __name__ == "__main__":
    # No command-line arguments needed for this specific task as paths are fixed
    main()