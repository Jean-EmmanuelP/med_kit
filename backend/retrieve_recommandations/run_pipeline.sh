#!/bin/bash

# run_pipeline.sh - Pipeline to classify articles and merge links
set -e  # Exit on any error

echo "🚀 Starting Retrieve Recommendations Pipeline..."

# Step 1: Create and activate virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Step 2: Install requirements
echo "📥 Installing requirements..."
pip install -r requirements.txt

# Step 3: Run determine_category.py
echo "🤖 Running article classification..."
python determine_category.py

# Step 4: Run extract_link.py
echo "🔗 Extracting links..."
python extract_link.py

# Step 5: Check if output_links.txt was created
if [ ! -f "output_links.txt" ]; then
    echo "❌ Error: output_links.txt was not created by extract_link.py"
    exit 1
fi

# Step 6: Run the JavaScript link merger
echo "🔄 Merging links to recommandations_scraper..."
node merge_links.js

echo "✅ Pipeline completed successfully!"

# Deactivate virtual environment
deactivate 