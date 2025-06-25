# Step 2: Link Organization (`check_links.js`)

This Node.js script manages the processing state by organizing successful and failed links, enabling intelligent retry logic for the pipeline.

[**← Back to Main Index**](../recommandations_scraper.md)

-   **Input**:
    -   `links.txt`: URLs that were attempted to be processed in the current run.
    -   `output/` directory: JSON files containing successfully processed recommendations.
    -   `successful.txt` (existing): Previously successful URLs from past runs.

-   **Process**:
    1.  **Link Verification**:
        -   Reads all URLs from `links.txt` that were targeted for processing.
        -   Scans all JSON files in the `output/` directory to identify which URLs were successfully processed.
        -   Compares the two sets to determine successful vs. failed processing attempts.
    
    2.  **State Management**:
        -   **Successful Links**: Appends newly successful URLs to `successful.txt` (preserving historical data).
        -   **Failed Links**: Writes failed URLs back to `links.txt` for retry in the next pipeline run.
        -   **Error Tracking**: Also saves failed URLs to `error.txt` for reference and debugging.

    3.  **Intelligent Retry Preparation**:
        -   The pipeline becomes self-healing: failed links are automatically queued for retry.
        -   No manual intervention required to identify which URLs need reprocessing.
        -   Prevents reprocessing of already successful URLs.

-   **Output**:
    -   **Updated `links.txt`**: Contains only URLs that need to be retried.
    -   **Appended `successful.txt`**: Historical record of all successfully processed URLs.
    -   **Updated `error.txt`**: Reference file showing URLs that failed in the current run.

-   **Key Features**:
    -   **Non-destructive Updates**: Never overwrites existing successful.txt data.
    -   **Comprehensive Logging**: Provides detailed statistics on processing results.
    -   **Fault Tolerance**: Handles missing files and malformed JSON gracefully.
    -   **Retry Logic**: Automatically prepares the pipeline for subsequent runs with only failed URLs. 