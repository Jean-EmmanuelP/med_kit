#!/bin/bash

# run_pipeline.sh
# Pipeline for processing medical recommendations

set -e  # Exit on any error

echo "🚀 Starting Medical Recommendations Pipeline"
echo "=============================================="

# Check if we're in the right directory
if [ ! -f "links.txt" ] || [ ! -f "scraper.py" ]; then
    echo "❌ Error: Please run this script from the recommandations directory"
    exit 1
fi

# Check if required files exist
if [ ! -f "prompt.txt" ]; then
    echo "❌ Error: prompt.txt not found"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p output

echo ""
echo "🐍 Step 0: Setting up Python virtual environment"
echo "----------------------------------------------"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip and install requirements
echo "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Virtual environment activated and dependencies installed"

echo ""
echo "📋 Step 1: Running scraper on links.txt"
echo "----------------------------------------"
python scraper.py links.txt --prompt_file prompt.txt

if [ $? -ne 0 ]; then
    echo "❌ Scraper failed. Stopping pipeline."
    exit 1
fi

echo ""
echo "🔗 Step 2: Reorganizing links with check_links.js"
echo "------------------------------------------------"
node check_links.js

if [ $? -ne 0 ]; then
    echo "❌ Link reorganization failed. Stopping pipeline."
    exit 1
fi

echo ""
echo "📤 Step 3: Updating recommendations in database"
echo "----------------------------------------------"
python update_recommandations.py

if [ $? -ne 0 ]; then
    echo "❌ Database update failed. Stopping pipeline."
    exit 1
fi

echo ""
echo "✅ Pipeline completed successfully!"
echo "=================================="
echo ""
echo "📊 Summary:"
echo "- Processed articles are saved in output/ (successfully updated files are deleted)"
echo "- Successful links are appended to successful.txt"
echo "- Failed/error links are written back to links.txt for retry"
echo "- Error links are also saved to error.txt for reference"
echo ""

# Show some stats if files exist
if [ -f "successful.txt" ]; then
    successful_count=$(wc -l < successful.txt 2>/dev/null || echo "0")
    echo "📈 Total successful articles: $successful_count"
fi

if [ -f "links.txt" ]; then
    remaining_count=$(wc -l < links.txt 2>/dev/null || echo "0")
    echo "🔄 Remaining links to process: $remaining_count"
fi

if [ -f "error.txt" ]; then
    error_count=$(wc -l < error.txt 2>/dev/null || echo "0")
    echo "❌ Error links this run: $error_count"
fi

echo ""
echo "💡 Note: Virtual environment is still active. Run 'deactivate' to exit it."
echo "Run the pipeline again to process remaining links in links.txt" 