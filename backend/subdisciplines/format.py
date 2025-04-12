import os
import json
import sys

# --- Configuration ---
RESULTS_DIR = "gemini-results"
OUTPUT_FILE = "read.txt"

# --- Helper Function to Parse the Raw Response ---
def extract_subdisciplines_from_response(raw_response: str | None) -> list[str] | str:
    """
    Attempts to parse the raw response as JSON and extract sub-disciplines.
    Returns a list of names on success, or a status string on failure/skip.
    """
    if raw_response is None:
        return "[Gemini call failed or blocked]"
    if raw_response.startswith("SKIPPED"):
        return f"[{raw_response}]" # Keep the skip reason
    if raw_response == "Error/Blocked/Skipped": # General failure marker
         return "[Gemini call failed or blocked]"

    extracted_names = []
    try:
        # Attempt to parse the raw response as JSON
        data = json.loads(raw_response)
        if not isinstance(data, dict):
            # Valid JSON, but not the expected dictionary structure
            return "[Invalid JSON structure in response]"

        # Iterate through parent disciplines and extract sub-discipline names
        for parent_discipline, selected_subs in data.items():
            if isinstance(selected_subs, list):
                for sub_name in selected_subs:
                    if isinstance(sub_name, str) and sub_name.strip():
                        extracted_names.append(sub_name.strip())
            # We don't need warnings here, just extraction

        if not extracted_names:
            return "[No sub-disciplines selected in response]"
        else:
            return sorted(extracted_names) # Return sorted list for consistent output

    except json.JSONDecodeError:
        # The raw response was not valid JSON
        return "[Could not parse Gemini response as JSON]"
    except Exception as e:
        # Other unexpected error during parsing
        print(f"  Unexpected error parsing response: {e}")
        return f"[Error parsing response: {e}]"


# --- Main Execution ---
def main():
    print(f"Reading results from directory: '{RESULTS_DIR}'")
    print(f"Writing summary to file: '{OUTPUT_FILE}'")

    if not os.path.isdir(RESULTS_DIR):
        print(f"Error: Results directory '{RESULTS_DIR}' not found.", file=sys.stderr)
        sys.exit(1)

    json_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith(".json")]
    if not json_files:
        print("No .json files found in the results directory.")
        # Create an empty output file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
            outfile.write("No results found.\n")
        sys.exit(0)

    print(f"Found {len(json_files)} result files. Processing...")

    # Sort files numerically by article ID for consistent output order
    json_files.sort(key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else float('inf'))


    processed_count = 0
    error_count = 0

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
            for filename in json_files:
                filepath = os.path.join(RESULTS_DIR, filename)
                try:
                    with open(filepath, "r", encoding="utf-8") as infile:
                        data = json.load(infile)

                    article_id = data.get("article_id", "N/A")
                    link = data.get("link", "[No Link Provided]")
                    raw_response = data.get("gemini_raw_response")

                    # Ensure link is treated as string, handle None
                    link_str = link if link is not None else "[No Link Provided]"

                    # Parse the raw response
                    sub_disciplines_or_status = extract_subdisciplines_from_response(raw_response)

                    # Write formatted output
                    outfile.write(f"Article ID: {article_id}\n")
                    outfile.write(f"Link: {link_str}\n")
                    outfile.write("Sub-Disciplines:\n")

                    if isinstance(sub_disciplines_or_status, list):
                        if sub_disciplines_or_status:
                            for sub_disc in sub_disciplines_or_status:
                                outfile.write(f"  - {sub_disc}\n")
                        else: # Should be caught by specific message now, but belt-and-suspenders
                             outfile.write("  [None selected]\n")
                    else: # It's a status string
                        outfile.write(f"  {sub_disciplines_or_status}\n")

                    outfile.write("---\n") # Separator
                    processed_count += 1

                except json.JSONDecodeError:
                    print(f"Error: Could not decode JSON from file: {filename}", file=sys.stderr)
                    outfile.write(f"File: {filename}\nError: Invalid JSON\n---\n")
                    error_count += 1
                except KeyError as e:
                     print(f"Error: Missing expected key '{e}' in file: {filename}", file=sys.stderr)
                     outfile.write(f"File: {filename}\nError: Missing key '{e}'\n---\n")
                     error_count += 1
                except Exception as e:
                    print(f"Error processing file {filename}: {e}", file=sys.stderr)
                    outfile.write(f"File: {filename}\nError: {e}\n---\n")
                    error_count += 1

    except IOError as e:
        print(f"Error: Could not write to output file '{OUTPUT_FILE}': {e}", file=sys.stderr)
        sys.exit(1)

    print("\n--- Reading Complete ---")
    print(f"Successfully processed: {processed_count} files")
    if error_count > 0:
        print(f"Encountered errors in: {error_count} files")
    print(f"Output written to: '{OUTPUT_FILE}'")

if __name__ == "__main__":
    main()