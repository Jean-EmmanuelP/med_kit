# Overall Workflow (`run_pipeline.sh`)

The `run_pipeline.sh` script is the main orchestrator for the entire article classification and link extraction workflow. It coordinates all components to create a seamless pipeline from database articles to processed recommendation links.

## Script Overview

**Location**: `backend/retrieve_recommandations/run_pipeline.sh`

**Purpose**: Automate the complete process of classifying articles in the database using AI and feeding recommendation links to the scraper pipeline.

## Workflow Steps

### 1. Environment Preparation
- Creates a fresh Python virtual environment (`.venv`)
- Activates the virtual environment
- Installs all required dependencies from `requirements.txt`

### 2. AI Classification
- Executes `determine_category.py` 
- Connects to Supabase database
- Uses Google Gemini AI to classify articles as recommendations vs research
- Saves classification results to JSON files

### 3. Link Extraction 
- Runs `extract_link.py`
- Reads classified recommendation articles
- Extracts PubMed links to `output_links.txt`

### 4. Link Integration
- Executes `merge_links.js` (Node.js script)
- Reads new links from `output_links.txt`
- Merges with existing `../recommandations_scraper/links.txt`
- Ensures no duplicate links are added
- Removes temporary `output_links.txt` file

### 5. Cleanup
- Deactivates the virtual environment
- Displays completion status

## Error Handling

The script uses `set -e` to ensure it stops on any error, preventing partial execution that could lead to inconsistent states.

## Usage

```bash
cd backend/retrieve_recommandations
./run_pipeline.sh
```

## Prerequisites

- Python 3.8+
- Node.js
- Valid `.env` file with Supabase and Google AI credentials
- Articles in the Supabase database to classify 