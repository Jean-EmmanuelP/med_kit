# Step 1: Scraping PubMed Recommendations (`scraper.py`)

This script is responsible for extracting full-text medical recommendations from PubMed URLs with advanced error detection and content validation.

[**← Back to Main Index**](../recommandations_scraper.md)

-   **Input**:
    -   `links.txt`: A text file containing PubMed URLs to process (one per line).
    -   `prompt.txt`: AI prompt template for generating structured summaries.
    -   Environment variables: `GOOGLE_API_KEY` for Gemini AI integration.

-   **Process**:
    1.  **Environment Setup**: Validates API keys and required files.
    2.  **Stealth Web Scraping**: Uses Selenium with stealth mode to avoid detection:
        -   Sets up a headed Chrome browser with anti-detection measures.
        -   Simulates human-like scrolling and interaction patterns.
        -   Implements random delays to mimic natural browsing behavior.
    3.  **Content Extraction**:
        -   For each PubMed URL, finds and follows full-text links.
        -   Extracts article content from the target pages.
        -   **Smart Error Detection**:
            -   Detects captcha pages using keywords like "captcha", "verify you are human", "cloudflare".
            -   Validates content length (minimum 100 characters).
            -   Identifies error pages ("404 error", "access denied", "service unavailable").
    4.  **AI Processing**:
        -   Sends extracted content to Gemini AI for structured summarization.
        -   The AI prompt includes error detection instructions to identify non-medical content.
        -   If the AI detects errors or captcha content, the processing is skipped.
    5.  **Quality Control**: Only saves content that passes all validation checks.

-   **Output**:
    -   JSON files in the `output/` directory, each containing:
        -   Structured medical recommendation summary in French.
        -   Original source URL for tracking.
        -   Hierarchical content organization with emojis for visual clarity.

-   **Error Handling**:
    -   Skips and reports captcha pages, error pages, and invalid content.
    -   Continues processing remaining URLs even if individual URLs fail.
    -   Provides detailed logging of all processing attempts and failures. 