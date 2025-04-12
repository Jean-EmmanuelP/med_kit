import os
import argparse
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- Argument Parsing ---
def setup_arg_parser():
    """Sets up the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Populate the sub_disciplines table from a text file for a given parent discipline."
    )
    parser.add_argument(
        "discipline_name",
        type=str,
        help="The exact name of the parent discipline as it appears in the 'disciplines' table.",
    )
    parser.add_argument(
        "filepath",
        type=str,
        help="Path to the .txt file containing sub-discipline names (one per line).",
    )
    return parser

# --- Database Interaction ---
def get_discipline_id(supabase: Client, discipline_name: str) -> int | None:
    """Fetches the ID of a discipline by its name."""
    try:
        response = (
            supabase.table("disciplines")
            .select("id")
            .eq("name", discipline_name)
            .limit(1) # Ensure we only get one if names happen to not be unique (though they should be)
            .execute()
        )
        if response.data:
            return response.data[0]["id"]
        else:
            print(f"Error: Discipline '{discipline_name}' not found in the database.", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error querying discipline ID for '{discipline_name}': {e}", file=sys.stderr)
        return None

def insert_sub_discipline(supabase: Client, sub_discipline_name: str, parent_discipline_id: int):
    """Inserts a single sub-discipline into the database."""
    try:
        data_to_insert = {
            "name": sub_discipline_name,
            "discipline_id": parent_discipline_id,
        }
        response = supabase.table("sub_disciplines").insert(data_to_insert).execute()

        if response.data:
            print(f"  Successfully inserted sub-discipline: '{sub_discipline_name}' (ID: {response.data[0]['id']})")
        else:
            # Check for specific errors, like unique constraint violation
            if response.error and "duplicate key value violates unique constraint" in response.error.message:
                 print(f"  Warning: Sub-discipline '{sub_discipline_name}' already exists for this discipline. Skipping.")
            else:
                 print(f"  Error inserting sub-discipline '{sub_discipline_name}': {response.error}", file=sys.stderr)

    except Exception as e:
        # Catch potential exceptions from the Supabase client itself
        print(f"  Exception during insert for '{sub_discipline_name}': {e}", file=sys.stderr)


# --- File Processing ---
def read_subdisciplines_from_file(filepath: str) -> list[str] | None:
    """Reads sub-discipline names from a file, one per line."""
    if not os.path.exists(filepath):
        print(f"Error: File not found at '{filepath}'", file=sys.stderr)
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            # Read lines, strip whitespace, filter out empty lines
            sub_disciplines = [line.strip() for line in f if line.strip()]
        return sub_disciplines
    except Exception as e:
        print(f"Error reading file '{filepath}': {e}", file=sys.stderr)
        return None

# --- Main Execution ---
def main():
    parser = setup_arg_parser()
    args = parser.parse_args()

    discipline_name = args.discipline_name
    filepath = args.filepath

    print("--- Starting Sub-discipline Population ---")
    print(f"Parent Discipline: {discipline_name}")
    print(f"Input File: {filepath}")

    # Validate Supabase credentials
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Error: SUPABASE_URL and SUPABASE_KEY environment variables must be set.", file=sys.stderr)
        sys.exit(1)

    # Initialize Supabase client
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error creating Supabase client: {e}", file=sys.stderr)
        sys.exit(1)

    # 1. Get Parent Discipline ID
    print("\nFetching parent discipline ID...")
    parent_discipline_id = get_discipline_id(supabase, discipline_name)
    if parent_discipline_id is None:
        sys.exit(1) # Error message already printed by get_discipline_id
    print(f"Found Parent Discipline ID: {parent_discipline_id}")

    # 2. Read Sub-disciplines from File
    print("\nReading sub-disciplines from file...")
    sub_discipline_names = read_subdisciplines_from_file(filepath)
    if sub_discipline_names is None:
         sys.exit(1) # Error message already printed
    if not sub_discipline_names:
        print("Warning: No valid sub-discipline names found in the file.")
        print("--- Population Finished (No changes made) ---")
        sys.exit(0)
    print(f"Found {len(sub_discipline_names)} potential sub-disciplines to insert.")

    # 3. Insert Sub-disciplines
    print("\nInserting sub-disciplines into the database...")
    for name in sub_discipline_names:
        insert_sub_discipline(supabase, name, parent_discipline_id)

    print("\n--- Sub-discipline Population Complete ---")

if __name__ == "__main__":
    main()