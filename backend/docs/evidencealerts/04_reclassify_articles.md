# Step 4: Article Classification (`classification_articles/reclassify_articles.py`)

This script performs a more detailed, fine-grained classification of articles that have been added to the database, assigning them to specific sub-disciplines.

[**← Back to Main Index**](../pipeline.md)

-   **Input**:
    -   Operates directly on the Supabase database. It queries for articles with a `reclassification_status` of `pending` or `error`.
    -   Supabase and Google API credentials from the `.env` file.

-   **Process**:
    1.  Fetches a batch of articles marked for reclassification.
    2.  For each article, it retrieves its title, content, and current classifications from the database.
    3.  It uses a sophisticated, asynchronous Gemini API workflow with a double-check and arbitration mechanism:
        -   Two parallel API calls are made to classify the article against a master list of disciplines and sub-disciplines.
        -   If the results differ, a third "arbitrator" call is made to determine the final, correct classification.
    4.  The script compares the new classification with the existing one and calculates the necessary database changes (records to add or delete).
    5.  It updates the `article_disciplines` and `article_sub_disciplines` tables with the corrected data.

-   **Output**:
    -   Updates records in the `article_disciplines` and `article_sub_disciplines` tables.
    -   Updates the `reclassification_status` of the article to `done` or `error`.
    -   Saves diagnostic JSON files to the `result_arbitration/` directory for debugging.