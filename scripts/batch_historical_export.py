#!/usr/bin/env python3
"""Batch export all Discord channels using DiscordChatExporter.

Usage:
    python batch_historical_export.py          # Export new channels only
    python batch_historical_export.py --resume # Resume partially exported channels
    python batch_historical_export.py -r       # Same as --resume

Resume mode will:
- Re-export all previously exported channels
- Continue from the last message ID found in existing JSON files
- Use DiscordChatExporter's --after parameter to avoid re-downloading old messages
"""

import sys
sys.path.insert(0, '.')

import os
import subprocess
import time
import yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# Configuration
DCE_PATH = os.getenv('DCE_PATH', 'DiscordChatExporter.Cli.exe')
DCE_TOKEN = os.getenv('DCE_TOKEN')
OUTPUT_DIR = Path('./exports')
DELAY_BETWEEN_CHANNELS = 5  # seconds to wait between exports (rate limit protection)
BATCH_SIZE = 10  # Number of channels to export before a longer break
BATCH_DELAY = 60  # seconds to wait after each batch
EXPORT_TIMEOUT = 10800  # 3 hours per channel (increased for large channels)

def load_channels():
    """Load channel IDs from subnets.yaml."""
    subnets_file = Path('config/subnets.yaml')
    
    if not subnets_file.exists():
        print("[!] config/subnets.yaml not found. Run auto_discover_channels.py first.")
        return []
    
    with open(subnets_file, 'r', encoding='utf-8') as f:
        subnets_data = yaml.safe_load(f)
    
    if not subnets_data or 'subnets' not in subnets_data:
        print("[!] No subnets found in config/subnets.yaml")
        return []
    
    channels = []
    for subnet in subnets_data['subnets']:
        channels.append({
            'name': subnet['name'],
            'channel_id': subnet['channel_id'],
            'subnet_id': subnet.get('subnet_id', 'unknown')
        })
    
    return channels

def get_last_message_id(channel_name):
    """Get the last exported message ID from a channel's JSON files."""
    folder_name = channel_name.replace('/', '-').replace('\\', '-').replace(':', '-')
    channel_dir = OUTPUT_DIR / folder_name

    if not channel_dir.exists():
        return None

    # Find all JSON files in the channel directory
    json_files = sorted(channel_dir.glob('*.json'))
    if not json_files:
        return None

    # Read the last JSON file
    last_file = json_files[-1]
    try:
        import json
        with open(last_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        messages = data.get('messages', [])
        if messages:
            # Get the last message ID (messages are in chronological order)
            last_message = messages[-1]
            return last_message.get('id')
    except Exception as e:
        print(f"[!] Warning: Could not read {last_file}: {e}")

    return None

def check_already_exported(channel_name):
    """Check if a channel has already been exported."""
    # Look for any directory or files matching the channel name
    for item in OUTPUT_DIR.iterdir():
        if channel_name.lower() in item.name.lower():
            return True
    return False

def export_channel(channel_id, channel_name, pbar=None, resume=False):
    """Export a single channel using DiscordChatExporter."""
    # Create output folder name (sanitize channel name)
    folder_name = channel_name.replace('/', '-').replace('\\', '-').replace(':', '-')
    output_path = OUTPUT_DIR / folder_name

    # Build command
    cmd = [
        DCE_PATH,
        'export',
        '--channel', channel_id,
        '--token', DCE_TOKEN,
        '--format', 'Json',
        '--output', str(output_path / f"{folder_name}.json"),
        '--partition', '1000'
    ]

    # If resuming, add --after parameter with last message ID
    if resume:
        last_message_id = get_last_message_id(channel_name)
        if last_message_id:
            cmd.extend(['--after', str(last_message_id)])
            if pbar:
                pbar.write(f"[~] Resuming from message ID: {last_message_id}")

    start_time = time.time()

    # Update progress bar description
    if pbar:
        pbar.set_description(f"Exporting: {channel_name[:50]}")

    try:
        # Run the export
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=EXPORT_TIMEOUT
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            if pbar:
                pbar.write(f"[+] {channel_name[:60]} - Success ({elapsed:.1f}s)")
            return True, elapsed, False
        else:
            # Provide more context for exit code 1 (usually forbidden/no access)
            error_msg = f"Failed (exit code {result.returncode})"
            is_forbidden = False
            if result.returncode == 1:
                if 'forbidden' in result.stderr.lower():
                    error_msg = "No access (forbidden)"
                    is_forbidden = True
                elif 'not found' in result.stderr.lower():
                    error_msg = "Channel not found"
            if pbar:
                pbar.write(f"[!] {channel_name[:60]} - {error_msg}")
            return False, elapsed, is_forbidden

    except subprocess.TimeoutExpired:
        if pbar:
            pbar.write(f"[!] {channel_name[:60]} - Timeout (>{EXPORT_TIMEOUT/3600:.0f}h)")
        return False, EXPORT_TIMEOUT, False
    except Exception as e:
        if pbar:
            pbar.write(f"[!] {channel_name[:60]} - Error: {str(e)[:100]}")
        return False, 0, False

def main():
    """Main function to batch export all channels."""
    import sys

    # Check for resume mode
    resume_mode = '--resume' in sys.argv or '-r' in sys.argv

    print("=" * 80)
    print(f"DISCORD HISTORICAL BATCH EXPORT{' (RESUME MODE)' if resume_mode else ''}")
    print("=" * 80)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Validate configuration
    if not DCE_TOKEN:
        print("\n[!] Error: DCE_TOKEN not set in .env file")
        return

    dce_path = Path(DCE_PATH)
    if not dce_path.exists():
        print(f"\n[!] Error: DiscordChatExporter not found at: {DCE_PATH}")
        print("Please update DCE_PATH in your .env file")
        return

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load channels
    print("\n[*] Loading channel list...")
    channels = load_channels()

    if not channels:
        print("[!] No channels found to export")
        return

    print(f"[+] Found {len(channels)} channels")

    # Filter channels based on mode
    print("\n[*] Checking for already exported channels...")
    to_export = []
    already_exported = []
    partial_exports = []
    skipped_forbidden = []

    # Load skip list (channels that failed with exit code 1)
    skip_list_file = OUTPUT_DIR / '.skip_forbidden_channels.txt'
    skip_list = set()
    if skip_list_file.exists():
        with open(skip_list_file, 'r', encoding='utf-8') as f:
            skip_list = set(line.strip() for line in f if line.strip())

    for channel in channels:
        # Skip channels that are known to be forbidden
        if channel['channel_id'] in skip_list:
            skipped_forbidden.append(channel['name'])
            continue

        is_exported = check_already_exported(channel['name'])

        if resume_mode and is_exported:
            # In resume mode, re-export partially completed channels
            partial_exports.append(channel['name'])
            to_export.append(channel)
        elif not resume_mode and is_exported:
            # In normal mode, skip already exported channels
            already_exported.append(channel['name'])
        else:
            to_export.append(channel)
    
    if skipped_forbidden:
        print(f"[>] Skipping {len(skipped_forbidden)} forbidden channels (no access)")
        if len(skipped_forbidden) <= 10:
            for name in skipped_forbidden[:10]:
                print(f"    - {name}")

    if resume_mode and partial_exports:
        print(f"[~] Resuming {len(partial_exports)} partially exported channels")
        if len(partial_exports) <= 10:
            for name in partial_exports[:10]:
                print(f"    - {name}")

    if already_exported:
        print(f"[>] Skipping {len(already_exported)} already exported channels")
        if len(already_exported) <= 10:
            for name in already_exported[:10]:
                print(f"    - {name}")

    if not to_export:
        print("\n[+] All accessible channels already exported!")
        return

    print(f"\n[*] Will export {len(to_export)} channels")
    if resume_mode:
        print(f"[*] Mode: Resume (will continue from last message ID)")
    print(f"[*] Estimated time: {len(to_export) * 30 / 60:.0f}-{len(to_export) * 120 / 60:.0f} minutes")
    print(f"[!] Rate limiting: {DELAY_BETWEEN_CHANNELS}s between channels, {BATCH_DELAY}s every {BATCH_SIZE} channels")

    input("\nPress ENTER to start the export...")
    
    # Export channels with progress bar
    successful = 0
    failed = 0
    forbidden_channels = []
    total_time = 0

    print("\n" + "=" * 80)
    print("STARTING EXPORT")
    print("=" * 80 + "\n")

    # Create progress bar
    with tqdm(
        total=len(to_export),
        desc="Exporting channels",
        unit="channel",
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
    ) as pbar:

        for idx, channel in enumerate(to_export, 1):
            success, elapsed, is_forbidden = export_channel(
                channel['channel_id'],
                channel['name'],
                pbar,
                resume=resume_mode
            )

            total_time += elapsed

            if success:
                successful += 1
            else:
                failed += 1
                # Track forbidden channels to skip them next time
                if is_forbidden:
                    forbidden_channels.append(channel['channel_id'])

            # Update progress bar
            pbar.update(1)
            
            # Rate limiting
            if idx < len(to_export):  # Don't delay after last channel
                if idx % BATCH_SIZE == 0:
                    pbar.write(f"\n[*] Batch {idx//BATCH_SIZE} complete. Waiting {BATCH_DELAY}s before next batch...\n")
                    time.sleep(BATCH_DELAY)
                else:
                    time.sleep(DELAY_BETWEEN_CHANNELS)
    
    # Save forbidden channels to skip file
    if forbidden_channels:
        with open(skip_list_file, 'a', encoding='utf-8') as f:
            for channel_id in forbidden_channels:
                if channel_id not in skip_list:  # Don't duplicate
                    f.write(f"{channel_id}\n")
        print(f"\n[*] Added {len(forbidden_channels)} forbidden channels to skip list")

    # Summary
    print("\n" + "=" * 80)
    print("EXPORT COMPLETE")
    print("=" * 80)
    print(f"[+] Successful: {successful}")
    print(f"[!] Failed: {failed}")
    if skipped_forbidden:
        print(f"[>] Skipped (forbidden): {len(skipped_forbidden)}")
    print(f"[>] Already exported: {len(already_exported)}")
    print(f"[*] Total channels: {len(channels)}")
    print(f"\n[*] Total export time: {total_time / 60:.1f} minutes ({total_time / 3600:.1f} hours)")
    if to_export:
        print(f"[*] Average time per channel: {total_time / len(to_export):.1f} seconds")
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nNext step: Run 'python scripts/batch_import_all.py' to import all exports")

if __name__ == "__main__":
    main()

