# Step 3: Database Updates (`update_recommandations.py`)

This script updates the Supabase database with processed medical recommendations and performs automatic cleanup of successfully processed files.

[**← Back to Main Index**](../recommandations_scraper.md)

-   **Input**:
    -   `output/` directory: JSON files containing structured medical recommendations.
    -   Environment variables: `SUPABASE_URL` and `SUPABASE_KEY` for database connection.

-   **Process**:
    1.  **Database Connection**:
        -   Establishes connection to Supabase using environment credentials.
        -   Validates connection before beginning processing.
    
    2.  **Content Processing**:
        -   Iterates through all JSON files in the `output/` directory.
        -   For each file:
            -   Extracts the source URL and recommendation data.
            -   Converts the structured JSON recommendation to Markdown format using a recursive formatting function.
            -   Preserves the hierarchical structure with proper heading levels.
    
    3.  **Database Updates**:
        -   Updates the `articles` table in Supabase:
            -   Sets `is_recommandation = true` to mark the article as a processed recommendation.
            -   Updates the `content` field with the formatted Markdown text.
            -   Uses the source URL to match existing articles in the database.
    
    4.  **Automatic Cleanup**:
        -   **Critical Feature**: After each successful database update, the corresponding JSON file is automatically deleted from the `output/` directory.
        -   This prevents reprocessing of the same content in future pipeline runs.
        -   Provides logging for both successful updates and file deletions.

-   **Output**:
    -   **Updated Database**: Articles in Supabase are marked and populated with recommendation content.
    -   **Cleaned Filesystem**: Successfully processed JSON files are removed from `output/`.
    -   **Processing Logs**: Detailed logs of successful updates, failures, and cleanup operations.

-   **Error Handling**:
    -   Continues processing remaining files even if individual updates fail.
    -   Provides detailed error logging for debugging failed database operations.
    -   Only deletes files after confirmed successful database updates.
    -   Maintains file integrity by keeping files that failed to update for retry.

-   **Key Features**:
    -   **Idempotent Operations**: Safe to run multiple times without duplicating data.
    -   **Automatic Cleanup**: Prevents accumulation of processed files.
    -   **Comprehensive Logging**: Tracks all operations for monitoring and debugging.
    -   **Fault Tolerance**: Gracefully handles database connection issues and malformed data. 