# Step 3: Link Extraction

This step extracts PubMed links from articles that have been classified as recommendations (Category 1) and saves them to a text file for further processing.

## What This Step Does

**Script**: `extract_link.py`

A simple but essential script that bridges the classification results with the recommendations scraper pipeline by extracting links in the correct format.

## Process Overview

### 1. Read Classification Results
```python
with open('output_new/recommendation_links.json', 'r') as file:
    data = json.load(file)
```
- Loads the JSON file containing links from classified recommendations
- Expects a simple array of PubMed URLs

### 2. Extract Links
```python
with open('output_links.txt', 'w') as output_file:
    for link in data:
        output_file.write(link + '\n')
```
- Iterates through each link in the array
- Writes each link on a separate line
- Simple transformation from JSON array to text file

### 3. Generate Output File
Creates `output_links.txt` containing:
- One PubMed URL per line
- Clean format suitable for automated processing
- No duplicates (inherits uniqueness from classification step)

## Input Requirements

**Expected Input File**: `output_new/recommendation_links.json`

Format:
```json
[
  "https://pubmed.ncbi.nlm.nih.gov/12345678/",
  "https://pubmed.ncbi.nlm.nih.gov/87654321/",
  "https://pubmed.ncbi.nlm.nih.gov/11223344/"
]
```

## Output

**File**: `output_links.txt`

Format:
```
https://pubmed.ncbi.nlm.nih.gov/12345678/
https://pubmed.ncbi.nlm.nih.gov/87654321/
https://pubmed.ncbi.nlm.nih.gov/11223344/
```

## Error Handling

- Script will fail gracefully if input JSON file doesn't exist
- Logs any formatting issues with individual entries
- Ensures output file is created even if input is empty

## Integration

This output file (`output_links.txt`) is consumed by the next step in the pipeline (`merge_links.js`) which merges these links with the main recommendations scraper workflow. 