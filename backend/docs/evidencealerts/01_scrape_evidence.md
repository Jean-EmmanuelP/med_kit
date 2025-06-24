# Step 1: Scraping (`scrape_evidence/scrape_evidencealerts.py`)

This script is responsible for gathering the initial raw data by automating web interactions.

[**← Back to Main Index**](../pipeline.md)

-   **Input**:
    -   Hardcoded login credentials for `www.evidencealerts.com`.

-   **Process**:
    1.  Uses a Selenium WebDriver to automate a Chrome browser.
    2.  Logs into the EvidenceAlerts website.
    3.  Navigates to the "Alerted Articles" page and extracts the URLs for all new articles.
    4.  For each article URL, the script performs a sub-process:
        -   It opens the article's detail page on EvidenceAlerts.
        -   It clicks the "View on PubMed" link, which opens a new browser tab.
        -   From the PubMed page, it extracts key metadata: Title, Journal, Publication Date, and DOI.
        -   From the EvidenceAlerts page, it extracts the article's abstract and the rated clinical categories (e.g., "Cardiology", "Family Medicine").
        -   It translates the English categories into their French equivalents using a predefined internal dictionary.
    5.  All collected data is aggregated into a single list of article objects.

-   **Output**:
    -   A single JSON file located at `data/YYYYMMDD/data.json`. This file contains an array of all the articles scraped during the run, with their associated metadata, abstract, and categories.