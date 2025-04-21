#!/usr/bin/env bash

# --- Configuration ---

# Define the names of directories or files to exclude.
# Add any other names you want to skip.
# Note: This matches the base name, not the full path.
EXCLUDE_NAMES=(
    ".git"          # Exclude the git directory itself
    ".venv"         # Exclude python virtual environments
    "__pycache__"   # Exclude python cache directories
    "node_modules"  # Exclude node.js dependencies
    "vendor"        # Exclude composer dependencies (PHP)
    "build"         # Exclude common build output directories
    "dist"          # Exclude common distribution directories
    "target"        # Exclude common build output (Java/Rust)
    "*.pyc"         # Exclude python compiled files
    "*.class"       # Exclude java compiled files
    "*.o"           # Exclude compiled object files
    "*.so"          # Exclude shared object files
    "*.dll"         # Exclude dynamic link libraries
    "*.exe"         # Exclude executable files (Windows)
    "context.txt"   # Exclude the output file itself!
    ".gitignore"   # Exclude git ignore files
    ".dockerignore" # Exclude docker ignore files
    "static"
    ".svelte-kit"
    "node_modules"
    "dist"
    "build"
    "out"
    "bun.lockb"
    "bun.lock"
    ".DS_Store"
    # Add more patterns or names as needed
)

# Output file name
OUTPUT_FILE="context.txt"

# Separator strings
PATH_MARKER="--- File Path ---"
END_MARKER="--- End of File ---" # Optional: Helps delimit file content visually

# --- Script Logic ---

# Check if a path argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <path>"
  echo "  <path>: The directory path (relative to the script) to scan recursively."
  exit 1
fi

TARGET_DIR="$1"

# Check if the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory '$TARGET_DIR' not found."
  exit 1
fi

# Clear the output file or create it if it doesn't exist
> "$OUTPUT_FILE"
echo "Cleared/Created $OUTPUT_FILE"

# --- Build the find command arguments ---
# Start with the target directory
find_args=("$TARGET_DIR")

# Add exclusion logic
# We need to construct something like: \( -name ".git" -o -name ".venv" ... \) -prune
if [ ${#EXCLUDE_NAMES[@]} -gt 0 ]; then
    find_args+=(\() # Start grouping for -prune
    first_exclude=true
    for name in "${EXCLUDE_NAMES[@]}"; do
        if [ "$first_exclude" = true ]; then
            first_exclude=false
        else
            find_args+=(-o) # Or operator between names
        fi
        # Use -name for exact matches or patterns, -path for path patterns
        if [[ "$name" == *"*"* ]]; then
             # Use -path for wildcard patterns as -name only checks the basename
             # Make sure pattern matches relative path from the starting point
             find_args+=(-path "*/$name")
        else
            # Use -name for exact directory/file names
             find_args+=(-name "$name")
        fi
    done
    find_args+=(\)) # End grouping
    find_args+=(-prune) # Prune these directories/files (don't descend/process)
    find_args+=(-o) # Or, process other things
fi

# Add the primary action: find files (-type f) and print them null-separated
find_args+=(-type f -print0)

echo "Scanning directory '$TARGET_DIR'..."
echo "Excluding: ${EXCLUDE_NAMES[*]}"
echo "Outputting to '$OUTPUT_FILE'..."

# Use process substitution and a while loop for safe file handling (handles spaces, newlines)
# find "${find_args[@]}" exits with non-zero if no files are found matching criteria *after* prune,
# which is often the case, so we can't reliably check its exit code here.
# Instead, we check if any files were processed.
file_count=0
while IFS= read -r -d $'\0' file; do
    # Check if file still exists and is readable (optional, but safer)
    if [ -f "$file" ] && [ -r "$file" ]; then
        echo "Processing: $file"
        # Append path marker and path to the output file
        echo "$PATH_MARKER" >> "$OUTPUT_FILE"
        echo "$file" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE" # Add a blank line for separation

        # Append file content
        cat "$file" >> "$OUTPUT_FILE"

        # Append end marker and newlines for clear separation
        echo "" >> "$OUTPUT_FILE" # Newline after content
        echo "$END_MARKER" >> "$OUTPUT_FILE"
        echo "" >> "$OUTPUT_FILE" # Blank line after marker
        ((file_count++))
    else
        echo "Warning: Skipping unreadable or non-existent file: $file"
    fi
done < <(find "${find_args[@]}") # Use process substitution <(...)

# Check the number of files processed
if [ $file_count -eq 0 ]; then
     echo "Warning: No files found or processed in '$TARGET_DIR' (check exclusions?). '$OUTPUT_FILE' might be empty or only contain initial message."
     # Optionally remove the empty file:
     # if [ ! -s "$OUTPUT_FILE" ]; then rm "$OUTPUT_FILE"; fi
else
    echo "Done. Processed $file_count files."
    echo "Context saved to '$OUTPUT_FILE'."
fi

exit 0