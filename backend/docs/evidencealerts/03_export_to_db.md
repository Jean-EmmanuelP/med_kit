# Step 3: Database Export (`scrape_evidence/export_to_db.py`)

This script is responsible for populating the production database with the newly processed and summarized articles.

[**← Back to Main Index**](../pipeline.md)

-   **Input**:
    -   The `summaries/YYYYMMDD/` directory containing the individual, processed JSON files from Step 2.
    -   Supabase credentials, loaded from the `.env` file.

-   **Process**:
    1.  Establishes a connection to the Supabase database.
    2.  Loads all existing medical disciplines from the `disciplines` table into a local cache for efficient ID lookups.
    3.  Iterates through each JSON file in the input directory.
    4.  For each article, it first checks if an article with the same `link` already exists in the `articles` table to prevent duplicates.
    5.  If the article is new, it inserts the main data (title, cleaned content, journal, etc.) into the `articles` table.
    6.  After a successful insertion, it uses the new article's ID to create associations in the `article_disciplines` table, linking the article to its relevant medical fields based on the categories in the JSON file.

-   **Output**:
    -   New records are created in the Supabase `articles` and `article_disciplines` tables.