const fs = require('fs');
const path = require('path');

// File paths
const inputFile = 'output_links.txt';
const targetFile = '../recommandations_scraper/links.txt';

console.log('🔗 Starting link merge process...');

try {
    // Step 1: Read new links from output_links.txt
    if (!fs.existsSync(inputFile)) {
        console.error(`❌ Error: ${inputFile} does not exist`);
        process.exit(1);
    }
    
    const newLinksContent = fs.readFileSync(inputFile, 'utf8');
    const newLinks = newLinksContent
        .split('\n')
        .map(link => link.trim())
        .filter(link => link.length > 0); // Remove empty lines
    
    console.log(`📖 Found ${newLinks.length} new links to process`);
    
    // Step 2: Read existing links from target file (if it exists)
    let existingLinks = [];
    if (fs.existsSync(targetFile)) {
        const existingContent = fs.readFileSync(targetFile, 'utf8');
        existingLinks = existingContent
            .split('\n')
            .map(link => link.trim())
            .filter(link => link.length > 0);
        console.log(`📚 Found ${existingLinks.length} existing links in target file`);
    } else {
        console.log('📄 Target file does not exist, will create new one');
        // Ensure the directory exists
        const targetDir = path.dirname(targetFile);
        if (!fs.existsSync(targetDir)) {
            fs.mkdirSync(targetDir, { recursive: true });
        }
    }
    
    // Step 3: Create a Set for unique links (existing + new)
    const allLinksSet = new Set(existingLinks);
    let addedCount = 0;
    
    // Add new links (only unique ones will be added to Set)
    newLinks.forEach(link => {
        if (!allLinksSet.has(link)) {
            allLinksSet.add(link);
            addedCount++;
        }
    });
    
    console.log(`➕ Adding ${addedCount} unique new links`);
    console.log(`📊 Total links after merge: ${allLinksSet.size}`);
    
    // Step 4: Convert Set back to array and write to target file
    const finalLinks = Array.from(allLinksSet);
    const finalContent = finalLinks.join('\n') + '\n'; // Add final newline
    
    fs.writeFileSync(targetFile, finalContent, 'utf8');
    console.log(`✅ Successfully updated ${targetFile}`);
    
    // Step 5: Remove the input file as requested
    fs.unlinkSync(inputFile);
    console.log(`🗑️  Removed ${inputFile}`);
    
    console.log('🎉 Link merge completed successfully!');
    
} catch (error) {
    console.error('❌ Error during link merge:', error.message);
    process.exit(1);
} 