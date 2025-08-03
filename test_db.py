import os
import json
from utils.db import ensure_db_files
from utils.helpers import ensure_data_files

print("Ensuring database files are created...")
ensure_db_files()

print("Ensuring helper data files are created...")
ensure_data_files()

print("\nChecking database files...")
DB_DIR = "data"
files = os.listdir(DB_DIR)

if files:
    print(f"Found {len(files)} files in the data directory:")
    for file in files:
        file_path = os.path.join(DB_DIR, file)
        file_size = os.path.getsize(file_path)
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                print(f" - {file}: {file_size} bytes, Valid JSON: Yes")
            except json.JSONDecodeError:
                print(f" - {file}: {file_size} bytes, Valid JSON: No")
else:
    print("No files found in the data directory. Something might be wrong with the initialization.")