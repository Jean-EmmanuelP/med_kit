# Step 1: Environment Setup and Dependencies

This step handles the creation and configuration of the Python environment needed for AI-powered article classification.

## What This Step Does

The pipeline begins by setting up a clean, isolated Python environment to ensure consistent execution across different systems.

### Virtual Environment Creation
```bash
python3 -m venv .venv
source .venv/bin/activate
```

- Creates a new virtual environment in the `.venv` directory
- Activates the environment to isolate dependencies
- Ensures consistent package versions across runs

### Dependency Installation
```bash
pip install -r requirements.txt
```

Installs the following key dependencies:
- **`python-dotenv`**: Environment variable management
- **`supabase`**: Database connectivity
- **`google-generativeai`**: Google Gemini AI integration
- **`selenium`**: Web scraping capabilities
- **`webdriver-manager`**: Automatic browser driver management
- **`requests`**: HTTP requests for PubMed scraping
- **`beautifulsoup4`**: HTML parsing
- **`readability-lxml`**: Content extraction

## Environment Variables Required

The pipeline expects a `.env` file with:
```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
GOOGLE_API_KEY=your_google_ai_api_key
```

## Error Handling

- Stops execution if virtual environment creation fails
- Validates that all dependencies install successfully
- Ensures Python 3.8+ compatibility

## Output

A fully configured Python environment ready for:
- Database connectivity to Supabase
- AI classification using Google Gemini
- Web scraping of PubMed articles 