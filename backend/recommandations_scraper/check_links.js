// check_links.js

const fs = require('fs/promises');
const path = require('path');

// --- Configuration ---
const OUTPUT_DIR = 'output';
const LINKS_FILE = 'links.txt';
const SUCCESS_FILE = 'successful.txt';
const ERROR_FILE = 'error.txt';
// -------------------

async function main() {
  console.log('Starting link verification process...');

  try {
    // 1. Read the list of links to check from links.txt
    const linksFileContent = await fs.readFile(LINKS_FILE, 'utf8');
    // Create a Set for efficient lookups. Filter out any empty lines.
    const targetLinks = new Set(linksFileContent.split('\n').filter(link => link.trim() !== ''));
    if (targetLinks.size === 0) {
      console.log('Warning: links.txt is empty or contains no valid links.');
      return;
    }
    console.log(`Found ${targetLinks.size} links to verify in ${LINKS_FILE}.`);

    // 2. Go through every .json file in the output directory and collect their links
    const filesInDir = await fs.readdir(OUTPUT_DIR);
    const jsonFiles = filesInDir.filter(file => path.extname(file).toLowerCase() === '.json');

    if (jsonFiles.length === 0) {
        console.error(`Error: No .json files found in the '${OUTPUT_DIR}' directory.`);
        // If no JSONs are found, all target links are considered 'not found'.
        await fs.writeFile(LINKS_FILE, Array.from(targetLinks).join('\n')); // Write back to links.txt for retry
        console.log(`Wrote all ${targetLinks.size} links back to ${LINKS_FILE} for retry.`);
        return;
    }

    const foundJsonLinks = new Set();
    for (const jsonFile of jsonFiles) {
      const filePath = path.join(OUTPUT_DIR, jsonFile);
      try {
        const fileContent = await fs.readFile(filePath, 'utf8');
        const data = JSON.parse(fileContent);
        if (data && data.link) {
          foundJsonLinks.add(data.link.trim());
        } else {
          console.warn(`Warning: No 'link' key found in ${jsonFile}.`);
        }
      } catch (err) {
        console.error(`Error reading or parsing ${jsonFile}:`, err.message);
      }
    }
    console.log(`Found ${foundJsonLinks.size} unique links across ${jsonFiles.length} JSON files.`);

    // 3. Compare the two sets of links and separate them
    const successfulLinks = [];
    const errorLinks = [];

    for (const targetLink of targetLinks) {
      if (foundJsonLinks.has(targetLink)) {
        successfulLinks.push(targetLink);
      } else {
        errorLinks.push(targetLink);
      }
    }

    // 4. Write the results to the output files
    // Append successful links to existing successful.txt instead of overwriting
    if (successfulLinks.length > 0) {
      try {
        // Check if successful.txt exists and read existing content
        let existingSuccessful = '';
        try {
          existingSuccessful = await fs.readFile(SUCCESS_FILE, 'utf8');
          if (existingSuccessful.trim()) {
            existingSuccessful += '\n'; // Add newline if file has content
          }
        } catch (err) {
          // File doesn't exist, which is fine
          existingSuccessful = '';
        }
        
        // Append new successful links
        await fs.writeFile(SUCCESS_FILE, existingSuccessful + successfulLinks.join('\n'));
        console.log(`✅ ${successfulLinks.length} successful links appended to ${SUCCESS_FILE}`);
      } catch (err) {
        console.error(`Error appending to ${SUCCESS_FILE}:`, err.message);
      }
    }

    // Write error links back to links.txt for retry in next run
    await fs.writeFile(LINKS_FILE, errorLinks.join('\n'));
    
    // Also write to error.txt for reference
    await fs.writeFile(ERROR_FILE, errorLinks.join('\n'));

    console.log('\n--- Verification Complete ---');
    console.log(`✅ ${successfulLinks.length} successful links appended to ${SUCCESS_FILE}`);
    console.log(`🔄 ${errorLinks.length} error links written back to ${LINKS_FILE} for retry`);
    console.log(`❌ ${errorLinks.length} error links also saved to ${ERROR_FILE} for reference`);
    console.log('---------------------------');

  } catch (error) {
    if (error.code === 'ENOENT') {
        console.error(`Error: A required file or directory was not found.`);
        console.error(`Please make sure '${OUTPUT_DIR}/' and '${LINKS_FILE}' exist.`);
    } else {
        console.error('An unexpected error occurred:', error);
    }
  }
}

// Run the main function
main();