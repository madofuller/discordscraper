#!/usr/bin/env python3
"""Batch import all exported Discord channel data into the database."""

import sys
sys.path.insert(0, '.')

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from db.service import DatabaseService
from tqdm import tqdm

load_dotenv()

# Configuration
OUTPUT_DIR = Path('./exports')

def find_all_json_exports():
    """Find all JSON export files in the exports directory."""
    json_files = []
    
    if not OUTPUT_DIR.exists():
        return json_files
    
    # Look for .json files recursively
    for json_file in OUTPUT_DIR.rglob('*.json'):
        json_files.append(json_file)
    
    return sorted(json_files)

def import_json_file(json_path, db_service, pbar=None):
    """Import a single JSON export file."""
    # Get filename for display
    filename = json_path.name
    
    # Update progress bar description
    if pbar:
        pbar.set_description(f"Importing: {filename[:50]}")
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data:
            if pbar:
                pbar.write(f"[!] {filename[:60]} - Empty file, skipped")
            return 0, 0
        
        # Import using the same logic as import_historical_exports.py
        from scripts.import_historical_exports import import_export_data
        
        messages_imported, messages_skipped = import_export_data(data, db_service)
        
        if pbar:
            pbar.write(f"[+] {filename[:60]} - Imported: {messages_imported}, Skipped: {messages_skipped}")
        
        return messages_imported, messages_skipped
        
    except json.JSONDecodeError as e:
        if pbar:
            pbar.write(f"[!] {filename[:60]} - JSON error: {str(e)[:80]}")
        return 0, 0
    except Exception as e:
        if pbar:
            pbar.write(f"[!] {filename[:60]} - Error: {str(e)[:80]}")
        return 0, 0

def main():
    """Main function to batch import all exports."""
    print("=" * 80)
    print("DISCORD HISTORICAL BATCH IMPORT")
    print("=" * 80)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize database
    print("\n[*] Connecting to database...")
    connection_string = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    db_service = DatabaseService(connection_string)
    print("[+] Database connected")
    
    # Find all JSON files
    print(f"\n[*] Scanning {OUTPUT_DIR} for JSON exports...")
    json_files = find_all_json_exports()
    
    if not json_files:
        print(f"[!] No JSON export files found in {OUTPUT_DIR}")
        return
    
    print(f"[+] Found {len(json_files)} JSON export file(s)")
    
    # Show first few files
    print("\nFiles to import:")
    for json_file in json_files[:10]:
        print(f"  - {json_file.relative_to(OUTPUT_DIR)}")
    if len(json_files) > 10:
        print(f"  ... and {len(json_files) - 10} more")
    
    input("\nPress ENTER to start the import...")
    
    # Import all files with progress bar
    total_imported = 0
    total_skipped = 0
    successful_files = 0
    failed_files = 0
    
    print("\n" + "=" * 80)
    print("STARTING IMPORT")
    print("=" * 80 + "\n")
    
    # Create progress bar
    with tqdm(
        total=len(json_files),
        desc="Importing files",
        unit="file",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
    ) as pbar:
        
        for json_file in json_files:
            try:
                imported, skipped = import_json_file(json_file, db_service, pbar)
                total_imported += imported
                total_skipped += skipped
                
                if imported > 0 or skipped > 0:
                    successful_files += 1
                else:
                    failed_files += 1
                    
            except Exception as e:
                pbar.write(f"[!] Unexpected error: {str(e)[:100]}")
                failed_files += 1
            
            # Update progress bar
            pbar.update(1)
    
    # Summary
    print("\n" + "=" * 80)
    print("IMPORT COMPLETE")
    print("=" * 80)
    print(f"[+] Files imported successfully: {successful_files}")
    print(f"[!] Files failed: {failed_files}")
    print(f"[*] Total files processed: {len(json_files)}")
    print(f"\n[+] Total messages imported: {total_imported:,}")
    print(f"[>] Total duplicates skipped: {total_skipped:,}")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Show database stats
    print("\n" + "=" * 80)
    print("DATABASE STATISTICS")
    print("=" * 80)
    
    with db_service.get_session() as session:
        from sqlalchemy import text, func
        from db.models import Channel, Message, User
        
        channel_count = session.query(func.count(Channel.channel_id)).scalar()
        message_count = session.query(func.count(Message.message_id)).scalar()
        user_count = session.query(func.count(User.user_id)).scalar()
        
        print(f"[*] Total channels: {channel_count:,}")
        print(f"[*] Total messages: {message_count:,}")
        print(f"[*] Total users: {user_count:,}")

if __name__ == "__main__":
    main()

