# Step 2: Summarization (`scrape_evidence/generate_summaries.py`)

This script enriches the raw data by using a Large Language Model (LLM) to generate high-quality summaries and translations, preparing the content for the end-user.

[**← Back to Main Index**](../pipeline.md)

-   **Input**:
    -   The `data/YYYYMMDD/data.json` file generated in Step 1.
    -   A Google API Key for the Gemini model, loaded from the `.env` file.

-   **Process**:
    1.  Reads the `data.json` file.
    2.  For each article in the file, it makes a call to the Google Gemini API.
    3.  The prompt instructs the model to perform two tasks based on the article's English title and abstract:
        -   Translate the title into French.
        -   Generate a structured summary in French, broken down into four key sections: `contexte`, `methodologie`, `resultats`, and `impact_clinique`.
    4.  The script formats the AI's response, along with other metadata (journal, categories, link), into a new JSON structure suitable for direct import into the database.

-   **Output**:
    -   A series of individual JSON files, one for each article, saved in the `summaries/YYYYMMDD/` directory. Each file is named using the article's ID (e.g., `37123456.json`).