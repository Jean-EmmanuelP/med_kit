# Article Classification Script

This script classifies articles stored in a Supabase `articles` table into two categories using information scraped from their PubMed links and analysis by the Google Gemini API.

## Categories

1.  **Category 1: Official Recommendation/Guideline:** Documents from scientific bodies, societies, or official groups providing recommendations or consensus.
2.  **Category 2: Classic Scientific Article:** Research papers (clinical studies, reviews, meta-analyses) from research teams.

## How it Works

1.  **Connects** to the Supabase database specified in the `.env` file.
2.  **Loads Processed IDs:** Checks the `output/` directory for existing JSON result files (`category_1_recommendations.json`, `category_2_classic_articles.json`) to determine which article IDs have already been processed.
3.  **Fetches Articles:** Queries the `articles` table in batches for entries with an ID greater than the last processed ID found.
4.  **Scrapes PubMed:** For each new article, it uses Selenium to navigate to the `link` (expected to be a PubMed URL) and scrapes the Title, Abstract, Authors, and Journal information.
5.  **Classifies with Gemini:** Sends the scraped information to the Google Gemini API (`gemini-1.5-flash` by default) using the prompt defined in `prompts.txt`. The API is asked to return the classification (1 or 2) in a specific JSON format.
6.  **Saves Results:** Appends the classification result (including article ID, link, original grade, category, and timestamp) to the appropriate JSON file in the `output/` directory.
7.  **Resilience:** If the script is stopped and restarted, it will resume processing from where it left off by checking the existing output files. Articles that resulted in scraping or classification errors are skipped on subsequent runs if their ID was recorded (implicitly by being the `last_processed_id` or explicitly added to the `processed_ids` set on error).

## Prerequisites

*   Python 3.8+
*   Google Chrome browser installed
*   Access credentials for:
    *   Supabase Project (URL and **Anon Key** - ensure RLS allows reading `articles` table)
    *   Google AI (Gemini) API Key

## Setup

1.  **Clone the repository (if not already done):**
    ```bash
    # Navigate to your project directory
    cd path/to/your/project
    ```

2.  **Navigate to the script directory:**
    ```bash
    cd backend/determine_category
    ```

3.  **Create and Activate a Virtual Environment (Recommended):**
    ```bash
    python3 -m venv .venv
    # Linux/macOS:
    source .venv/bin/activate
    # Windows (Git Bash):
    # source .venv/Scripts/activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure Environment Variables:**
    *   Create a `.env` file in the `backend/determine_category` directory.
    *   Add your `GOOGLE_API_KEY`, `SUPABASE_URL`, and `SUPABASE_KEY` (anon key) to this file. See the example `.env` content above.

6.  **Create Output Directory:**
    ```bash
    mkdir output
    ```
    *(The script will create this if it doesn't exist, but it's good practice).*

7.  **Review Prompt:**
    *   Check `prompts.txt` to ensure it matches your classification needs.

## Usage

1.  **Activate the virtual environment** (if not already active):
    ```bash
    source .venv/bin/activate
    ```

2.  **Run the script:**
    ```bash
    python determine_category.py
    ```
    *   Optional: Specify a different batch size:
        ```bash
        python determine_category.py --batch-size 100
        ```

The script will log its progress to the console, including which articles are being processed, scraped, classified, and where the results are saved. Errors during scraping or classification will also be logged.

## Output

*   `output/category_1_recommendations.json`: A JSON list containing details of articles classified as Category 1.
*   `output/category_2_classic_articles.json`: A JSON list containing details of articles classified as Category 2.

Each entry in the JSON files will look similar to this:

```json
{
  "id": 12345,
  "link": "https://pubmed.ncbi.nlm.nih.gov/12345678/",
  "classified_category": 1,
  "original_grade": "A",
  "processed_at": "2023-10-27T10:30:00.123456+00:00"
}