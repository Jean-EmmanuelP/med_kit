import os
import json
import time
import argparse
import sys
from collections import defaultdict # For grouping subdisciplines
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai
from tqdm import tqdm  # For progress bar

# --- Configuration ---
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") # Use Service Role Key
GEMINI_API_KEY = os.getenv("GOOGLE_API_KEY") # Using GOOGLE_API_KEY

# --- Constants ---
RESULTS_DIR = "../subdisciplines/gemini-results" # Directory for logs AND state tracking
BATCH_SIZE = 1
GEMINI_MODEL = "gemini-2.0-flash" # Standard model name
REQUEST_DELAY_SECONDS = 2 # Initial delay, might be overridden by API response

# Ensure results directory exists
os.makedirs(RESULTS_DIR, exist_ok=True)

# --- Argument Parser ---
def setup_arg_parser():
    parser = argparse.ArgumentParser(
        description="Process articles with Gemini for sub-disciplines (max 3 per parent, JSON output) and populate DB. Skips saving file on Gemini API errors."
    )
    parser.add_argument("--batch_size", type=int, default=BATCH_SIZE, help=f"Articles per batch (default: {BATCH_SIZE}).")
    parser.add_argument("--delay", type=float, default=REQUEST_DELAY_SECONDS, help=f"Base delay between Gemini calls (s) (default: {REQUEST_DELAY_SECONDS}).")
    parser.add_argument("--max_articles", type=int, default=None, help="Max articles to process this run (optional).")
    return parser

# --- State Management ---
def load_processed_ids() -> set[int]:
    """Loads processed IDs by scanning the results directory."""
    processed_ids = set()
    print(f"Scanning directory '{RESULTS_DIR}' for processed article IDs...")
    if not os.path.isdir(RESULTS_DIR):
        print(f"  Warning: Results directory '{RESULTS_DIR}' not found. Creating it.")
        try: os.makedirs(RESULTS_DIR)
        except OSError as e: print(f"  Error: Could not create results directory: {e}. Exiting."); sys.exit(1)
        return processed_ids
    try:
        for filename in os.listdir(RESULTS_DIR):
            if filename.endswith(".json"):
                base_name = filename[:-5]
                try: processed_ids.add(int(base_name))
                except ValueError: print(f"  Warning: Skipping file with non-integer name: {filename}")
    except Exception as e: print(f"  Error scanning results directory: {e}")
    print(f"Found {len(processed_ids)} previously processed article IDs from result files.")
    return processed_ids

# --- Database Functions ---
# (fetch_disciplines_data, fetch_subdisciplines_data, fetch_article_discipline_ids remain the same)
def fetch_disciplines_data(supabase: Client) -> dict[int, str]:
    discipline_id_to_name_map = {}
    try:
        response = supabase.table("disciplines").select("id, name").execute()
        if response.data:
            for item in response.data: discipline_id_to_name_map[item["id"]] = item["name"]
        elif hasattr(response, 'error') and response.error: print(f"DB Error fetching disciplines: {response.error}", file=sys.stderr)
    except Exception as e: print(f"Exception fetching disciplines: {e}", file=sys.stderr)
    return discipline_id_to_name_map

def fetch_subdisciplines_data(supabase: Client) -> tuple[dict[int, list[str]], dict[str, int]]:
    grouped_subdisciplines = defaultdict(list)
    subdiscipline_name_to_id_map = {}
    try:
        response = supabase.table("sub_disciplines").select("id, name, discipline_id").execute()
        if response.data:
            for item in response.data:
                grouped_subdisciplines[item["discipline_id"]].append(item["name"])
                subdiscipline_name_to_id_map[item["name"]] = item["id"]
            for disc_id in grouped_subdisciplines: grouped_subdisciplines[disc_id].sort()
        elif hasattr(response, 'error') and response.error: print(f"DB Error fetching subdisciplines: {response.error}", file=sys.stderr)
    except Exception as e: print(f"Exception fetching subdisciplines: {e}", file=sys.stderr)
    return dict(grouped_subdisciplines), subdiscipline_name_to_id_map

def fetch_article_discipline_ids(supabase: Client, article_id: int) -> list[int]:
    try:
        response = supabase.table("article_disciplines").select("discipline_id").eq("article_id", article_id).execute()
        if response.data: return [item["discipline_id"] for item in response.data]
        else:
            if hasattr(response, 'error') and response.error: print(f"  DB Error fetching discipline IDs for article {article_id}: {response.error}", file=sys.stderr)
            return []
    except Exception as e: print(f"  Exception fetching discipline IDs for article {article_id}: {e}", file=sys.stderr); return []

def fetch_articles_batch(supabase: Client, processed_ids: set[int], limit: int) -> list[dict]:
    """ Fetches unprocessed articles including the 'link' field. """
    try:
        query = supabase.table("articles").select("id, title, content, link")
        if processed_ids: query = query.not_.in_("id", list(processed_ids))
        response = query.limit(limit).order("id", desc=False).execute()
        if response.data: return response.data
        elif hasattr(response, 'error') and response.error: print(f"DB Error fetching articles: {response.error}", file=sys.stderr)
        else: return []
    except Exception as e: print(f"Exception fetching articles: {e}", file=sys.stderr); return []

def insert_article_subdiscipline_link(supabase: Client, article_id: int, sub_discipline_id: int):
    """ Inserts link between article and sub-discipline, ignoring duplicates. """
    try:
        data = {"article_id": article_id, "sub_discipline_id": sub_discipline_id}
        supabase.table("article_sub_disciplines").upsert(data, on_conflict="article_id, sub_discipline_id", ignore_duplicates=True).execute()
    except Exception as e: print(f"  Exception inserting link ({article_id}, {sub_discipline_id}): {e}", file=sys.stderr)

# --- Gemini Functions ---
# (build_relevant_subdiscipline_list_string_for_prompt remains the same)
def build_relevant_subdiscipline_list_string_for_prompt(
    parent_discipline_ids: list[int],
    discipline_id_to_name_map: dict[int, str],
    grouped_subdisciplines_by_discipline_id: dict[int, list[str]]
) -> tuple[str, set[str]]:
    prompt_lines = []
    relevant_subdiscipline_names_set = set()
    for disc_id in sorted(parent_discipline_ids):
        discipline_name = discipline_id_to_name_map.get(disc_id)
        sub_discipline_names = grouped_subdisciplines_by_discipline_id.get(disc_id, [])
        if discipline_name and sub_discipline_names:
            prompt_lines.append(f"\nParent Discipline: {discipline_name}")
            for name in sub_discipline_names:
                prompt_lines.append(f"- {name}")
                relevant_subdiscipline_names_set.add(name)
    return "\n".join(prompt_lines).strip(), relevant_subdiscipline_names_set

# (construct_gemini_prompt_json remains the same)
def construct_gemini_prompt_json(title: str, content: str, relevant_subdiscipline_list_str: str) -> str:
    full_content = content
    prompt = f"""You are an expert in specialized medicine. Your role is to analyze a medical article (title + abstract/content) and assign it to relevant medical sub-specialties from a provided list. This list is grouped by the article's parent disciplines.

Steps to follow:
1. Carefully read the title and the entire abstract/content of the article.
2. For EACH "Parent Discipline" section in the list below:
    a. Identify the main clinical themes relevant to THAT parent discipline.
    b. Compare these themes with the sub-specialties listed ONLY under THAT parent discipline heading.
    c. Select 1 to 3 of the MOST relevant sub-specialties from THAT specific group. Prioritize the single most relevant sub-specialty if possible. Add 1 or 2 more ONLY if the article significantly contributes to those specific areas *within that parent discipline*. If none are relevant for a parent discipline, the list for that discipline should be empty in the final JSON.

Assignment Rules:
- You MUST consider each "Parent Discipline" group independently.
- Select a maximum of 3 sub-specialties *per parent discipline group*.
- NEVER suggest a sub-specialty not listed under its corresponding parent discipline below.
- NEVER create a new category or suggest a general specialty.
- Your response MUST be ONLY a valid JSON object and nothing else. The keys of the JSON object should be the exact "Parent Discipline" names provided in the list below. The value for each key must be a JSON list of strings, containing the exact names of the 0 to 3 selected sub-specialties for that parent discipline.
- Ensure the entire output is ONLY the JSON object. Do not include *any* introductory text, concluding text, or any other markers before or after the JSON object itself.

Example JSON Output Format:
{{
  "Cardiology": ["Cardiac Imaging", "Interventional Cardiology"],
  "Pulmonology": ["Sleep Medicine"],
  "Neurology": []
}}

Here is the article to classify:
Title: {title}

Abstract/Content:
{full_content}


Here is the specific list of relevant sub-specialties, grouped by their parent discipline:
{relevant_subdiscipline_list_str}


Your response (ONLY the JSON object in the specified format, starting with {{ and ending with }}):"""
    return prompt

# Modified call_gemini to potentially return retry delay
def call_gemini(model, prompt: str) -> tuple[str | None, int | None]:
    """ Calls the Gemini API. Returns (raw potential JSON string | None, retry_delay_seconds | None). """
    retry_delay = None
    try:
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        ]
        response = model.generate_content(prompt, safety_settings=safety_settings)

        if not response.parts:
            finish_reason = 'UNKNOWN'; safety_ratings = []
            if hasattr(response, 'candidates') and response.candidates:
                 candidate = response.candidates[0]
                 finish_reason = getattr(candidate, 'finish_reason', 'UNKNOWN')
                 safety_ratings = getattr(candidate, 'safety_ratings', [])
            # Check specifically for rate limit finish reason if available
            if finish_reason == 'RATE_LIMIT_EXCEEDED':
                 # Attempt to extract retry delay (might not always be present)
                 if hasattr(response, 'usage_metadata') and response.usage_metadata:
                      retry_delay = response.usage_metadata.get('retry_delay', {}).get('seconds')
                 print(f"  Warning: Gemini Rate Limit Exceeded. Suggested delay: {retry_delay}s")
            else:
                 print(f"  Warning: Gemini response empty/blocked. Reason: {finish_reason}, Ratings: {safety_ratings}, Feedback: {response.prompt_feedback}")
            return None, retry_delay # Return None for response, potentially with delay

        raw_text = response.text.strip()
        if raw_text.startswith("```json"): raw_text = raw_text[7:]
        elif raw_text.startswith("```"): raw_text = raw_text[3:]
        if raw_text.endswith("```"): raw_text = raw_text[:-3]
        return raw_text.strip(), None # Return response, no specific delay needed

    except Exception as e:
        # Check if the exception message indicates a 429 error (more robust check might be needed)
        if "429" in str(e):
             print(f"  Error calling Gemini API (429 Rate Limit): {e}", file=sys.stderr)
             # Could try to parse retry delay from exception string if needed, but often not present there
        else:
             print(f"  Error calling Gemini API: {e}", file=sys.stderr)
        return None, None # Return None for response, no delay info from exception


def parse_gemini_json_response(response_text: str, valid_subdisciplines_for_article: set[str]) -> list[str]:
    """ Parses the JSON response from Gemini and returns a FLAT list of validated subdiscipline names. """
    if not response_text: return []
    validated_names = []
    try:
        data = json.loads(response_text)
        if not isinstance(data, dict):
            print(f"  Warning: Gemini response was valid JSON but not dict: {type(data)}. Content: {response_text[:200]}...")
            return []
        for parent_discipline, selected_subs in data.items():
            if not isinstance(selected_subs, list):
                print(f"  Warning: Value for parent '{parent_discipline}' not list: {selected_subs}. Skip.")
                continue
            for sub_name in selected_subs:
                if not isinstance(sub_name, str):
                    print(f"  Warning: Item in list for '{parent_discipline}' not str: {sub_name}. Skip.")
                    continue
                sub_name_cleaned = sub_name.strip()
                if sub_name_cleaned in valid_subdisciplines_for_article:
                    validated_names.append(sub_name_cleaned)
                elif sub_name_cleaned:
                        print(f"  Warning: Gemini JSON invalid subdiscipline '{sub_name_cleaned}'. Ignoring.")
    except json.JSONDecodeError as e:
        print(f"  Error: Failed to decode Gemini response as JSON: {e}", file=sys.stderr)
        print(f"  Raw response snippet: {response_text[:500]}...")
        return []
    except Exception as e:
         print(f"  Error processing Gemini JSON structure: {e}", file=sys.stderr)
         return []
    return validated_names

# --- Utility Function ---
# Modified save_gemini_result to accept status string
def save_gemini_result(article_id: int, title: str, content: str, link: str | None, status_or_response: str):
    """ Saves article details, link, and Gemini status/response to JSON in RESULTS_DIR. """
    filepath = os.path.join(RESULTS_DIR, f"{article_id}.json")
    data_to_save = {
        "article_id": article_id,
        "title": title,
        "link": link,
        "content_preview": content[:500] + "...",
        "gemini_raw_response": status_or_response # Store status or actual response
    }
    try:
        with open(filepath, "w", encoding="utf-8") as f: json.dump(data_to_save, f, indent=2, ensure_ascii=False)
    except IOError as e: print(f"  Error saving result file '{filepath}': {e}", file=sys.stderr)

# --- Main Execution ---
def main():
    parser = setup_arg_parser()
    args = parser.parse_args()
    batch_size = args.batch_size
    current_delay = args.delay # Use a variable for delay that might change
    max_articles_to_process = args.max_articles

    print("--- Starting Article Sub-discipline Processing (Max 3 per Parent, JSON Output, No Save on API Error) ---")

    if not all([SUPABASE_URL, SUPABASE_KEY, GEMINI_API_KEY]):
        print("Error: Supabase/Gemini config missing.", file=sys.stderr); sys.exit(1)
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        genai.configure(api_key=GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel(GEMINI_MODEL)
        print("Supabase and Gemini clients initialized.")
    except Exception as e: print(f"Error initializing clients: {e}", file=sys.stderr); sys.exit(1)

    processed_ids = load_processed_ids()

    print("Fetching static discipline & subdiscipline data...")
    discipline_id_to_name_map = fetch_disciplines_data(supabase)
    grouped_subdisciplines_by_disc_id, subdiscipline_name_to_id_map = fetch_subdisciplines_data(supabase)
    if not discipline_id_to_name_map or not subdiscipline_name_to_id_map:
        print("Exiting: Failed to fetch discipline/subdiscipline data.", file=sys.stderr); sys.exit(1)
    print(f"Fetched {len(discipline_id_to_name_map)} disciplines and {len(subdiscipline_name_to_id_map)} subdisciplines.")

    total_processed_in_run = 0
    articles_processed_this_batch = 0 # Track processed within the current fetch batch
    while True:
        if max_articles_to_process is not None and total_processed_in_run >= max_articles_to_process:
            print(f"\nReached processing limit ({max_articles_to_process}).")
            break

        limit = batch_size
        if max_articles_to_process is not None:
             limit = min(batch_size, max_articles_to_process - total_processed_in_run)
        if limit <= 0: break

        print(f"\nFetching next batch of up to {limit} articles...")
        articles = fetch_articles_batch(supabase, processed_ids, limit)
        if not articles: print("No more unprocessed articles found."); break

        print(f"Processing batch of {len(articles)} articles...")
        articles_processed_this_batch = 0 # Reset for new batch

        for article in tqdm(articles, desc="Processing Batch"):
            article_id = article["id"]
            if article_id in processed_ids: continue # Skip if already processed

            title = article["title"]
            content = article["content"]
            link = article.get("link")

            # --- Pre-Gemini Skip Conditions ---
            parent_discipline_ids = fetch_article_discipline_ids(supabase, article_id)
            if not parent_discipline_ids:
                skip_reason = "SKIPPED - No Parent Disciplines"
                tqdm.write(f"\n  Skipping Article {article_id}: No parent disciplines.")
                save_gemini_result(article_id, title, content, link, skip_reason) # Save skip status
                processed_ids.add(article_id); total_processed_in_run += 1; articles_processed_this_batch += 1
                continue # Move to next article

            relevant_subdiscipline_list_str, relevant_subdiscipline_names_set = build_relevant_subdiscipline_list_string_for_prompt(
                parent_discipline_ids, discipline_id_to_name_map, grouped_subdisciplines_by_disc_id
            )
            if not relevant_subdiscipline_names_set:
                skip_reason = "SKIPPED - No Relevant Subdisciplines"
                tqdm.write(f"\n  Skipping Article {article_id}: No relevant subdisciplines.")
                save_gemini_result(article_id, title, content, link, skip_reason) # Save skip status
                processed_ids.add(article_id); total_processed_in_run += 1; articles_processed_this_batch += 1
                continue # Move to next article

            # --- Gemini Call ---
            prompt = construct_gemini_prompt_json(title, content, relevant_subdiscipline_list_str)
            gemini_response_raw, retry_delay_seconds = call_gemini(gemini_model, prompt)

            # --- Post-Gemini Processing ---
            if gemini_response_raw is not None:
                # Successful API call (might still be invalid JSON, but API didn't fail)
                # Save result file for successful API call
                save_gemini_result(article_id, title, content, link, gemini_response_raw)
                processed_ids.add(article_id)
                total_processed_in_run += 1
                articles_processed_this_batch += 1

                # Parse and Insert Links
                chosen_subdiscipline_names = parse_gemini_json_response(gemini_response_raw, relevant_subdiscipline_names_set)
                if chosen_subdiscipline_names:
                    tqdm.write(f"\n  Article {article_id}: Linking to {chosen_subdiscipline_names}")
                    for name in chosen_subdiscipline_names:
                        sub_discipline_id = subdiscipline_name_to_id_map.get(name)
                        if sub_discipline_id:
                            insert_article_subdiscipline_link(supabase, article_id, sub_discipline_id)
                        else:
                             tqdm.write(f"\n  Error: Could not find ID for validated subdiscipline '{name}' for article {article_id}.", file=sys.stderr)

                # Reset delay after successful call
                current_delay = args.delay
            else:
                # Gemini API call failed (returned None) - DO NOT SAVE FILE, DO NOT mark as processed
                tqdm.write(f"\n  Gemini API call failed for Article {article_id}. Will retry later.")
                # Increase delay if suggested by API
                if retry_delay_seconds is not None:
                     wait_time = max(retry_delay_seconds, args.delay) # Use suggested or base delay, whichever is longer
                     tqdm.write(f"    API suggested retry delay: {retry_delay_seconds}s. Waiting {wait_time}s.")
                     time.sleep(wait_time)
                     current_delay = args.delay # Reset delay for next attempt after waiting
                else:
                    # Apply base delay even on failure to avoid hammering
                    time.sleep(current_delay)
                continue # Skip to next article without marking current one processed

            # --- Loop Control & Delay ---
            if max_articles_to_process is not None and total_processed_in_run >= max_articles_to_process: break
            # Apply the current delay (might have been increased by rate limit response)
            # But only if the last call wasn't rate limited (already waited)
            if retry_delay_seconds is None:
                 time.sleep(current_delay)

        # --- End of Batch Loop ---
        # Optional: Add a longer pause between batches if rate limiting is frequent
        if articles_processed_this_batch < len(articles) and articles: # Check if batch ended early due to errors
             tqdm.write("\nBatch finished early due to API errors. Pausing before next fetch...")
             time.sleep(current_delay * 2) # Extra pause

        if max_articles_to_process is not None and total_processed_in_run >= max_articles_to_process: break

    # --- End of Main Loop ---
    print("\n--- Processing Complete ---")
    print(f"Total articles processed or skipped (saved file): {total_processed_in_run}")
    print(f"Final count of result files in '{RESULTS_DIR}': {len(os.listdir(RESULTS_DIR))}") # Verify count

if __name__ == "__main__":
    main()