# Step 4: Link Merging and Cleanup

This final step merges the extracted recommendation links with the main recommendations scraper pipeline, ensuring no duplicates are added and maintaining data integrity across the system.

## What This Step Does

**Script**: `merge_links.js` (Node.js)

This JavaScript script handles the critical integration between the retrieve_recommandations pipeline and the recommendations_scraper pipeline, ensuring seamless data flow.

## Process Overview

### 1. Read New Links
```javascript
const newLinksContent = fs.readFileSync('output_links.txt', 'utf8');
const newLinks = newLinksContent
    .split('\n')
    .map(link => link.trim())
    .filter(link => link.length > 0);
```
- Reads links from `output_links.txt` (created by `extract_link.py`)
- Normalizes links by trimming whitespace
- Filters out empty lines

### 2. Read Existing Links
```javascript
const existingContent = fs.readFileSync('../recommandations_scraper/links.txt', 'utf8');
const existingLinks = existingContent
    .split('\n')
    .map(link => link.trim())
    .filter(link => link.length > 0);
```
- Reads current links from the recommendations scraper pipeline
- Handles case where target file doesn't exist yet
- Creates target directory if needed

### 3. Merge with Duplicate Prevention
```javascript
const allLinksSet = new Set(existingLinks);
newLinks.forEach(link => {
    if (!allLinksSet.has(link)) {
        allLinksSet.add(link);
        addedCount++;
    }
});
```
- Uses JavaScript `Set` to automatically handle duplicates
- Only adds genuinely new links
- Tracks count of added links for reporting

### 4. Write Merged Results
```javascript
const finalLinks = Array.from(allLinksSet);
const finalContent = finalLinks.join('\n') + '\n';
fs.writeFileSync(targetFile, finalContent, 'utf8');
```
- Converts Set back to array
- Writes all links (existing + new) to target file
- Maintains consistent format with trailing newline

### 5. Cleanup
```javascript
fs.unlinkSync('output_links.txt');
```
- Removes temporary `output_links.txt` file
- Keeps workspace clean for next pipeline run

## File Locations

- **Input**: `retrieve_recommandations/output_links.txt`
- **Target**: `recommandations_scraper/links.txt`
- **Cleanup**: Removes input file after successful merge

## Integration Benefits

### Data Integrity
- **No Duplicates**: Ensures each link appears only once
- **Preservation**: Existing links are never lost or modified
- **Validation**: Only processes valid, non-empty links

### Pipeline Coordination
- **Seamless Integration**: Feeds directly into recommendations scraper
- **Automatic Cleanup**: No manual intervention required
- **Progress Tracking**: Reports how many new links were added

## Error Handling

- Validates input file exists before processing
- Creates target directory structure if missing
- Provides detailed error messages for debugging
- Exits gracefully on any failure

## Output Example

```
📖 Found 15 new links to process
📚 Found 42 existing links in target file
➕ Adding 12 unique new links
📊 Total links after merge: 54
✅ Successfully updated ../recommandations_scraper/links.txt
🗑️  Removed output_links.txt
🎉 Link merge completed successfully!
```

This step completes the retrieve_recommandations pipeline and successfully hands off the identified recommendation links to the scraper pipeline for content extraction and processing. 