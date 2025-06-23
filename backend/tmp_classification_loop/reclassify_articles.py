import asyncio
import os
import json
import time
import logging
from typing import List, Dict, Set, Tuple, Optional, Any
from pathlib import Path

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv

try:
    from supabase import create_client, Client, PostgrestAPIError
except ImportError:
    print("ERROR: 'supabase' library not found. Please install it: pip install supabase google-generativeai python-dotenv")
    exit(1)

load_dotenv()

GOOGLE_API_KEYS_LIST = [
    "AIzaSyC0ZL-JSKKpTmw7jaGRWSTvKup6L6cn-GE",
    "AIzaSyDFvmws1GE52VBrKDYsgqvrrswmruuNVB4",
    "AIzaSyDeK-M3Ns8kG2r2j_e92xLqhQYNEWWN8Qg",
    "AIzaSyAITsfE616q7ISHQ9GunsV2oZq9IItcfXs",
    "AIzaSyBcyOuOQHOpJ82d_3ub6eYeEuX0_gDL0hk",
    "AIzaSyD8k8gH-zL8hXGbt-_zd7zMOHAupc4d4wk",
]
current_google_api_key_index = 0

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

GEMINI_MODEL = 'gemini-2.5-flash-preview-04-17'

MAX_GEMINI_RETRIES = 6
RETRY_DELAY_SECONDS = 10
GEMINI_CONCURRENCY_LIMIT = 2

PROMPT_FILENAME = "reclassification_prompt.txt"
ARBITRATION_PROMPT_FILENAME = "arbitration_prompt.txt"

PROCESS_CONCURRENCY = 1
BATCH_SIZE = 1
LOOP_DELAY_SECONDS = 1
MAX_CONTENT_LENGTH = 1500000
RESULT_DIR = Path("result_arbitration")
DELAY_BETWEEN_CALLS = 1.0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] - %(message)s')
logger = logging.getLogger(__name__)

disciplines_map: Dict[str, int] = {}
sub_disciplines_map: Dict[int, Dict[str, int]] = {}
prompt_template_cache: Optional[str] = None
arbitration_prompt_template_cache: Optional[str] = None
master_classifications_list_str_cache: Optional[str] = None

def load_api_key():
    global current_google_api_key_index
    if not GOOGLE_API_KEYS_LIST:
        raise ValueError("GOOGLE_API_KEYS_LIST is empty. Please provide API keys in the script.")
    
    selected_key = GOOGLE_API_KEYS_LIST[current_google_api_key_index]
    logger.debug(f"Using Google API Key from list (index: {current_google_api_key_index})")
    current_google_api_key_index = (current_google_api_key_index + 1) % len(GOOGLE_API_KEYS_LIST)
    return selected_key

def create_supabase_client() -> Optional[Client]:
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.error("SUPABASE_URL and SUPABASE_KEY must be set.")
        return None
    try:
        client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Successfully connected to Supabase.")
        return client
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {e}", exc_info=True)
        return None

def load_prompt_template(filepath=PROMPT_FILENAME, is_arbitration=False) -> Optional[str]:
    global prompt_template_cache, arbitration_prompt_template_cache
    cache_to_use = arbitration_prompt_template_cache if is_arbitration else prompt_template_cache
    if cache_to_use:
        return cache_to_use
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        if not content:
             logger.error(f"Prompt template file '{filepath}' is empty.")
             return None
        if is_arbitration:
            arbitration_prompt_template_cache = content
        else:
            prompt_template_cache = content
        logger.info(f"Successfully loaded prompt template from {filepath}")
        return content
    except FileNotFoundError:
        logger.error(f"Prompt template file not found at {filepath}")
        return None
    except IOError as e:
         logger.error(f"Error reading prompt template file {filepath}: {e}")
         return None

async def fetch_master_discipline_data(supabase: Client):
    global disciplines_map, sub_disciplines_map, master_classifications_list_str_cache
    try:
        logger.info("Fetching master discipline data...")
        disc_response = await asyncio.to_thread(
            supabase.table('disciplines').select('id, name').execute
        )
        if disc_response.data:
            disciplines_map = {
                d['name'].strip(): d['id']
                for d in disc_response.data if d.get('name') and isinstance(d.get('name'), str)
            }
        else: 
            logger.error("Failed to fetch disciplines or no disciplines found.")
            return False

        sub_disc_response = await asyncio.to_thread(
             supabase.table('sub_disciplines').select('id, name, discipline_id').execute
        )
        if sub_disc_response.data:
            sub_disciplines_map = {}
            for sd in sub_disc_response.data:
                disc_id = sd['discipline_id']
                sub_name_raw = sd.get('name')
                if not sub_name_raw or not isinstance(sub_name_raw, str): continue
                sub_name = sub_name_raw.strip()
                if disc_id not in sub_disciplines_map:
                    sub_disciplines_map[disc_id] = {}
                sub_disciplines_map[disc_id][sub_name] = sd['id']
        else: 
            logger.warning("No sub-disciplines found or failed to fetch.")

        master_list_for_prompt: Dict[str, List[str]] = {}
        for disc_name, disc_id in disciplines_map.items():
            master_list_for_prompt[disc_name] = []
            if disc_id in sub_disciplines_map:
                master_list_for_prompt[disc_name] = sorted(list(sub_disciplines_map[disc_id].keys()))
        master_classifications_list_str_cache = json.dumps(master_list_for_prompt, indent=2, ensure_ascii=False)
        logger.info("Master discipline data loaded successfully.")
        return True
    except Exception as e: 
        logger.error(f"Error fetching master discipline data: {e}", exc_info=True)
        return False


def get_discipline_id(name: str) -> Optional[int]:
    return disciplines_map.get(name)

def get_sub_discipline_id(discipline_name: str, sub_discipline_name: str) -> Optional[int]:
    discipline_id = get_discipline_id(discipline_name)
    if discipline_id and discipline_id in sub_disciplines_map:
        return sub_disciplines_map[discipline_id].get(sub_discipline_name)
    return None

def format_reclassification_prompt_content(
    title: str, content: str, current_classifications: Dict[str, List[str]]
) -> Optional[str]:
    global master_classifications_list_str_cache
    template = load_prompt_template()
    if not template or not master_classifications_list_str_cache: 
        logger.error("Prompt template or master classifications list not loaded.")
        return None
    current_class_str = json.dumps(current_classifications, indent=2, ensure_ascii=False) or "No current classifications found."
    truncated_content = content[:MAX_CONTENT_LENGTH] + ("\n[... CONTENT TRUNCATED ...]" if len(content) > MAX_CONTENT_LENGTH else "")
    try:
        prompt = template.replace("{master_classifications_list_str}", master_classifications_list_str_cache)
        prompt = prompt.replace("{title}", title)
        prompt = prompt.replace("{truncated_content}", truncated_content)
        prompt = prompt.replace("{current_class_str}", current_class_str)
        return prompt
    except Exception as e:
        logger.error(f"Error formatting reclassification prompt: {e}", exc_info=True)
        return None

def format_arbitration_prompt_content(
    title: str, content: str, classification_1: Dict[str, Any], classification_2: Dict[str, Any]
) -> Optional[str]:
    global master_classifications_list_str_cache
    template = load_prompt_template(filepath=ARBITRATION_PROMPT_FILENAME, is_arbitration=True)
    if not template or not master_classifications_list_str_cache: 
        logger.error("Arbitration prompt template or master classifications list not loaded.")
        return None
    truncated_content = content[:MAX_CONTENT_LENGTH] + ("\n[... CONTENT TRUNCATED ...]" if len(content) > MAX_CONTENT_LENGTH else "")
    class_1_str = json.dumps(classification_1.get("corrected_classifications", {}), indent=2, ensure_ascii=False)
    class_2_str = json.dumps(classification_2.get("corrected_classifications", {}), indent=2, ensure_ascii=False)
    try:
        prompt = template.replace("{master_classifications_list_str}", master_classifications_list_str_cache)
        prompt = prompt.replace("{title}", title)
        prompt = prompt.replace("{truncated_content}", truncated_content)
        prompt = prompt.replace("{classification_1_str}", class_1_str)
        prompt = prompt.replace("{classification_2_str}", class_2_str)
        return prompt
    except Exception as e:
        logger.error(f"Error formatting arbitration prompt: {e}", exc_info=True)
        return None

async def call_gemini_api(prompt: str, semaphore: asyncio.Semaphore) -> Optional[Dict[str, Any]]:
    try:
        api_key = load_api_key()
    except ValueError as e:
        logger.error(f"Failed to load API key: {e}")
        return None
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        GEMINI_MODEL,
        generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
    )
    attempts = 0
    async with semaphore:
        while attempts < MAX_GEMINI_RETRIES:
            attempts += 1
            try:
                logger.debug(f"Calling Gemini API (Attempt {attempts})...")
                response = await asyncio.to_thread(model.generate_content, prompt)
                
                if not response.parts:
                    logger.warning(f"Gemini call attempt {attempts} returned no parts.")
                    if attempts < MAX_GEMINI_RETRIES: await asyncio.sleep(RETRY_DELAY_SECONDS); continue
                    return None
                
                raw_json_text = response.text.strip()
                if not raw_json_text:
                    logger.warning(f"Gemini call attempt {attempts} returned empty text.")
                    if attempts < MAX_GEMINI_RETRIES: await asyncio.sleep(RETRY_DELAY_SECONDS); continue
                    return None
                
                try:
                    result_json = json.loads(raw_json_text)
                    logger.info(f"Gemini call attempt {attempts} successful.")
                    if "corrected_classifications" not in result_json or not isinstance(result_json["corrected_classifications"], dict):
                        logger.error(f"Gemini JSON invalid structure (missing corrected_classifications dict). Attempt {attempts}. Response: {raw_json_text[:500]}")
                        return None
                    return result_json
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode Gemini JSON response on attempt {attempts}: {e}")
                    logger.debug(f"Raw text: {raw_json_text[:500]}...")
                    return None
            except google_exceptions.ResourceExhausted as e:
                logger.warning(f"Gemini API rate limit hit (429) on attempt {attempts}: {e}")
                if attempts < MAX_GEMINI_RETRIES:
                    delay = RETRY_DELAY_SECONDS * (2**(attempts-1))
                    logger.info(f"Retrying Gemini call in {delay} seconds...")
                    await asyncio.sleep(delay)
                    continue
                else:
                    logger.error("Max retries reached for Gemini rate limit.")
                    return None
            except google_exceptions.GoogleAPIError as e:
                logger.error(f"Google API error during Gemini call attempt {attempts}: {e}", exc_info=True)
                if attempts < MAX_GEMINI_RETRIES:
                    delay = RETRY_DELAY_SECONDS * (2**(attempts-1))
                    logger.info(f"Retrying Gemini call (GoogleAPIError) in {delay} seconds...")
                    await asyncio.sleep(delay)
                    continue
                return None
            except Exception as e:
                logger.error(f"Unexpected error during Gemini API call attempt {attempts}: {e}", exc_info=True)
                return None
    logger.error("Exited Gemini retry loop without success.")
    return None

async def select_articles_for_reclassification(supabase: Client, limit: int) -> List[int]:
    article_ids = []
    try:
        select_response = await asyncio.to_thread(
            supabase.table('articles').select('id')
            .in_('reclassification_status', ['pending', 'error'])
            .order('created_at', desc=False).limit(limit)
            .execute
        )
        if select_response.data:
            article_ids = [a['id'] for a in select_response.data]
            if article_ids:
                update_response = await asyncio.to_thread(
                    supabase.table('articles').update({'reclassification_status': 'processing'})
                    .in_('id', article_ids).execute
                )
                if getattr(update_response, 'error', None):
                     logger.error(f"Failed to mark articles {article_ids} as 'processing': {update_response.error}")
                     return []
    except PostgrestAPIError as e:
        logger.error(f"Supabase API Error selecting/updating articles for processing: {e}", exc_info=True)
        return []
    except Exception as e:
        logger.error(f"Error selecting/updating articles for processing: {e}", exc_info=True)
        return []
    return article_ids

async def fetch_article_details(supabase: Client, article_id: int) -> Optional[Dict[str, Any]]:
    details = {'id': article_id, 'title': None, 'content': None, 'current_classifications': {}}
    try:
        article_resp = await asyncio.to_thread(
            supabase.table('articles').select('title, content').eq('id', article_id).maybe_single().execute
        )
        if not article_resp.data or not article_resp.data.get('title') or not article_resp.data.get('content'):
            logger.error(f"Article ID {article_id} missing title or content. Response: {article_resp.data}")
            await update_article_status(supabase, article_id, 'error', "Missing title/content")
            return None
        details['title'], details['content'] = article_resp.data['title'], article_resp.data['content']

        disc_links_resp = await asyncio.to_thread(
            supabase.table('article_disciplines').select('discipline_id, disciplines(name)').eq('article_id', article_id).execute
        )
        current_disciplines: Dict[int, str] = {item['discipline_id']: item['disciplines']['name'] for item in disc_links_resp.data if item.get('disciplines')} if disc_links_resp.data else {}

        sub_disc_links_resp = await asyncio.to_thread(
            supabase.table('article_sub_disciplines').select('sub_discipline_id, sub_disciplines(name, discipline_id)').eq('article_id', article_id).execute
        )
        current_classifications: Dict[str, List[str]] = {name: [] for name in current_disciplines.values()}
        if sub_disc_links_resp.data:
            for item in sub_disc_links_resp.data:
                if not item.get('sub_disciplines'): continue
                parent_discipline_id, sub_discipline_name = item['sub_disciplines']['discipline_id'], item['sub_disciplines']['name']
                parent_discipline_name = current_disciplines.get(parent_discipline_id)
                if parent_discipline_name:
                    if parent_discipline_name not in current_classifications: current_classifications[parent_discipline_name] = []
                    current_classifications[parent_discipline_name].append(sub_discipline_name)
                else:
                    parent_name_from_map = next((name for name, id_ in disciplines_map.items() if id_ == parent_discipline_id), None)
                    if parent_name_from_map:
                        logger.warning(f"Article {article_id}: Sub-discipline '{sub_discipline_name}' linked to parent discipline ID {parent_discipline_id} ('{parent_name_from_map}') which was not directly linked to the article. Adding.")
                        if parent_name_from_map not in current_classifications: current_classifications[parent_name_from_map] = []
                        current_classifications[parent_name_from_map].append(sub_discipline_name)
        details['current_classifications'] = current_classifications
        return details
    except PostgrestAPIError as e:
        logger.error(f"Supabase API Error fetching article details for {article_id}: {e}", exc_info=True)
        await update_article_status(supabase, article_id, 'error', f"DB error fetching details: {e.code or e.message}")
        return None
    except Exception as e:
        logger.error(f"Error fetching article details for {article_id}: {e}", exc_info=True)
        await update_article_status(supabase, article_id, 'error', "Generic error fetching details")
        return None

async def update_article_classifications(supabase: Client, article_id: int, disciplines_to_add: Set[int], disciplines_to_delete: Set[int], sub_disciplines_to_add: Set[int], sub_disciplines_to_delete: Set[int]):
    try:
        if disciplines_to_delete: 
            logger.debug(f"Article {article_id}: Deleting discipline IDs: {disciplines_to_delete}")
            await asyncio.to_thread(supabase.table('article_disciplines').delete().eq('article_id', article_id).in_('discipline_id', list(disciplines_to_delete)).execute)
        if sub_disciplines_to_delete: 
            logger.debug(f"Article {article_id}: Deleting sub-discipline IDs: {sub_disciplines_to_delete}")
            await asyncio.to_thread(supabase.table('article_sub_disciplines').delete().eq('article_id', article_id).in_('sub_discipline_id', list(sub_disciplines_to_delete)).execute)
        
        if disciplines_to_add: 
            logger.debug(f"Article {article_id}: Adding discipline IDs: {disciplines_to_add}")
            await asyncio.to_thread(supabase.table('article_disciplines').insert([{'article_id': article_id, 'discipline_id': d_id} for d_id in disciplines_to_add], upsert=True).execute)
        if sub_disciplines_to_add: 
            logger.debug(f"Article {article_id}: Adding sub-discipline IDs: {sub_disciplines_to_add}")
            await asyncio.to_thread(supabase.table('article_sub_disciplines').insert([{'article_id': article_id, 'sub_discipline_id': sd_id} for sd_id in sub_disciplines_to_add], upsert=True).execute)
        
        logger.info(f"Successfully updated classifications for Article ID {article_id}")
        return True
    except PostgrestAPIError as e:
        logger.error(f"DB Error updating classifications for article {article_id}: {e.message} (Code: {e.code}, Details: {e.details})")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating classifications for article {article_id}: {e}", exc_info=True)
        return False

async def update_article_status(supabase: Client, article_id: int, status: str, message: str = ""):
    try:
        log_msg = f"Updating Article ID {article_id} status to '{status}'" + (f" ({message})" if message else "")
        logger.info(log_msg)
        update_payload = {'reclassification_status': status}
        if message: # Only include the message if it's not empty, can be a separate log field later if needed.
             pass # Not adding message to db payload unless a specific field exists and is requested.

        await asyncio.to_thread(
            supabase.table('articles').update(update_payload)
            .eq('id', article_id).execute
        )
    except PostgrestAPIError as e:
        logger.error(f"Supabase API Error: Failed to update status for article {article_id} to '{status}': {e.message}", exc_info=True)
    except Exception as e:
        logger.error(f"Failed to update status for article {article_id} to '{status}': {e}", exc_info=True)

def save_diagnostic_info(article_id: int, title: str, content: str, gemini_response: Optional[Dict[str, Any]], call_suffix: str, prompt_used: Optional[str] = None):
    if not gemini_response and not prompt_used:
        logger.warning(f"No Gemini response or prompt to save for Article {article_id}, call '{call_suffix}'")
        return
    try:
        RESULT_DIR.mkdir(parents=True, exist_ok=True)
        output_filepath = RESULT_DIR / f"{article_id}-{call_suffix}.json"
        max_diag_content_len = 50000 
        diag_content = content[:max_diag_content_len] + ("\n[... CONTENT TRUNCATED FOR DIAGNOSTIC FILE ...]" if len(content) > max_diag_content_len else "")

        data_to_save = {
            "article_id": article_id, 
            "title": title, 
            "content_preview": diag_content,
            "prompt_sent_to_gemini": prompt_used,
            "gemini_response": gemini_response
        }
        with open(output_filepath, 'w', encoding='utf-8') as f_out: json.dump(data_to_save, f_out, ensure_ascii=False, indent=2)
        logger.info(f"Saved diagnostic info to {output_filepath}")
    except Exception as e:
        logger.error(f"Failed to save diagnostic JSON for article {article_id}, call '{call_suffix}': {e}")

async def process_article(supabase: Client, article_id: int, gemini_semaphore: asyncio.Semaphore):
    logger.info(f"--- Starting processing for Article ID: {article_id} ---")
    article_details = await fetch_article_details(supabase, article_id)
    if not article_details: 
        logger.error(f"Article {article_id}: Could not fetch details. Aborting processing for this article.")
        return

    title, content, current_classifications_map = article_details['title'], article_details['content'], article_details['current_classifications']
    
    prompt1_text = format_reclassification_prompt_content(title, content, current_classifications_map)
    prompt2_text = prompt1_text 

    if not prompt1_text: 
        await update_article_status(supabase, article_id, 'error', "Failed to format reclassification prompt")
        save_diagnostic_info(article_id, title, content, None, "first_prompt_failed", "PROMPT_FORMATTING_FAILED")
        return

    logger.info(f"Initiating concurrent calls for Article ID: {article_id}")
    task1 = asyncio.create_task(call_gemini_api(prompt1_text, gemini_semaphore))
    await asyncio.sleep(DELAY_BETWEEN_CALLS) 
    task2 = asyncio.create_task(call_gemini_api(prompt2_text, gemini_semaphore))

    results = await asyncio.gather(task1, task2, return_exceptions=True)

    gemini_result_1 = results[0] if not isinstance(results[0], Exception) else None
    if isinstance(results[0], Exception): logger.error(f"Article {article_id}: Exception in Gemini call 1: {results[0]}")
    
    gemini_result_2 = results[1] if not isinstance(results[1], Exception) else None
    if isinstance(results[1], Exception): logger.error(f"Article {article_id}: Exception in Gemini call 2: {results[1]}")

    save_diagnostic_info(article_id, title, content, gemini_result_1, "first", prompt1_text)
    save_diagnostic_info(article_id, title, content, gemini_result_2, "second", prompt2_text)

    if not gemini_result_1 or not gemini_result_2:
        err_msg = ""
        if not gemini_result_1 and not gemini_result_2: err_msg = "Gemini calls 1 and 2 failed"
        elif not gemini_result_1: err_msg = "Gemini call 1 failed"
        else: err_msg = "Gemini call 2 failed"
        logger.error(f"Article {article_id}: {err_msg}")
        await update_article_status(supabase, article_id, 'error', err_msg)
        return

    final_gemini_result = gemini_result_1
    if gemini_result_1.get("corrected_classifications") != gemini_result_2.get("corrected_classifications"):
        logger.info(f"Article {article_id}: Results differ. Calling arbitrator.")
        arbitration_prompt_text = format_arbitration_prompt_content(title, content, gemini_result_1, gemini_result_2)
        if not arbitration_prompt_text:
            await update_article_status(supabase, article_id, 'error', "Failed to format arbitration prompt")
            save_diagnostic_info(article_id, title, content, None, "arbitration_prompt_failed", "ARBITRATION_PROMPT_FORMATTING_FAILED")
            return

        arbitrated_result_task = call_gemini_api(arbitration_prompt_text, gemini_semaphore)
        arbitrated_result = await arbitrated_result_task
        if isinstance(arbitrated_result, Exception):
            logger.error(f"Article {article_id}: Exception in Gemini arbitration call: {arbitrated_result}")
            arbitrated_result = None

        save_diagnostic_info(article_id, title, content, arbitrated_result, "third_arbitrated", arbitration_prompt_text)
        if not arbitrated_result:
            await update_article_status(supabase, article_id, 'error', "Arbitration call failed or returned invalid data")
            return
        final_gemini_result = arbitrated_result
        logger.info(f"Article {article_id}: Arbitration completed.")
    else:
        logger.info(f"Article {article_id}: Results are consistent. Using first result.")


    corrected_classifications_map = final_gemini_result.get("corrected_classifications")
    if not isinstance(corrected_classifications_map, dict):
        logger.error(f"Article {article_id}: Final Gemini result 'corrected_classifications' is not a dictionary. Payload: {final_gemini_result}")
        await update_article_status(supabase, article_id, 'error', "Final result format error (corrected_classifications not dict)")
        return
        
    current_discipline_ids, current_sub_discipline_ids = set(), set()
    for disc_name, sub_disc_names in current_classifications_map.items():
        disc_id = get_discipline_id(disc_name)
        if disc_id:
            current_discipline_ids.add(disc_id)
            for sub_name in sub_disc_names:
                sub_id = get_sub_discipline_id(disc_name, sub_name)
                if sub_id: current_sub_discipline_ids.add(sub_id)

    target_discipline_ids, target_sub_discipline_ids = set(), set()
    for disc_name_raw, sub_disc_names_list in corrected_classifications_map.items():
        if not isinstance(disc_name_raw, str): 
            logger.warning(f"Article {article_id}: Final classification contains non-string discipline name '{disc_name_raw}'. Skipping.")
            continue
        disc_name = disc_name_raw.strip()
        disc_id = get_discipline_id(disc_name)
        if not disc_id:
             logger.warning(f"Article {article_id}: Final classification contains unknown discipline '{disc_name}'. Skipping.")
             continue
        target_discipline_ids.add(disc_id)

        if not isinstance(sub_disc_names_list, list): 
            logger.warning(f"Article {article_id}: Sub-disciplines for '{disc_name}' is not a list: {sub_disc_names_list}. Skipping sub-disciplines for this discipline.")
            continue
        for sub_name_raw in sub_disc_names_list:
            if not isinstance(sub_name_raw, str): 
                logger.warning(f"Article {article_id}: Final classification contains non-string sub-discipline name '{sub_name_raw}' for '{disc_name}'. Skipping.")
                continue
            sub_name = sub_name_raw.strip()
            sub_id = get_sub_discipline_id(disc_name, sub_name)
            if not sub_id:
                 logger.warning(f"Article {article_id}: Final classification contains unknown sub-discipline '{sub_name}' for '{disc_name}'. Skipping.")
                 continue
            target_sub_discipline_ids.add(sub_id)

    disciplines_to_add = target_discipline_ids - current_discipline_ids
    disciplines_to_delete = current_discipline_ids - target_discipline_ids
    sub_disciplines_to_add = target_sub_discipline_ids - current_sub_discipline_ids
    sub_disciplines_to_delete = current_sub_discipline_ids - target_sub_discipline_ids

    if disciplines_to_add or disciplines_to_delete or sub_disciplines_to_add or sub_disciplines_to_delete:
        logger.info(f"Article {article_id}: Changes detected. D_add:{len(disciplines_to_add)}, D_del:{len(disciplines_to_delete)}, SD_add:{len(sub_disciplines_to_add)}, SD_del:{len(sub_disciplines_to_delete)}")
        if await update_article_classifications(supabase, article_id, disciplines_to_add, disciplines_to_delete, sub_disciplines_to_add, sub_disciplines_to_delete):
            await update_article_status(supabase, article_id, 'done', "Classifications updated.")
        else: 
            await update_article_status(supabase, article_id, 'error', "DB update failed for classifications")
    else:
        logger.info(f"Article {article_id}: No classification changes needed after final evaluation. Marking as 'done'.")
        await update_article_status(supabase, article_id, 'done', "No changes needed.")

    logger.info(f"--- Finished processing for Article ID: {article_id} ---")

async def main():
    supabase = create_supabase_client()
    if not supabase: return
    
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    
    if not load_prompt_template() or not load_prompt_template(filepath=ARBITRATION_PROMPT_FILENAME, is_arbitration=True):
        logger.critical("Failed to load prompt template file(s). Cannot proceed.")
        return
    if not await fetch_master_discipline_data(supabase):
        logger.critical("Failed to load master discipline data. Cannot proceed.")
        return

    actual_concurrency_limit = max(3, GEMINI_CONCURRENCY_LIMIT) 
    gemini_semaphore = asyncio.Semaphore(actual_concurrency_limit)
    logger.info(f"Gemini API call semaphore limit set to: {actual_concurrency_limit}")

    logger.info(f"Starting arbitration processing loop. Article Process Concurrency={PROCESS_CONCURRENCY}, Batch Size={BATCH_SIZE}, Loop Delay={LOOP_DELAY_SECONDS}s")
    logger.info(f"Results will be saved in: {RESULT_DIR.resolve()}")
    
    processing_tasks: Set[asyncio.Task] = set()

    try:
        while True:
            completed_tasks = {task for task in processing_tasks if task.done()}
            for task in completed_tasks:
                try:
                    task.result()
                except Exception as e:
                    logger.error(f"A process_article task failed: {e}", exc_info=True)
            processing_tasks -= completed_tasks

            if len(processing_tasks) < PROCESS_CONCURRENCY:
                num_to_fetch = min(BATCH_SIZE, PROCESS_CONCURRENCY - len(processing_tasks))
                if num_to_fetch > 0:
                    logger.debug(f"Checking for up to {num_to_fetch} articles to process...")
                    article_ids_to_process = await select_articles_for_reclassification(supabase, num_to_fetch)
                    
                    if article_ids_to_process:
                        logger.info(f"Processing article ID(s): {article_ids_to_process}")
                        for article_id in article_ids_to_process:
                            if len(processing_tasks) < PROCESS_CONCURRENCY:
                                task = asyncio.create_task(process_article(supabase, article_id, gemini_semaphore))
                                processing_tasks.add(task)
                            else:
                                logger.warning("Process concurrency limit reached, will pick up remaining IDs in next iteration if still pending.")
                                break 
                    else:
                        logger.debug("No pending articles found in this check.")
                else:
                     logger.debug("Process concurrency limit reached. Waiting for tasks to complete.")
            else:
                logger.debug(f"Process concurrency limit ({PROCESS_CONCURRENCY}) met. Waiting for tasks to complete.")

            await asyncio.sleep(LOOP_DELAY_SECONDS)

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down gracefully...")
        if processing_tasks:
            logger.info(f"Waiting for {len(processing_tasks)} active article processing tasks to complete...")
            await asyncio.gather(*processing_tasks, return_exceptions=True)
            logger.info("All active tasks finished.")
    except Exception as e:
        logger.critical(f"Critical error in main loop: {e}", exc_info=True)
        if processing_tasks:
            logger.info(f"Attempting to wait for {len(processing_tasks)} active tasks before exiting due to critical error...")
            await asyncio.gather(*processing_tasks, return_exceptions=True)
    finally:
        logger.info("Processing loop finished.")

if __name__ == "__main__":
    if not all([SUPABASE_URL, SUPABASE_KEY]) or not GOOGLE_API_KEYS_LIST:
         logger.critical("Error: SUPABASE_URL, SUPABASE_KEY must be set in .env, and GOOGLE_API_KEYS_LIST must be populated in the script.")
    else:
        try: 
            asyncio.run(main())
        except Exception as e:
            logger.critical(f"Script failed to run or unhandled exception in main: {e}", exc_info=True)