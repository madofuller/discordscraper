#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Check export status of all channels and identify incomplete exports."""

import sys
import io
sys.path.insert(0, '.')

# Fix encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import json
from pathlib import Path
import yaml

# Configuration
OUTPUT_DIR = Path('./exports')
SUBNETS_FILE = Path('config/subnets.yaml')


def load_channels():
    """Load channel IDs from subnets.yaml."""
    if not SUBNETS_FILE.exists():
        print(f"[!] {SUBNETS_FILE} not found")
        return []

    with open(SUBNETS_FILE, 'r', encoding='utf-8') as f:
        subnets_data = yaml.safe_load(f)

    if not subnets_data or 'subnets' not in subnets_data:
        return []

    return [{
        'name': subnet['name'],
        'channel_id': subnet['channel_id']
    } for subnet in subnets_data['subnets']]


def get_channel_stats(channel_name):
    """Get statistics for a channel's exports."""
    folder_name = channel_name.replace('/', '-').replace('\\', '-').replace(':', '-')
    channel_dir = OUTPUT_DIR / folder_name

    if not channel_dir.exists():
        return {
            'status': 'not_exported',
            'files': 0,
            'messages': 0,
            'last_message_id': None
        }

    json_files = sorted(channel_dir.glob('*.json'))
    if not json_files:
        return {
            'status': 'empty',
            'files': 0,
            'messages': 0,
            'last_message_id': None
        }

    total_messages = 0
    last_message_id = None

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            messages = data.get('messages', [])
            total_messages += len(messages)

            # Get last message ID from the last file
            if json_file == json_files[-1] and messages:
                last_message_id = messages[-1].get('id')

        except Exception as e:
            return {
                'status': 'corrupted',
                'files': len(json_files),
                'messages': total_messages,
                'last_message_id': last_message_id,
                'error': str(e)
            }

    return {
        'status': 'complete',
        'files': len(json_files),
        'messages': total_messages,
        'last_message_id': last_message_id
    }


def main():
    """Main function."""
    print("=" * 80)
    print("EXPORT STATUS CHECKER")
    print("=" * 80)

    if not OUTPUT_DIR.exists():
        print(f"\n[!] Export directory not found: {OUTPUT_DIR}")
        return

    channels = load_channels()
    if not channels:
        print("[!] No channels found in config")
        return

    print(f"\n[*] Checking {len(channels)} channels...\n")

    not_exported = []
    empty = []
    complete = []
    corrupted = []

    for channel in channels:
        stats = get_channel_stats(channel['name'])
        channel['stats'] = stats

        if stats['status'] == 'not_exported':
            not_exported.append(channel)
        elif stats['status'] == 'empty':
            empty.append(channel)
        elif stats['status'] == 'corrupted':
            corrupted.append(channel)
        else:
            complete.append(channel)

    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"[+] Complete:      {len(complete):4d}")
    print(f"[!] Not exported:  {len(not_exported):4d}")
    print(f"[~] Empty:         {len(empty):4d}")
    print(f"[~] Corrupted:     {len(corrupted):4d}")
    print(f"    TOTAL:         {len(channels):4d}")

    # Total messages
    total_messages = sum(c['stats']['messages'] for c in complete)
    print(f"\n[*] Total messages exported: {total_messages:,}")

    # Show details if requested
    print("\n" + "=" * 80)

    if not_exported:
        print(f"\nNOT EXPORTED ({len(not_exported)}):")
        print("-" * 80)
        for channel in not_exported[:20]:  # Show first 20
            print(f"  - {channel['name']}")
        if len(not_exported) > 20:
            print(f"  ... and {len(not_exported) - 20} more")

    if empty:
        print(f"\nEMPTY EXPORTS ({len(empty)}):")
        print("-" * 80)
        for channel in empty:
            print(f"  - {channel['name']}")

    if corrupted:
        print(f"\nCORRUPTED EXPORTS ({len(corrupted)}):")
        print("-" * 80)
        for channel in corrupted:
            print(f"  - {channel['name']}")
            print(f"    Error: {channel['stats'].get('error', 'Unknown')}")

    # Show channels with most messages
    if complete:
        print(f"\nTOP 10 CHANNELS BY MESSAGE COUNT:")
        print("-" * 80)
        top_channels = sorted(complete, key=lambda c: c['stats']['messages'], reverse=True)[:10]
        for idx, channel in enumerate(top_channels, 1):
            stats = channel['stats']
            print(f"  {idx:2d}. {channel['name'][:60]:<60} {stats['messages']:>8,} msgs ({stats['files']} files)")

    # Suggest next steps
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)

    if not_exported:
        print(f"\n[!] {len(not_exported)} channels need to be exported")
        print("    Run: python scripts/batch_historical_export.py")

    if empty or corrupted:
        print(f"\n[!] {len(empty) + len(corrupted)} channels may need re-export")
        print("    Run: python scripts/batch_historical_export.py --resume")

    if complete and not (not_exported or empty or corrupted):
        print("\n[+] All channels exported successfully!")
        print("    Run: python scripts/batch_import_all.py")


if __name__ == "__main__":
    main()
