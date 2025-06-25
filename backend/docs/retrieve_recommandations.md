# Retrieve Recommendations Pipeline Documentation

This document outlines the automated article classification pipeline orchestrated by `run_pipeline.sh`. The pipeline's primary goal is to classify medical articles as recommendations vs classic research articles using AI, extract their links, and merge them with the recommendations scraper workflow.

## Overall Workflow

The main script is the master orchestrator for the entire workflow. It handles environment setup, sequential execution of classification steps, and automatic link merging with duplicate prevention.

*   [**Read more about the Overall Workflow (`run_pipeline.sh`)**](./retrieve_recommandations/00_run_pipeline.md)

## Pipeline Steps

The pipeline is composed of four main steps, each designed to handle the article classification and link extraction workflow efficiently.

1.  [**Step 1: Environment Setup and Dependencies**](./retrieve_recommandations/01_environment_setup.md)
    *   *Creates virtual environment and installs required Python packages for AI classification.*

2.  [**Step 2: Article Classification with AI**](./retrieve_recommandations/02_classify_articles.md)
    *   *Uses Google Gemini AI to classify articles from Supabase database as recommendations or classic research.*

3.  [**Step 3: Link Extraction**](./retrieve_recommandations/03_extract_links.md)
    *   *Extracts PubMed links from classified recommendation articles into a text file.*

4.  [**Step 4: Link Merging and Cleanup**](./retrieve_recommandations/04_merge_links.md)
    *   *Merges extracted links with the recommendations scraper pipeline, ensuring no duplicates.*

## Key Features

- **🤖 AI-Powered Classification**: Uses Google Gemini AI to intelligently distinguish between official recommendations and research articles
- **🔗 Smart Link Management**: Automatically extracts and merges links without duplicates
- **🔄 Database Integration**: Seamlessly integrates with existing Supabase database workflows
- **🧹 Automatic Cleanup**: Removes temporary files after successful processing
- **🐍 Environment Management**: Automated Python virtual environment setup and dependency management
- **⚡ Pipeline Integration**: Designed to feed directly into the recommendations scraper workflow

## Integration with Other Pipelines

This pipeline acts as a **feeder** for the recommendations scraper pipeline:
- Classifies articles in the database to identify recommendations
- Extracts links from identified recommendations
- Adds unique links to the recommendations scraper's processing queue
- Maintains data integrity by preventing duplicate processing

---
*This documentation is split into multiple files. You can `Ctrl+Click` (or `Cmd+Click` on Mac) on the links above to navigate between sections in VS Code.* 