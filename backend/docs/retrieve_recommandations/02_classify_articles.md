# Step 2: Article Classification with AI

This step uses Google Gemini AI to intelligently classify medical articles from the Supabase database into two categories: official recommendations and classic research articles.

## What This Step Does

**Script**: `determine_category.py`

The classification process analyzes article metadata (title, authors, journal, abstract) scraped from PubMed to determine if an article represents:

### Category 1: Official Recommendation/Guideline
- Documents from scientific bodies, societies, or official groups
- Contains formal recommendations or consensus statements
- Examples: "AHA Guidelines for...", "European Society Consensus on..."

### Category 2: Classic Scientific Article  
- Research papers from individual research teams
- Clinical studies, reviews, meta-analyses
- Focus on presenting research methodology and results

## AI Classification Process

### 1. Database Connection
- Connects to Supabase using credentials from `.env`
- Queries the `articles` table for unprocessed entries
- Processes articles in configurable batches (default: 50)

### 2. PubMed Data Scraping
For each article:
- Navigates to the PubMed URL using requests/BeautifulSoup
- Extracts metadata: title, abstract, authors, journal
- Handles various PubMed page formats and selectors

### 3. AI Classification
- Sends scraped metadata to Google Gemini AI (`gemini-2.0-flash`)
- Uses a detailed French prompt from `prompts.txt`
- Requests structured JSON response with category (1 or 2)
- Implements retry logic for API failures

### 4. Result Storage
Classifications are saved to JSON files in `output_new/`:
- `recommendation_links.json`: Simple array of PubMed links for Category 1 articles (recommendations)

## Key Features

- **Resume Capability**: Tracks processed articles to avoid reprocessing
- **Error Resilience**: Continues processing if individual articles fail
- **Rate Limiting**: Respects API limits with built-in delays
- **Detailed Logging**: Comprehensive logging for debugging and monitoring

## Output Files

- `output_new/recommendation_links.json`: Simple JSON array containing PubMed links of identified recommendations
- Logs classification decisions and any errors encountered

**Example Output Format**:
```json
[
  "https://pubmed.ncbi.nlm.nih.gov/12345678/",
  "https://pubmed.ncbi.nlm.nih.gov/87654321/",
  "https://pubmed.ncbi.nlm.nih.gov/11223344/"
]
```

## Configuration

- **Batch Size**: 50 articles per database query
- **API Model**: `gemini-2.0-flash`
- **Retry Logic**: 3 attempts with 20-second delays
- **Request Timeout**: 25 seconds for PubMed scraping 