# Recommendations Scraper Pipeline Documentation

This document outlines the automated recommendations processing pipeline orchestrated by `run_pipeline.sh`. The pipeline's primary goal is to scrape medical recommendations from PubMed articles, generate structured summaries using AI, and update them in the Supabase database.

## Overall Workflow

The main script is the master orchestrator for the entire workflow. It handles environment setup, sequential execution of processing steps, and intelligent error handling for captcha detection and content validation.

*   [**Read more about the Overall Workflow (`run_pipeline.sh`)**](./recommandations_scraper/00_run_pipeline.md)

## Pipeline Steps

The pipeline is composed of three main steps, each designed to handle errors gracefully and ensure only high-quality medical content is processed.

1.  [**Step 1: Scraping PubMed Recommendations**](./recommandations_scraper/01_scrape_recommendations.md)
    *   *Extracts full-text medical recommendations from PubMed URLs with captcha detection and content validation.*

2.  [**Step 2: Link Organization and Error Handling**](./recommandations_scraper/02_organize_links.md)
    *   *Reorganizes processed and failed links, preparing for retry cycles and maintaining processing state.*

3.  [**Step 3: Database Updates and Cleanup**](./recommandations_scraper/03_update_database.md)
    *   *Updates the Supabase database with structured recommendations and cleans up processed files.*

## Key Features

- **🔍 Smart Error Detection**: Automatically detects and skips captcha pages, error pages, and non-medical content
- **🔄 Retry Logic**: Failed links are automatically queued for retry in subsequent runs
- **🧹 Automatic Cleanup**: Successfully processed files are automatically removed to prevent reprocessing
- **📊 Progress Tracking**: Maintains separate files for successful and failed processing attempts
- **🐍 Environment Management**: Automated Python virtual environment setup and dependency management

---
*This documentation is split into multiple files. You can `Ctrl+Click` (or `Cmd+Click` on Mac) on the links above to navigate between sections in VS Code.* 