import os
import argparse
import json
import logging
import time
import re
# --- MODIFIED: Use datetime from datetime for consistency ---
from datetime import datetime, timezone, date # Added 'date'
from dotenv import load_dotenv
import google.generativeai as genai
from dateutil.parser import parse as dateutil_parse
from google.api_core.exceptions import GoogleAPIError
import hashlib

# --- Configuration ---
# --- MODIFIED: Changed base output directory name ---
OUTPUT_DIR = "summaries"  # Base directory to save date-specific summary folders
# --- MODIFIED: Add timestamp format for consistency ---
TIMESTAMP_FORMAT = '%Y%m%d' # YYYYMMDD format
MODEL_NAME = "gemini-2.0-flash" # Or "gemini-1.0-pro" if JSON mode is desired and available
API_RETRY_DELAY = 5
API_MAX_RETRIES = 3
DEFAULT_GRADE = "A"

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# --- Google AI Setup ---
if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not found.")
    exit(1)

genai.configure(api_key=GOOGLE_API_KEY)

generation_config = genai.GenerationConfig(
    # response_mime_type="application/json", # Keep commented unless using Pro with native JSON support
    temperature=0.3,
    max_output_tokens=2000, # Adjust if needed, 2000 is reasonable for summaries
)

try:
    model = genai.GenerativeModel(
        MODEL_NAME,
        generation_config=generation_config,
    )
    logger.info(f"Google AI Model '{MODEL_NAME}' initialized.")
except Exception as e:
    logger.error(f"Failed to initialize Google AI Model: {e}")
    exit(1)

# --- Helper Functions (No changes needed in these helpers) ---

def safe_api_call(prompt, max_retries=API_MAX_RETRIES, delay=API_RETRY_DELAY):
    """Makes an API call with retry logic, expects text response."""
    retries = 0
    while retries < max_retries:
        try:
            time.sleep(1) # Small delay before each call
            logger.debug(f"Sending API request (attempt {retries + 1}/{max_retries})...")
            response = model.generate_content(prompt)

            # Check for blocking reasons first
            if response.prompt_feedback and response.prompt_feedback.block_reason:
                 block_reason = response.prompt_feedback.block_reason
                 logger.warning(f"API call blocked. Reason: {block_reason}. Prompt starts: '{prompt[:150]}...'")
                 return f"ERROR: Blocked by API ({block_reason})"

            # Check safety ratings and finish reason in candidates
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                # Safety Ratings Check
                if candidate.safety_ratings:
                    for rating in candidate.safety_ratings:
                        # Original code used rating.blocked which doesn't exist
                        # Check if probability is high or above medium based on API docs
                        # Example check: Adjust threshold as needed (HIGH is strictest)
                        if rating.probability.name in ["HIGH", "MEDIUM"]: # Check MEDIUM or HIGH probability blocks
                             logger.warning(f"Content potentially blocked by safety setting: {rating.category.name} (Probability: {rating.probability.name})")
                             # Decide if this constitutes an error return
                             # return f"ERROR: Blocked by Safety ({rating.category.name})" # Stricter: block on MEDIUM/HIGH

                # Finish Reason Check
                finish_reason = getattr(candidate, 'finish_reason', 'UNKNOWN')
                # Convert finish_reason enum to string if necessary
                finish_reason_str = finish_reason.name if hasattr(finish_reason, 'name') else str(finish_reason)

                if finish_reason_str not in ["STOP", "MAX_TOKENS"]:
                    logger.warning(f"API response finished unexpectedly. Reason: {finish_reason_str}.")
                    # Consider SAFETY/RECITATION/OTHER as definite errors
                    if finish_reason_str in ["SAFETY", "RECITATION", "OTHER"]:
                         return f"ERROR: API Response Issue ({finish_reason_str})"
                    # Handle other reasons (e.g., UNKNOWN, UNSPECIFIED) as potential issues, maybe retry?
                    # For now, treat them as warnings but check content

                # Content Check
                if hasattr(candidate, 'content') and candidate.content.parts:
                     if hasattr(candidate.content.parts[0], 'text') and candidate.content.parts[0].text:
                        text_response = candidate.content.parts[0].text
                        # Remove markdown code fences (json or plain)
                        text_response = re.sub(r'^```(json)?\s*|\s*```$', '', text_response).strip()
                        logger.debug("API call successful, received text response.")
                        return text_response
                     else:
                        logger.warning("API candidate content part exists but has no text content.")
                        return "ERROR: API Response Empty (in candidate part)"
                else:
                    # If no content but finish reason was STOP/MAX_TOKENS, it's likely an empty valid response
                    if finish_reason_str in ["STOP", "MAX_TOKENS"]:
                        logger.warning(f"API candidate has no content, but finish reason was {finish_reason_str}. Returning empty.")
                        return "" # Return empty string instead of error for this case
                    else:
                        logger.warning(f"API candidate exists but has no content or parts. Finish Reason: {finish_reason_str}")
                        return "ERROR: API Candidate No Content"

            # Fallback check (Older structure, less likely with current SDK but safe)
            elif hasattr(response, 'parts') and response.parts:
                 if hasattr(response.parts[0], 'text') and response.parts[0].text:
                    text_response = response.parts[0].text
                    text_response = re.sub(r'^```(json)?\s*|\s*```$', '', text_response).strip()
                    logger.debug("API call successful (fallback check), received text response.")
                    return text_response
                 else:
                    logger.warning("API response part exists but has no text content (fallback check).")
                    return "ERROR: API Response Empty (fallback check)"
            else:
                # Handle potentially empty successful responses (no parts, no candidates, but maybe no error?)
                # Check prompt feedback again
                 if not (response.prompt_feedback and response.prompt_feedback.block_reason):
                     logger.warning(f"API response structure unexpected but no explicit block reason found. Assuming empty/failed response. Response: {response}")
                     return "ERROR: Unexpected or Empty Response Structure"
                 else:
                     # We already handled block reason at the start, but double check
                      return f"ERROR: Blocked by API ({response.prompt_feedback.block_reason})"


        except (GoogleAPIError, Exception) as e:
            retries += 1
            error_type = type(e).__name__
            logger.warning(f"API call failed (Attempt {retries}/{max_retries}): {error_type} - {e}")
            if retries >= max_retries:
                logger.error("Max retries reached. Skipping API call.")
                return f"ERROR: Max Retries Reached ({error_type})"
            logger.info(f"Retrying in {delay} seconds...")
            time.sleep(delay)
    return "ERROR: Max Retries Reached (Loop Exit)"


def load_articles_from_json(filepath):
    """Loads article data from a source JSON file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list):
            logger.error(f"Source JSON file {filepath} does not contain a list.")
            return None
        logger.info(f"Successfully loaded {len(data)} articles from {filepath}")
        return data
    except FileNotFoundError:
        logger.error(f"Source JSON file not found: {filepath}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding source JSON file {filepath}: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred loading {filepath}: {e}")
        return None

def format_publication_date_iso(date_str):
    """Attempts to parse date and format as ISO 8601 (YYYY-MM-DDTHH:MM:SZ). Returns None if invalid."""
    if not date_str:
        return None
    try:
        # Handle potential MM/DD/YYYY format specifically before general parsing
        if re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
             dt = datetime.strptime(date_str, '%m/%d/%Y')
        else:
            dt = dateutil_parse(date_str)

        # Ensure UTC timezone if none is present
        if dt.tzinfo is None:
             dt = dt.replace(tzinfo=timezone.utc)

        # Format to ISO 8601 with timezone offset Z for UTC
        return dt.strftime('%Y-%m-%dT%H:%M:%SZ')

    except (ValueError, TypeError, OverflowError) as e:
        logger.warning(f"Could not parse date '{date_str}' to ISO 8601: {e}. Trying YYYY-MM-DD extraction.")
        # Regex to find YYYY-MM-DD pattern
        match = re.search(r"(\d{4}-\d{2}-\d{2})", str(date_str))
        if match:
             try:
                 # Convert extracted date to datetime and format as ISO with T00:00:00Z
                 dt_date_only = datetime.strptime(match.group(0), "%Y-%m-%d")
                 dt_utc = dt_date_only.replace(tzinfo=timezone.utc)
                 return dt_utc.strftime('%Y-%m-%dT00:00:00Z') # Use explicit format for consistency
             except Exception as inner_e:
                 logger.warning(f"Could not create ISO string from extracted date {match.group(0)}: {inner_e}")
                 return None # Fail if extraction doesn't lead to valid ISO
        logger.error(f"Completely unable to parse date: '{date_str}' for ISO format. Returning None.")
        return None
    except Exception as e:
         logger.error(f"Unexpected error parsing date '{date_str}' for ISO: {e}. Returning None.")
         return None


def format_publication_date_for_ref(date_str):
    """Attempts to parse date into 'YYYY-MM-DD' or returns 'Inconnue'. For reference line."""
    if not date_str:
        return "Inconnue"
    try:
        # Use the ISO formatter first, then extract the date part
        iso_date = format_publication_date_iso(date_str)
        if iso_date:
            return iso_date[:10] # Extract YYYY-MM-DD part
        else:
             # Fallback: try MM/DD/YYYY specifically
             if re.match(r'\d{1,2}/\d{1,2}/\d{4}', date_str):
                 dt = datetime.strptime(date_str, '%m/%d/%Y')
                 return dt.strftime("%Y-%m-%d")
             # Fallback: try general parsing if ISO failed
             dt = dateutil_parse(date_str)
             return dt.strftime("%Y-%m-%d")
    except (ValueError, TypeError, OverflowError, AttributeError) as e: # Added AttributeError
        logger.warning(f"Could not parse date '{date_str}' for reference line: {e}. Trying regex.")
        match = re.search(r"(\d{4}-\d{2}-\d{2})", str(date_str))
        if match:
            return match.group(0)
        logger.warning(f"Could not format date '{date_str}' for reference. Returning 'Inconnue'.")
        return "Inconnue"
    except Exception as e:
        logger.warning(f"Unexpected error parsing date '{date_str}' for reference: {e}. Returning 'Inconnue'.")
        return "Inconnue"


def generate_summary_json_with_translation(original_title, original_abstract):
    """
    Generates structured summary components (JSON) from the English abstract
    AND translates the provided English title.
    """
    prompt = f"""
    Rôle: Tu es un expert en rédaction médicale bilingue (anglais/français).

    Tâche:
    1. Traduis le TITRE ANGLAIS fourni ci-dessous en français.
    2. Lis l'ABSTRACT MÉDICAL suivant (en anglais). Extrais les informations clés (contexte, méthodologie, résultats, impact clinique) et formule-les en français.
    3. Retourne TOUTES ces informations (titre traduit ET composants de l'abstract) sous forme d'un objet JSON **valide**.

    Format JSON Requis (utilise exactement ces clés):
    {{
      "titre_traduit": "La traduction française concise et informative du titre anglais fourni.",
      "contexte": "Brève description du contexte et de la problématique abordée (en français, basée sur l'abstract).",
      "methodologie": "Description succincte de la méthodologie utilisée (étude, population, intervention, etc. en français, basée sur l'abstract).",
      "resultats": "Principaux résultats quantitatifs ou qualitatifs rapportés (en français, basée sur l'abstract).",
      "impact_clinique": "Synthèse de l'impact ou de la pertinence clinique des résultats (en français, basée sur l'abstract)."
    }}

    Instructions:
    1.  **Sortie JSON Uniquement:** Ta réponse doit être UNIQUEMENT un objet JSON valide, sans texte explicatif avant ou après. Ne pas utiliser de blocs de code markdown (```json ... ```).
    2.  **Langue du Contenu:** Toutes les valeurs textuelles dans le JSON doivent être en **français**.
    3.  **Contenu Abstract:** Base-toi EXCLUSIVEMENT sur l'abstract fourni pour les champs `contexte`, `methodologie`, `resultats`, `impact_clinique`. N'ajoute aucune information externe. Sois concis et factuel.
    4.  **Contenu Titre:** Base-toi EXCLUSIVEMENT sur le titre anglais fourni pour le champ `titre_traduit`.
    5.  **Champs Abstract:** Si une information (contexte, etc.) n'est absolument pas présente dans l'abstract, utilise la valeur "Non précisé dans l'abstract".
    6.  **Abréviations:** Évite les abréviations non communes dans les valeurs JSON, ou explique-les lors de la première utilisation (ex: "accident vasculaire cérébral (AVC)").

    TITRE ANGLAIS Fourni:
    {original_title}

    Abstract original (en anglais):
    {original_abstract}

    Réponse JSON attendue (uniquement le JSON):
    """
    logger.debug("Sending JSON generation request (with title translation) to API.")
    json_string = safe_api_call(prompt)

    if not json_string or json_string.startswith("ERROR:"):
        logger.error(f"Failed to get valid response from API for title/abstract. Response: {json_string}")
        return None

    try:
        summary_data = json.loads(json_string)
        required_keys = {"titre_traduit", "contexte", "methodologie", "resultats", "impact_clinique"}
        missing_keys = required_keys - summary_data.keys()
        if missing_keys:
            logger.error(f"API response is valid JSON but missing required keys: {missing_keys}. Found: {list(summary_data.keys())}")
            for key in missing_keys:
                summary_data[key] = f"Erreur: Clé '{key}' manquante dans la réponse de l'IA"
            # Decide whether to return partially filled data or None
            # return None # Option: fail strictly if keys are missing
        logger.debug("JSON parsing and basic validation successful.")
        return summary_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from API: {e}")
        logger.error(f"Invalid JSON string received:\n{'-'*20}\n{json_string}\n{'-'*20}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error processing API JSON response: {e}")
        return None

def extract_fallback_article_id(url_or_link):
    """
    Extracts common IDs (PMID, PMC) or creates a hash from URL/link.
    Used when the primary '/(\d+)$' pattern on 'url' fails.
    """
    if not url_or_link:
        # Create hash based on time if no URL/link is provided at all
        fallback_id = f"no_url_{hashlib.md5(str(time.time()).encode()).hexdigest()[:10]}"
        logger.warning(f"No URL/Link for fallback ID, using time-based fallback ID: {fallback_id}")
        return fallback_id

    # Try to extract PubMed ID (PMID) specifically (from link mostly)
    match_pubmed = re.search(r'pubmed/(\d+)', url_or_link, re.IGNORECASE)
    if match_pubmed:
        logger.debug(f"Extracted fallback PMID: {match_pubmed.group(1)} from {url_or_link}")
        return match_pubmed.group(1)
    match_pubmed_term = re.search(r'term=(\d+)', url_or_link, re.IGNORECASE)
    if match_pubmed_term:
        logger.debug(f"Extracted fallback PMID (term=): {match_pubmed_term.group(1)} from {url_or_link}")
        return match_pubmed_term.group(1)

    # Try to extract PMC ID specifically
    match_pmc = re.search(r'articles/PMC(\d+)', url_or_link, re.IGNORECASE)
    if match_pmc:
        pmc_id = f"PMC{match_pmc.group(1)}" # Keep the PMC prefix
        logger.debug(f"Extracted fallback PMC ID: {pmc_id} from {url_or_link}")
        return pmc_id

    # Try to extract DOI (use hash for filename safety)
    match_doi = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', url_or_link, re.IGNORECASE)
    if match_doi:
        doi_str = match_doi.group(1)
        # Further sanitize DOI for use as part of filename or ID if needed elsewhere
        # This hash approach is safe for filename but keeps the ID derived from DOI
        doi_hash = hashlib.md5(doi_str.encode()).hexdigest()[:10]
        logger.debug(f"Using DOI hash for fallback ID: doi_{doi_hash} (from DOI: {doi_str}) in {url_or_link}")
        return f"doi_{doi_hash}"


    # Try the general numeric ID at the end pattern AGAIN, just in case it was missed
    # (e.g., if the link field also ended in numbers but wasn't PMID/PMC)
    match_numeric_end = re.search(r'/(\d+)$', url_or_link.strip('/'))
    if match_numeric_end:
        logger.debug(f"Extracted fallback numeric ID (end pattern): {match_numeric_end.group(1)} from {url_or_link}")
        return match_numeric_end.group(1)


    # If NO specific pattern matches, use hash of the input string
    url_hash = hashlib.md5(url_or_link.encode()).hexdigest()[:10]
    logger.warning(f"Could not extract standard ID from fallback source: {url_or_link}. Using hash: url_{url_hash}")
    return f"url_{url_hash}"


# --- MODIFIED: process_article now takes date_specific_output_dir ---
def process_article(article_data, date_specific_output_dir):
    """
    Processes a single article: gets title, generates summary/translation,
    formats content, includes categories, and saves as an individual JSON file
    within the provided date-specific directory.
    Filename is based on numeric ID from 'url' if possible, otherwise falls back.
    Returns True on success, False on failure/skip.
    """
    article_url = article_data.get("url")
    pubmed_link = article_data.get("link")

    article_id = None
    id_source_log = "N/A"

    # --- Prioritize ID extraction from 'url' ---
    if article_url:
        match_url_id = re.search(r'/(\d+)$', article_url.strip('/'))
        if match_url_id:
            article_id = match_url_id.group(1)
            id_source_log = f"URL ending pattern ({article_url})"
            logger.info(f"Using specific ID from URL: {article_id}")

    # --- Fallback ID Extraction ---
    if not article_id:
        logger.info("Specific URL ID pattern not found or URL missing. Trying fallback ID extraction...")
        fallback_source = pubmed_link or article_url
        if fallback_source:
            article_id = extract_fallback_article_id(fallback_source)
            id_source_log = f"Fallback logic ({fallback_source})"
        else:
            article_id = f"missing_id_{hashlib.md5(str(time.time()).encode()).hexdigest()[:10]}"
            id_source_log = "Time-based hash (no URL/link)"
            logger.warning("Both 'link' and 'url' missing in input data. Generating time-based ID.")

    logger.info(f"--- Processing Article ID: {article_id} (Source: {id_source_log}) ---")

    # --- Construct the full output path ---
    output_filename = f"{article_id}.json"
    # --- MODIFIED: Use the passed-in date_specific_output_dir ---
    output_path = os.path.join(date_specific_output_dir, output_filename)

    # Check for existing file
    if os.path.exists(output_path):
        logger.info(f"Output file {output_path} already exists. Skipping article ID {article_id}.")
        return False

    # --- Get Required Input Data ---
    original_title = article_data.get("title")
    original_abstract = article_data.get("abstract")
    journal = article_data.get("journal", "Inconnu")
    pub_date_raw = article_data.get("published_at")
    categories = article_data.get("categories", [])

    # --- Validate Input Data ---
    if not original_title:
        logger.warning(f"Article {article_id}: Original title missing in input JSON. Skipping.")
        return False
    if not original_abstract or original_abstract.strip().upper() == "N/A":
        logger.warning(f"Article {article_id}: Abstract missing or N/A in input JSON. Skipping.")
        return False
    if not isinstance(categories, list):
        logger.warning(f"Article {article_id}: 'categories' field is not a list. Found type {type(categories)}. Treating as empty.")
        categories = []

    logger.info(f"  Original Title: '{original_title[:100]}...'")
    logger.info(f"  Generating structured summary and translating title...")

    # --- Generate Summary and Translated Title ---
    summary_components = generate_summary_json_with_translation(original_title, original_abstract)

    if not summary_components:
        logger.error(f"Article {article_id}: Failed to generate structured summary/translation. Skipping.")
        return False

    # --- Extract Data from AI Response ---
    translated_title = summary_components.get('titre_traduit', f"Erreur: Titre non traduit ({article_id})")
    if translated_title.startswith("Erreur:"):
         logger.warning(f"Article {article_id}: Title translation missing or failed in AI response.")

    contexte = summary_components.get('contexte', 'Non précisé dans l\'abstract')
    methodologie = summary_components.get('methodologie', 'Non précisé dans l\'abstract')
    resultats = summary_components.get('resultats', 'Non précisé dans l\'abstract')
    impact_clinique = summary_components.get('impact_clinique', 'Non précisé dans l\'abstract')

    # --- Format Dates ---
    published_at_iso = format_publication_date_iso(pub_date_raw)
    pub_date_str_for_ref = format_publication_date_for_ref(pub_date_raw)

    logger.info(f"  Translated Title: '{translated_title[:100]}...'")
    logger.info(f"  Publication date (ISO for DB): {published_at_iso}")
    logger.info(f"  Publication date (for ref line): {pub_date_str_for_ref}")
    logger.info(f"  Categories: {categories}")

    # --- Construct the Output JSON ---
    try:
        content_sections = [
            f"## 📌 Contexte & Problématique\n{contexte}",
            f"## 🧪 Méthodologie\n{methodologie}",
            f"## 📊 Résultats Clés\n{resultats}",
            f"## 🩺 Impact Clinique\n{impact_clinique}",
            f"## Revue\n{journal if journal else 'Inconnu'}",
            f"## 📖 Référence\n{pub_date_str_for_ref.split('-')[0] if pub_date_str_for_ref != 'Inconnue' else 'Année inconnue'}"
        ]
        main_content = "\n\n".join(content_sections)

        output_data = {
            "title": translated_title,
            "content": main_content,
            "published_at": published_at_iso if published_at_iso else None,
            "link": pubmed_link if pubmed_link else article_url if article_url else None,
            "journal": journal if journal else "Inconnu",
            "grade": DEFAULT_GRADE,
            "categories": categories,
            "original_source_url": article_url if article_url and article_url != pubmed_link else None,
        }
        # Clean up None values for optional fields
        if output_data.get("original_source_url") is None:
            output_data.pop("original_source_url", None)
        if output_data.get("link") is None:
             output_data.pop("link", None)
        if output_data.get("published_at") is None:
             output_data.pop("published_at", None)


        # --- Save the Output JSON ---
        # --- MODIFIED: Ensure directory exists (robustness, though should be created in main) ---
        os.makedirs(date_specific_output_dir, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"  Summary saved: {output_path}")
        return True

    except KeyError as e:
        logger.error(f"Article {article_id}: Missing key {e} when constructing output JSON. Check AI response structure. Skipping.")
        return False
    except IOError as e:
        logger.error(f"Article {article_id}: Error saving file {output_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Article {article_id}: Unexpected error constructing or saving output: {e}", exc_info=True)
        return False


# --- Main Execution ---
def main():
    parser = argparse.ArgumentParser(
        description="Generates individual JSON summaries (incl. title translation and categories) for articles from a source JSON file using Google AI."
    )
    parser.add_argument(
        "json_file", help="Path to the source JSON file containing article data (must include 'title', 'abstract', optionally 'categories', 'url', 'link')."
    )
    parser.add_argument(
        "--output-dir",
        default=OUTPUT_DIR,
        # --- MODIFIED: Updated help text ---
        help=f"Base directory to save date-specific summary folders (default: {OUTPUT_DIR})",
    )
    args = parser.parse_args()

    # --- MODIFIED: Create date-specific output directory ---
    today_date_str = date.today().strftime(TIMESTAMP_FORMAT)
    date_specific_output_dir = os.path.join(args.output_dir, today_date_str)

    try:
        os.makedirs(date_specific_output_dir, exist_ok=True)
        logger.info(f"Ensured date-specific output directory exists: {date_specific_output_dir}")
    except OSError as e:
        logger.error(f"Could not create output directory {date_specific_output_dir}: {e}")
        return

    articles = load_articles_from_json(args.json_file)
    if not articles:
        return

    total_articles = len(articles)
    logger.info(f"Starting processing for {total_articles} articles...")
    logger.info(f"Input JSON: {args.json_file}")
    # --- MODIFIED: Log the specific output directory ---
    logger.info(f"Output JSON files will be saved to: {date_specific_output_dir}")

    processed_count = 0
    success_count = 0
    skipped_count = 0
    start_time = time.time()

    for i, article_data in enumerate(articles):
        logger.debug(f"Attempting article {i+1}/{total_articles}")
        processed_count += 1

        try:
            # --- MODIFIED: Pass the date_specific_output_dir ---
            success = process_article(article_data, date_specific_output_dir)
            if success:
                success_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            article_url_log = article_data.get("url", "URL_MISSING")
            article_link_log = article_data.get("link", "LINK_MISSING")
            logger.error(f"CRITICAL UNEXPECTED ERROR in main loop for article entry {i+1} (URL: {article_url_log}, Link: {article_link_log}): {e}", exc_info=True)
            skipped_count += 1
        finally:
            if processed_count % 10 == 0 or processed_count == total_articles:
                elapsed_time = time.time() - start_time
                logger.info(f"Progress: {processed_count}/{total_articles} articles attempted ({success_count} successful, {skipped_count} skipped/failed) in {elapsed_time:.2f} seconds.")
            # time.sleep(0.5) # Optional delay


    end_time = time.time()
    logger.info(f"--- Processing Finished ---")
    logger.info(f"Total articles in source file: {total_articles}")
    logger.info(f"Total articles attempted: {processed_count}")
    logger.info(f"Successfully processed and saved: {success_count}")
    logger.info(f"Skipped (already exist, errors, missing data): {skipped_count}")
    logger.info(f"Total time: {end_time - start_time:.2f} seconds")
    # --- MODIFIED: Log the specific output directory ---
    logger.info(f"Individual JSON summaries saved in: {date_specific_output_dir}")

if __name__ == "__main__":
    main()