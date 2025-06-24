# EvidenceAlerts Data Pipeline Documentation

This document outlines the automated data processing pipeline orchestrated by `run_pipeline.sh`. The pipeline's primary goal is to scrape medical articles, enrich them using AI, and load them into a Supabase database.

## Overall Workflow

The main script is the master orchestrator for the entire workflow. It handles environment setup, sequential execution of processing steps, and cleanup of temporary data.

*   [**Read more about the Overall Workflow (`run_pipeline.sh`)**](./pipeline/00_run_pipeline.md)

## Pipeline Steps

The pipeline is composed of five distinct steps, each handled by a dedicated Python script.

1.  [**Step 1: Scraping Articles**](./pipeline/01_scrape_evidence.md)
    *   *Gathers raw article data from EvidenceAlerts and PubMed.*

2.  [**Step 2: Generating Summaries**](./pipeline/02_generate_summaries.md)
    *   *Uses AI to translate titles and generate structured summaries in French.*

3.  [**Step 3: Exporting to Database**](./pipeline/03_export_to_db.md)
    *   *Loads the enriched articles into the Supabase database, avoiding duplicates.*

4.  [**Step 4: Reclassifying Articles**](./pipeline/04_reclassify_articles.md)
    *   *Performs detailed, fine-grained sub-discipline classification for new articles.*

5.  [**Step 5: Grading Articles**](./pipeline/05_grade_articles.md)
    *   *Evaluates the level of evidence for each article and assigns a grade.*

---
*This documentation is split into multiple files. You can `Ctrl+Click` (or `Cmd+Click` on Mac) on the links above to navigate between sections in VS Code.*