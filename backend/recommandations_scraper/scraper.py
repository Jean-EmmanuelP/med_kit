import os
import sys
import re
import argparse
import time
import json
import random
from dotenv import load_dotenv

import google.generativeai as genai

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains

from selenium_stealth import stealth

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def setup_selenium_driver():
    print("Setting up stealth Selenium driver in headed mode...")
    options = webdriver.ChromeOptions()
    
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        stealth(driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        
        print("Stealth driver setup complete. A browser window will be used.")
        return driver
    except Exception as e:
        print(f"Error setting up Selenium driver: {e}")
        sys.exit(1)

def get_sanitized_id_from_url(url):
    match = re.search(r'pubmed\.ncbi\.nlm\.nih\.gov/(\d+)/?', url)
    if match:
        return match.group(1)
    
    term_match = re.search(r'term=([^&]+)', url)
    if term_match:
        term = term_match.group(1)
        return re.sub(r'[^a-zA-Z0-9_-]', '_', term)
    
    return f"article_{int(time.time())}"

def get_full_text_links(driver, pubmed_url):
    print(f"  Finding full-text links from: {pubmed_url}")
    try:
        driver.get(pubmed_url)
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.ID, "article-details")))
        time.sleep(random.uniform(1.0, 2.5))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        links_list = soup.select('div.full-text-links-list a.link-item')
        
        if not links_list:
            print("  Article page loaded, but no full-text link elements found.")
            return []

        extracted_links = [link['href'] for link in links_list if 'href' in link.attrs]
        print(f"  Found {len(extracted_links)} full-text link(s).")
        return list(set(extracted_links))
    except Exception as e:
        print(f"  Could not find full-text links for {pubmed_url}. Error: {e}")
        return []

def extract_content_with_stealth_driver(driver, article_urls):
    print("  Extracting article content with human-like interaction...")
    all_content = []

    for i, url in enumerate(article_urls):
        print(f"    Opening link {i+1}/{len(article_urls)}: {url[:80]}...")
        try:
            driver.get(url)
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(random.uniform(2.0, 4.0))

            # Check for captcha indicators
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            page_text = soup.get_text().lower()
            
            # Common captcha indicators
            captcha_indicators = [
                'captcha', 'verify you are human', 'prove you are not a robot',
                'security check', 'human verification', 'confirm you are human',
                'i am not a robot', 'verify your identity', 'cloudflare',
                'access denied', 'bot detection', 'suspicious activity'
            ]
            
            if any(indicator in page_text for indicator in captcha_indicators):
                print(f"      CAPTCHA or security check detected on {url}. Skipping this link.")
                return None

            print("      Simulating user scrolling...")
            scroll_pause_time = random.uniform(0.6, 1.2)
            screen_height = driver.execute_script("return window.screen.height;")
            for j in range(1, 4):
                driver.execute_script(f"window.scrollTo(0, {screen_height * j});")
                time.sleep(scroll_pause_time)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            article_body = soup.find('article') or soup.find('main') or soup.body
            
            if article_body:
                for tag in article_body.select('nav, header, footer, script, style, [role="navigation"], [role="banner"], [role="contentinfo"]'):
                    tag.decompose()
                body_text = article_body.get_text(separator='\n', strip=True)
                
                # Check if extracted content is meaningful (not just navigation/error content)
                if len(body_text.strip()) < 100:
                    print(f"      Content too short ({len(body_text)} chars), likely extraction failure. Skipping this link.")
                    return None
                
                # Check for common error page indicators
                error_indicators = [
                    'page not found', '404 error', 'access denied', 'forbidden',
                    'service unavailable', 'temporarily unavailable', 'maintenance mode'
                ]
                
                if any(indicator in body_text.lower() for indicator in error_indicators):
                    print(f"      Error page detected. Skipping this link.")
                    return None
                
                all_content.append(f"\n\n--- START OF CONTENT FROM {url} ---\n\n")
                all_content.append(body_text)
                all_content.append(f"\n\n--- END OF CONTENT FROM {url} ---\n\n")
                print("      Successfully extracted content.")
            else:
                 print("      Could not find main body content. Skipping this link.")
                 return None
        
        except Exception as e:
            print(f"      An error occurred while opening {url}: {e}. Skipping this link.")
            return None
            
    return "".join(all_content) if all_content else None

def summarize_with_gemini(article_content, gemini_prompt):
    print("  Summarizing with Gemini...")
    
    model = genai.GenerativeModel(
        'gemini-2.5-flash-preview-05-20',
        generation_config={"response_mime_type": "application/json"}
    )
    
    full_prompt = f"{gemini_prompt}\n\n--- ARTICLE CONTENT TO SUMMARIZE ---\n\n{article_content}"
    
    retry_delays = [10, 20, 35]
    for i, delay in enumerate(retry_delays + [0]):
        try:
            response = model.generate_content(full_prompt)
            response_text = response.text.strip()
            
            # Check if the model detected error/captcha content
            if any(keyword in response_text.lower() for keyword in ['captcha', 'error_page', 'extraction_error', 'no_medical_content']):
                print("  Model detected captcha/error page or non-medical content. Skipping save.")
                return None
            
            print("  Successfully received summary from Gemini.")
            return response_text
        except Exception as e:
            print(f"  Error calling Gemini API: {e}")
            if i < len(retry_delays):
                print(f"  Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                print("  All retry attempts failed.")
                return None
    return None

def save_summary_json(filename, summary_json_str, source_url):
    filepath = os.path.join(OUTPUT_DIR, filename)
    try:
        data = json.loads(summary_json_str)
        data['link'] = source_url
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  Successfully saved structured summary to {filepath}\n")
    except json.JSONDecodeError:
        print(f"  Error: Gemini did not return valid JSON. Could not parse.")
        fallback_path = filepath.replace('.json', '.raw_output.txt')
        with open(fallback_path, 'w', encoding='utf-8') as f:
            f.write(f"--- Source URL: {source_url} ---\n\n")
            f.write(summary_json_str)
        print(f"  Raw output saved for debugging to {fallback_path}\n")
    except Exception as e:
        print(f"  Error saving summary to {filepath}. Error: {e}\n")

def main():
    parser = argparse.ArgumentParser(description="Scrape PubMed articles, summarize with Gemini into structured JSON, and save.")
    parser.add_argument("input_file", type=str, help="Path to the .txt file containing PubMed URLs.")
    parser.add_argument("--prompt_file", type=str, default="prompt.txt", help="Path to the .txt file containing the Gemini prompt.")
    args = parser.parse_args()

    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("Error: GOOGLE_API_KEY not found in .env file.")
        sys.exit(1)
    genai.configure(api_key=google_api_key)

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found.")
        sys.exit(1)
        
    if not os.path.exists(args.prompt_file):
        print(f"Error: Prompt file '{args.prompt_file}' not found.")
        sys.exit(1)
        
    with open(args.prompt_file, 'r', encoding='utf-8') as f:
        gemini_prompt = f.read()

    with open(args.input_file, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    random.shuffle(urls)

    driver = setup_selenium_driver()

    for i, url in enumerate(urls):
        print(f"--- Processing URL {i+1}/{len(urls)}: {url} ---")
        
        sanitized_id = get_sanitized_id_from_url(url)
        output_filename = f"{sanitized_id}_summary.json"
        
        if os.path.exists(os.path.join(OUTPUT_DIR, output_filename)):
            print(f"  Summary for {sanitized_id} already exists. Skipping.\n")
            continue
            
        full_text_links = get_full_text_links(driver, url)

        if not full_text_links:
            print(f"  No full-text links found for {sanitized_id}. Moving to next URL.\n")
            continue
            
        first_link_to_scrape = [full_text_links[0]]
        article_content = extract_content_with_stealth_driver(driver, first_link_to_scrape)

        if article_content:
            summary_json_str = summarize_with_gemini(article_content, gemini_prompt)
            if summary_json_str:
                save_summary_json(output_filename, summary_json_str, url)
        else:
            print(f"  Failed to extract any content for {sanitized_id}.\n")

    driver.quit()
    print("--- Script finished ---")

if __name__ == "__main__":
    main()