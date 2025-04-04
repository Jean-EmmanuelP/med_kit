import datetime
import json
import re
import os
import logging
import time
from typing import List, Dict, Optional, Any, Set

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, WebDriverException, ElementClickInterceptedException
)
from selenium.webdriver.remote.webelement import WebElement

# --- Configuration ---
LOGIN_URL = "https://www.evidencealerts.com/Account/Login?ReturnUrl=%2FArticles%2FAlerted"
BASE_URL = "https://www.evidencealerts.com"
EMAIL = "aalleexxiiss123456@gmail.com"
PASSWORD = "imf!gl@IW#NNJ0DWJ4^uObNEO!!uks99i@$%2KZF"

# --- Output Configuration ---
OUTPUT_DIR_LINKS = 'links'
OUTPUT_DIR_DATA = 'data'
OUTPUT_DIR_SUMMARIES = 'summaries'
# --- MODIFIED: Changed timestamp format ---
TIMESTAMP_FORMAT = '%Y%m%d' # Changed format to YYYYMMDD

# --- Selenium Configuration ---
WEBDRIVER_WAIT_TIMEOUT = 45 # seconds

# --- Selectors (Centralized for maintainability) ---
# Login Page
LOGIN_FORM_SELECTOR = "section#loginForm form"
EMAIL_FIELD_ID = "Email"
PASSWORD_FIELD_ID = "Password"
LOGIN_BUTTON_SELECTOR = "input[type='submit'][value='Log in']"
# Alerted Articles Page
ALERTED_ARTICLES_TABLE_SELECTOR = "table.table-striped.table-hover"
ARTICLE_LINK_SELECTOR = "table.table-striped tr[id^='Article'] a[href^='/Articles/AlertedArticle/']"
# Article Detail Page (EvidenceAlerts)
ARTICLE_RECORD_DIV_ID = "ArticleRecord"
PUBMED_LINK_XPATH = "//a[contains(@class, 'article-record-button') and contains(., 'View on PubMed')]"
ABSTRACT_PANEL_XPATH = "//div[@id='ArticleRecord']//div[contains(@class,'panel-heading') and contains(.,'Abstract')]/following-sibling::div[contains(@class,'panel-body')]"
RATINGS_TABLE_ID = "SearchRatings"
CATEGORY_ROW_XPATH = ".//tr[td[1] and not(contains(td[2]/text(), 'Coming Soon...')) and not(contains(td[3]/text(), 'Coming Soon...'))]"
CATEGORY_ROW_FALLBACK_TAG = "tr"
CATEGORY_CELL_TAG = "td"
# PubMed Page
PUBMED_DOI_LINK_SELECTOR = "span.identifier.doi a.id-link"
PUBMED_DOI_META_SELECTOR = 'meta[name="citation_doi"]'
PUBMED_JOURNAL_META_SELECTOR = 'meta[name="citation_journal_title"]'
PUBMED_JOURNAL_BUTTON_SELECTOR = "#full-view-journal-trigger"
PUBMED_DATE_META_SELECTOR = 'meta[name="citation_date"]'
PUBMED_TITLE_META_SELECTOR = 'meta[name="citation_title"]' # Added
PUBMED_TITLE_H1_SELECTOR = "h1.heading-title"              # Added

# --- Category Mapping ---
CATEGORY_MAP: Dict[str, str] = {
    # General / Primary Care
    "Emergency Medicine": "Urgences",
    "Family Medicine (FM)/General Practice (GP)": "Médecine Générale",
    "FM/GP/Anesthesia": "Médecine Générale", # Consolidate under GP
    "FM/GP/Obstetrics": "Médecine Générale", # Consolidate under GP
    "FM/GP/Mental Health": "Médecine Générale", # Consolidate under GP
    "General Internal Medicine-Primary Care(US)": "Médecine Générale",
    "Hospital Doctor/Hospitalists": "Médecine Interne", # Often manage internal med cases inpatient
    "Internal Medicine (or see subspecialties below)": "Médecine Interne",
    "Pediatrics (General)": "Pédiatrie",
    "Pediatric Hospital Medicine": "Pédiatrie",
    "Pediatric Neonatology": "Pédiatrie",
    "Pediatric Emergency Medicine": "Pédiatrie", # Could argue Urgences, but keep under Peds
    "Gynecology": "Gynécologie-obstétrique",
    "Obstetrics": "Gynécologie-obstétrique",
    "Occupational and Environmental Health": "Médecine du Travail",
    "Public Health": "Santé Publique",

    # Internal Medicine Subspecialties
    "Allergy and Immunology": "Allergie et immunologie",
    "Cardiology": "Cardiologie",
    "Dermatology": "Dermatologie",
    "Endocrine": "Endocrinologie-Diabétologie-Nutrition",
    "Gastroenterology": "Hépato-Gastroentérologie",
    "Genetics": "Génétique",
    "Geriatrics": "Gériatrie",
    "Hematology": "Hématologie",
    "Hemostasis and Thrombosis": "Hématologie", # Consolidate under Hematology
    "Infectious Disease": "Maladies infectieuses",
    "Tropical and Travel Medicine": "Maladies infectieuses", # Consolidate
    "Intensivist/Critical Care": "Anesthésie - Réanimation", # Often combined
    "Nephrology": "Néphrologie",
    "Neurology": "Neurologie",
    "Physical Medicine and Rehabilitation": "Médecine physique et réadaptation",
    "Respirology/Pulmonology": "Pneumologie",
    "Rheumatology": "Rhumatologie",

    # Oncology (Consolidated)
    "Oncology - General": "Oncologie",
    "Oncology - Breast": "Oncologie",
    "Oncology - Gastrointestinal": "Oncologie",
    "Oncology - Gynecology": "Oncologie",
    "Oncology - Hematology": "Oncologie", # Could argue Hematologie, but keep under Onco
    "Oncology - Lung": "Oncologie",
    "Oncology - Palliative and Supportive Care": "Oncologie", # Or Médecine de la douleur? Sticking to Onco
    "Oncology - Pediatric": "Oncologie", # Or Pédiatrie? Sticking to Onco
    "Oncology - Genitourinary": "Oncologie", # Or Urologie? Sticking to Onco

    # Psychiatry / Anesthesia
    "Psychiatry": "Psychiatrie",
    "Anesthesiology": "Anesthésie - Réanimation",

    # Surgery
    "Surgery - General": "Chirurgie digestive", # Often covers abdominal/digestive general cases
    "Surgery - Cardiac": "Chirurgie cardiaque",
    "Surgery - Colorectal": "Chirurgie digestive", # Consolidate
    "Surgery - Ear Nose Throat": "Chirurgie ORL",
    "Surgery - Gastrointestinal": "Chirurgie digestive", # Consolidate
    "Surgery - Head and Neck": "Chirurgie ORL", # Often managed by ENT
    "Surgery - Neurosurgery": "Neurochirurgie",
    "Surgery - Oncology": "Oncologie", # Focus on the field, not just surgery
    "Surgery - Ophthalmology": "Ophtalmologie",
    "Surgery - Plastic": "Chirurgie plastique",
    "Surgery - Orthopaedics": "Chirurgie orthopédique",
    "Surgery - Thoracic": "Chirurgie thoracique",
    "Surgery - Urology": "Urologie",
    "Surgery - Vascular": "Chirurgie vasculaire",

    # Special Interest
    "Special Interest - Obesity -- Physician": "Endocrinologie-Diabétologie-Nutrition", # Closest medical fit
    "Special Interest - Obesity -- Surgeon": "Chirurgie digestive", # Often Bariatric is under digestive
    "Special Interest - Pain -- Physician": "Médecine de la douleur",
}

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# --- Helper Functions ---

# --- MODIFIED: Create date-specific subdirectories ---
def create_output_directories():
    """Creates the necessary date-specific output directories if they don't exist."""
    logger.info("Ensuring output directories exist...")
    today_date_str = datetime.date.today().strftime(TIMESTAMP_FORMAT)

    links_date_dir = os.path.join(OUTPUT_DIR_LINKS, today_date_str)
    data_date_dir = os.path.join(OUTPUT_DIR_DATA, today_date_str)
    summaries_date_dir = os.path.join(OUTPUT_DIR_SUMMARIES, today_date_str) # Also handle summaries dir

    os.makedirs(links_date_dir, exist_ok=True)
    os.makedirs(data_date_dir, exist_ok=True)
    os.makedirs(summaries_date_dir, exist_ok=True)

    logger.info(f"Ensured directories exist: {links_date_dir}, {data_date_dir}, {summaries_date_dir}")

# --- MODIFIED: Generate filenames within date-specific directories ---
def get_output_filenames() -> (str, str):
    """Generates filenames for links and data within date-specific directories."""
    today_date_str = datetime.date.today().strftime(TIMESTAMP_FORMAT)
    links_filename = os.path.join(OUTPUT_DIR_LINKS, today_date_str, "links.txt")
    data_filename = os.path.join(OUTPUT_DIR_DATA, today_date_str, "data.json")
    logger.info(f"Links filename set to: {links_filename}")
    logger.info(f"Data filename set to: {data_filename}")
    return links_filename, data_filename

def setup_driver() -> (WebDriver, WebDriverWait):
    """Initializes and returns the WebDriver and WebDriverWait."""
    logger.info("Initializing Chrome WebDriver...")
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, WEBDRIVER_WAIT_TIMEOUT)
    logger.info("WebDriver initialized.")
    return driver, wait

def perform_login(driver: WebDriver, wait: WebDriverWait) -> bool:
    """Logs into the EvidenceAlerts website."""
    logger.info(f"Navigating to login page: {LOGIN_URL}")
    try:
        driver.get(LOGIN_URL)
        logger.info("Waiting for login form...")
        login_form = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, LOGIN_FORM_SELECTOR)))
        logger.info("Login form found.")

        email_field = login_form.find_element(By.ID, EMAIL_FIELD_ID)
        password_field = login_form.find_element(By.ID, PASSWORD_FIELD_ID)
        login_button = login_form.find_element(By.CSS_SELECTOR, LOGIN_BUTTON_SELECTOR)

        logger.info("Entering credentials...")
        email_field.send_keys(EMAIL)
        password_field.send_keys(PASSWORD)

        logger.info("Attempting login...")
        login_button.click()

        logger.info("Login submitted. Waiting for alerted articles table...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ALERTED_ARTICLES_TABLE_SELECTOR)))
        logger.info("Login successful and alerted articles page loaded!")
        return True
    except TimeoutException:
        logger.error("Timeout during login process. Could not find expected elements.")
        return False
    except NoSuchElementException as e:
        logger.error(f"Could not find login element: {e}")
        return False
    except WebDriverException as e:
        logger.error(f"WebDriver error during login: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred during login: {e}")
        return False

def extract_article_links(driver: WebDriver) -> List[str]:
    """Finds and extracts unique article links from the alerted articles page."""
    logger.info("Finding article links...")
    article_links = []
    processed_links = set()
    try:
        article_link_elements = driver.find_elements(By.CSS_SELECTOR, ARTICLE_LINK_SELECTOR)
        if not article_link_elements:
            logger.warning("No article link elements found using the selector.")
            return []

        logger.info(f"Found {len(article_link_elements)} potential article link elements.")
        for link_element in article_link_elements:
            try:
                relative_link = link_element.get_attribute('href')
                if relative_link and relative_link not in processed_links:
                    full_link = BASE_URL + relative_link if not relative_link.startswith('http') else relative_link
                    article_links.append(full_link)
                    processed_links.add(relative_link)
            except Exception as link_err:
                logger.warning(f"  Error extracting href from an element: {link_err}")

        logger.info(f"Successfully extracted {len(article_links)} unique article links.")
        return article_links
    except NoSuchElementException:
        logger.warning("Could not find article link elements on the page.")
        return []
    except Exception as e:
        logger.error(f"An error occurred during link extraction: {e}")
        return []

# No change needed here, it accepts the full filename path
def save_links_to_file(links: List[str], filename: str):
    """Saves the extracted links to a text file."""
    if not links:
        logger.info("No links to save.")
        return
    logger.info(f"Saving {len(links)} links to {filename}...")
    try:
        # Ensure the directory exists before writing (should be done by create_output_directories, but good practice)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            for link in links:
                f.write(link + '\n')
        logger.info("Links saved successfully.")
    except IOError as io_err:
        logger.error(f"Error saving links to file {filename}: {io_err}")

def extract_data_from_pubmed(driver: WebDriver, wait: WebDriverWait) -> Dict[str, Optional[str]]:
    """
    Extracts DOI, Journal Name, Publication Date, and Title from the PubMed page.
    Assumes the driver is currently focused on the PubMed window/tab.
    """
    pubmed_data = {"doi": None, "journal": None, "published_at": None, "title": None}
    logger.info("    Attempting to extract data from PubMed page...")

    # ---- Extract Title ----
    try:
        title_meta = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PUBMED_TITLE_META_SELECTOR)))
        title_content = title_meta.get_attribute('content').strip()
        if title_content:
            pubmed_data["title"] = title_content
            logger.info(f"      Title extracted from PubMed meta tag: {pubmed_data['title'][:50]}...") # Log truncated title
        else:
            logger.warning("      Title meta tag found but content is empty. Trying H1 tag...")
            raise NoSuchElementException # Trigger fallback intentionally if content is empty
    except (NoSuchElementException, TimeoutException):
        logger.info("      Title meta tag not found or empty. Trying H1 tag (fallback)...")
        try:
            title_h1 = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PUBMED_TITLE_H1_SELECTOR)))
            wait.until(lambda d: title_h1.text.strip() != "") # Wait for text to be non-empty
            pubmed_data["title"] = title_h1.text.strip()
            if pubmed_data["title"]:
                logger.info(f"      Title extracted from PubMed H1 tag (fallback): {pubmed_data['title'][:50]}...") # Log truncated title
            else:
                logger.warning("      Title H1 tag found but text content is empty.")
        except (NoSuchElementException, TimeoutException):
            logger.warning("      Could not find Title meta tag or H1 tag on PubMed page.")
        except Exception as meta_title_err:
            logger.error(f"      Error extracting Title from H1 tag: {meta_title_err}")
    except Exception as pubmed_title_err:
        logger.error(f"      Unexpected error extracting Title on PubMed page: {pubmed_title_err}")


    # ---- Extract DOI ----
    try:
        doi_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PUBMED_DOI_LINK_SELECTOR)))
        wait.until(lambda d: doi_element.text.strip() != "") # Wait for text to be non-empty
        pubmed_data["doi"] = doi_element.text.strip()
        logger.info(f"      DOI extracted from PubMed link: {pubmed_data['doi']}")
    except (NoSuchElementException, TimeoutException):
        logger.info("      DOI link element not found or timed out. Trying DOI meta tag...")
        try:
            meta_doi = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PUBMED_DOI_META_SELECTOR)))
            pubmed_data["doi"] = meta_doi.get_attribute('content').strip()
            if pubmed_data["doi"]:
                logger.info(f"      DOI extracted from PubMed meta tag (fallback): {pubmed_data['doi']}")
            else:
                logger.warning("      DOI meta tag found but content is empty.")
        except (NoSuchElementException, TimeoutException):
            logger.warning("      Could not find DOI link or meta tag on PubMed page.")
        except Exception as meta_doi_err:
            logger.error(f"      Error extracting DOI from meta tag: {meta_doi_err}")
    except Exception as pubmed_doi_err:
        logger.error(f"      Unexpected error extracting DOI on PubMed page: {pubmed_doi_err}")

    # ---- Extract Journal Name ----
    try:
        journal_meta = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PUBMED_JOURNAL_META_SELECTOR)))
        pubmed_data["journal"] = journal_meta.get_attribute('content').strip()
        if pubmed_data["journal"]:
            logger.info(f"      Journal extracted from PubMed meta tag: {pubmed_data['journal']}")
        else:
            logger.warning("      Journal meta tag found but content is empty. Trying button...")
            try:
                journal_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PUBMED_JOURNAL_BUTTON_SELECTOR)))
                pubmed_data["journal"] = journal_button.text.strip()
                logger.info(f"      Journal extracted from PubMed button (fallback): {pubmed_data['journal']}")
            except (NoSuchElementException, TimeoutException):
                 logger.warning("      Journal button fallback also failed.")
    except (NoSuchElementException, TimeoutException):
        logger.info("      Journal meta tag not found on PubMed page. Trying button...")
        try:
            journal_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PUBMED_JOURNAL_BUTTON_SELECTOR)))
            pubmed_data["journal"] = journal_button.text.strip()
            logger.info(f"      Journal extracted from PubMed button (fallback): {pubmed_data['journal']}")
        except (NoSuchElementException, TimeoutException):
             logger.warning("      Journal meta tag and button fallback failed.")
    except Exception as pubmed_journal_err:
        logger.error(f"      Error extracting Journal on PubMed page: {pubmed_journal_err}")

    # ---- Extract Publication Date ----
    try:
        published_at_meta = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, PUBMED_DATE_META_SELECTOR)))
        pubmed_data["published_at"] = published_at_meta.get_attribute('content').strip()
        if pubmed_data["published_at"]:
            logger.info(f"      Published At date extracted from PubMed meta tag: {pubmed_data['published_at']}")
        else:
            logger.warning("      Published At meta tag found but content is empty.")
    except (NoSuchElementException, TimeoutException):
        logger.warning("      Published At meta tag not found on PubMed page.")
    except Exception as pubmed_date_err:
        logger.error(f"      Error extracting Published At date on PubMed page: {pubmed_date_err}")

    return pubmed_data

def process_pubmed_interaction(driver: WebDriver, wait: WebDriverWait) -> Dict[str, Optional[str]]:
    """
    Handles clicking the PubMed link, switching windows, extracting data,
    and returning to the original window.
    Returns a dictionary with 'doi', 'journal', 'published_at', 'title' or None values.
    """
    original_window = driver.current_window_handle
    initial_window_count = len(driver.window_handles)
    pubmed_data = {"doi": None, "journal": None, "published_at": None, "title": None}

    try:
        pubmed_link_element = wait.until(EC.element_to_be_clickable((By.XPATH, PUBMED_LINK_XPATH)))
        logger.info("    Found PubMed link element.")
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", pubmed_link_element)
            time.sleep(0.2) # Short pause after scroll
            pubmed_link_element.click()
        except ElementClickInterceptedException:
            logger.warning("    PubMed link click intercepted, trying JavaScript click...")
            driver.execute_script("arguments[0].click();", pubmed_link_element)

        logger.info("    Clicked PubMed link.")

        wait.until(EC.number_of_windows_to_be(initial_window_count + 1))
        logger.info(f"    Window count increased to {len(driver.window_handles)}.")

        new_window = None
        for window_handle in driver.window_handles:
            if window_handle != original_window:
                new_window = window_handle
                break

        if new_window:
            driver.switch_to.window(new_window)
            logger.info(f"    Switched to PubMed window. Current URL: {driver.current_url}")
            try:
                pubmed_data = extract_data_from_pubmed(driver, wait)
            finally:
                logger.info("    Closing PubMed window...")
                driver.close()
                driver.switch_to.window(original_window)
                logger.info("    Switched back to EvidenceAlerts window.")
                wait.until(EC.number_of_windows_to_be(initial_window_count))
                wait.until(EC.url_contains("evidencealerts.com"))
                logger.info(f"    Successfully returned to: {driver.current_url}")
        else:
            logger.warning("    Could not identify the new PubMed window handle.")
            if driver.current_window_handle != original_window:
                 logger.warning("    Driver context is not the original window. Attempting to switch back forcefully.")
                 try:
                     driver.switch_to.window(original_window)
                     logger.info("    Forceful switch back successful.")
                 except Exception as force_switch_err:
                      logger.error(f"   Could not forcefully switch back: {force_switch_err}")


    except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
        logger.warning(f"    'View on PubMed' link interaction failed: {e}")
    except WebDriverException as wde:
         logger.error(f"    WebDriverException during PubMed link processing: {wde}")
         if original_window in driver.window_handles and driver.current_window_handle != original_window:
             try:
                 logger.warning("    Attempting to switch back to original window after WebDriverException.")
                 driver.switch_to.window(original_window)
             except Exception as switch_err:
                 logger.error(f"    Could not switch back after WebDriverException: {switch_err}")
         elif original_window not in driver.window_handles:
             logger.error("    Original window seems closed. Cannot reliably continue PubMed interaction for this article.")
             return {"doi": None, "journal": None, "published_at": None, "title": None}
    except Exception as e:
        logger.error(f"    Unexpected error during PubMed interaction: {e}")
        if driver.current_window_handle != original_window and original_window in driver.window_handles:
            try:
                driver.switch_to.window(original_window)
                logger.info("    Switched back to original window after unexpected error.")
            except Exception as switch_err:
                logger.error(f"    Could not switch back to original window after error: {switch_err}")

    return pubmed_data

def extract_abstract(driver: WebDriver, wait: WebDriverWait) -> Optional[str]:
    """Extracts the abstract text from the EvidenceAlerts article page."""
    logger.info("    Extracting abstract from EvidenceAlerts page...")
    try:
         abstract_element = wait.until(EC.presence_of_element_located((By.XPATH, ABSTRACT_PANEL_XPATH)))
         abstract = abstract_element.text.strip()
         logger.info(f"      Abstract extracted (length: {len(abstract)}).")
         return abstract
    except (NoSuchElementException, TimeoutException):
         logger.warning("      Could not find the abstract element or timed out.")
         return None
    except Exception as abstract_err:
         logger.error(f"      Error extracting abstract: {abstract_err}")
         return None

def extract_categories(driver: WebDriver, wait: WebDriverWait) -> List[str]:
    """
    Extracts the rated categories from the EvidenceAlerts article page
    and translates them to French using CATEGORY_MAP.
    """
    logger.info("    Extracting and translating categories...")
    translated_categories: Set[str] = set()

    try:
        ratings_table = wait.until(EC.presence_of_element_located((By.ID, RATINGS_TABLE_ID)))

        def process_row(row_element: WebElement):
            try:
                category_name_en = row_element.find_element(By.XPATH, "./td[1]").text.strip()
                if category_name_en:
                    category_name_fr = CATEGORY_MAP.get(category_name_en)
                    if category_name_fr:
                        translated_categories.add(category_name_fr)
                        logger.debug(f"      Mapped '{category_name_en}' to '{category_name_fr}'")
                    else:
                        logger.warning(f"      Category '{category_name_en}' found on page but not in CATEGORY_MAP. Skipping.")
            except NoSuchElementException:
                logger.debug("      Skipping row - could not find category cell (td[1]).")
            except Exception as cat_row_err:
                logger.warning(f"      Error processing a category row: {cat_row_err}")

        try:
            category_rows = ratings_table.find_elements(By.XPATH, CATEGORY_ROW_XPATH)
            if category_rows:
                logger.info(f"      Found {len(category_rows)} potential category rows using primary XPath.")
                for row in category_rows:
                    process_row(row)
            else:
                logger.info("      Primary category XPath found no rows. Using fallback method on all rows.")
                all_rows = ratings_table.find_elements(By.TAG_NAME, CATEGORY_ROW_FALLBACK_TAG)
                if all_rows:
                    data_rows_to_check = all_rows[1:] if all_rows[0].find_elements(By.TAG_NAME, "th") else all_rows
                    logger.info(f"      Checking {len(data_rows_to_check)} rows in fallback.")
                    for row in data_rows_to_check:
                        try:
                            cols = row.find_elements(By.TAG_NAME, CATEGORY_CELL_TAG)
                            if len(cols) >= 3:
                                rating_text_1 = cols[1].text.strip()
                                rating_text_2 = cols[2].text.strip()
                                has_rating = "Coming Soon..." not in rating_text_1 and "Coming Soon..." not in rating_text_2
                                if has_rating:
                                     process_row(row)
                                else:
                                     logger.debug("      Skipping fallback row - 'Coming Soon...' detected.")
                            else:
                                logger.debug("      Skipping fallback row - not enough columns.")
                        except Exception as fallback_row_err:
                             logger.warning(f"      Error checking a fallback category row: {fallback_row_err}")

        except NoSuchElementException:
             logger.warning("      Could not find category rows using primary XPath.")


        if translated_categories:
            logger.info(f"      Final French categories found: {', '.join(sorted(list(translated_categories)))}")
        else:
            logger.info("      No valid mappable categories found for this article.")

    except (NoSuchElementException, TimeoutException):
        logger.warning("    Could not find/timeout waiting for the ratings table (ID='SearchRatings').")
    except Exception as cat_err:
        logger.error(f"    An unexpected error occurred extracting/translating categories: {cat_err}")

    return sorted(list(translated_categories))

def process_single_article(driver: WebDriver, wait: WebDriverWait, article_url: str) -> Optional[Dict[str, Any]]:
    """Navigates to an article URL and extracts all relevant data."""
    logger.info(f"Processing article: {article_url}")
    current_article_data = {
        "url": article_url,
        "title": None,
        "link": None,
        "abstract": None,
        "journal": None,
        "published_at": None,
        "categories": []
    }

    try:
        driver.get(article_url)
        wait.until(EC.presence_of_element_located((By.ID, ARTICLE_RECORD_DIV_ID)))
        logger.info("  EvidenceAlerts article page loaded.")

        pubmed_info = process_pubmed_interaction(driver, wait)
        current_article_data["title"] = pubmed_info.get("title")
        if pubmed_info.get("doi"):
            doi = pubmed_info['doi']
            if 'doi.org' in doi:
                match = re.search(r'(10\.\d{4,9}/[-._;()/:A-Z0-9]+)', doi, re.IGNORECASE)
                if match:
                    doi = match.group(1)
                else:
                    logger.warning(f"    Could not reliably extract DOI from full link: {doi}. Using as is for PubMed link.")
            current_article_data["link"] = f"https://pubmed.ncbi.nlm.nih.gov/?term={doi}"
        current_article_data["journal"] = pubmed_info.get("journal")
        current_article_data["published_at"] = pubmed_info.get("published_at")

        current_article_data["abstract"] = extract_abstract(driver, wait)
        current_article_data["categories"] = extract_categories(driver, wait)

        ordered_data = {
            "url": current_article_data["url"],
            "title": current_article_data["title"],
            "link": current_article_data["link"],
            "journal": current_article_data["journal"],
            "published_at": current_article_data["published_at"],
            "abstract": current_article_data["abstract"],
            "categories": current_article_data["categories"]
        }
        return ordered_data

    except TimeoutException:
        logger.error(f"Timeout waiting for core EvidenceAlerts page elements on {article_url}. Skipping article.")
        return None
    except WebDriverException as wde_main:
         logger.error(f"WebDriverException processing EvidenceAlerts page {article_url}: {wde_main}")
         raise
    except Exception as page_err:
        logger.error(f"Failed to process page {article_url}: {page_err}")
        return None

# No change needed here, it accepts the full filename path
def save_data_to_json(data: List[Dict[str, Any]], filename: str):
    """Saves the collected article data to a JSON file."""
    if not data:
        logger.info("No data was extracted, skipping JSON file save.")
        return

    logger.info(f"Saving extracted data for {len(data)} articles to {filename}...")
    try:
        # Ensure the directory exists before writing (should be done by create_output_directories, but good practice)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info("Data saved successfully to JSON.")
    except IOError as io_err:
         logger.error(f"Error saving data to file {filename}: {io_err}")
    except TypeError as json_err:
        logger.error(f"Error serializing data to JSON: {json_err}")


# --- Main Execution ---
def main():
    """Main script execution function."""
    driver = None
    all_article_data = []

    try:
        # --- MODIFIED: Call order matters - get filenames after ensuring directories ---
        # 1. Create directories first (needs the date)
        create_output_directories()
        # 2. Get the full filenames (also needs the date)
        links_filename, data_filename = get_output_filenames()

        driver, wait = setup_driver()

        if not perform_login(driver, wait):
            logger.critical("Login failed. Cannot proceed.")
            return

        article_links = extract_article_links(driver)
        # 3. Save links using the obtained filename
        save_links_to_file(article_links, links_filename)

        if not article_links:
            logger.info("No article links found to process.")
            return

        logger.info(f"\nStarting processing of {len(article_links)} articles...")
        for i, link in enumerate(article_links, 1):
            logger.info(f"\n--- Article {i}/{len(article_links)} ---")
            try:
                article_data = process_single_article(driver, wait, link)
                if article_data:
                    all_article_data.append(article_data)
            except WebDriverException as inner_wde:
                 logger.critical(f"Critical WebDriverException encountered processing article {i} ({link}). Stopping processing. Error: {inner_wde}")
                 break
            except Exception as article_proc_err:
                 logger.error(f"Unhandled exception processing article {i} ({link}): {article_proc_err}. Continuing...")
                 continue

        # 4. Save data using the obtained filename
        save_data_to_json(all_article_data, data_filename)

    except Exception as e:
        logger.critical(f"A critical error occurred during the main process: {e}", exc_info=True)
        if driver:
            try:
                # --- MODIFIED: Save screenshot in a consistent place if needed ---
                today_date_str = datetime.date.today().strftime(TIMESTAMP_FORMAT)
                error_screenshot_filename = f"error_screenshot_{today_date_str}.png"
                driver.save_screenshot(error_screenshot_filename)
                logger.info(f"Saved an error screenshot to {error_screenshot_filename}")
            except Exception as screen_err:
                 logger.error(f"Could not save error screenshot: {screen_err}")
    finally:
        if driver:
            logger.info("Closing the browser...")
            try:
                driver.quit()
                logger.info("Browser closed.")
            except Exception as quit_err:
                logger.error(f"Error closing browser: {quit_err}")

if __name__ == "__main__":
    main()