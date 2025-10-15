"""
Auto-discover Discord channels and generate subnets.yaml configuration.
This script fetches all channels from your Discord server and creates the subnet config.
"""

import os
import sys
import yaml
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

load_dotenv()

def get_all_channels(server_id, token):
    """Fetch all channels from a Discord server."""
    url = f"https://discord.com/api/v10/guilds/{server_id}/channels"
    
    headers = {
        "Authorization": token
    }
    
    print(f"Fetching channels from server {server_id}...")
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(f"Response: {response.text}")
        return None
    
    return response.json()


def generate_subnets_config(channels, output_file):
    """Generate subnets.yaml from channel list."""
    
    # Filter only text channels and sort by name
    text_channels = [
        ch for ch in channels 
        if ch.get('type') in [0, 5]  # 0=text, 5=announcement
    ]
    
    text_channels.sort(key=lambda x: x.get('name', ''))
    
    # Build subnet configurations
    subnets = []
    for channel in text_channels:
        channel_name = channel.get('name', 'unknown')
        channel_id = str(channel.get('id', ''))
        
        subnet_config = {
            'name': channel_name,
            'channel_id': channel_id,
            'description': f"{channel_name} channel"
        }
        
        # Try to categorize based on channel name
        tags = []
        if 'subnet' in channel_name.lower():
            tags.append('subnet')
        if 'general' in channel_name.lower():
            tags.append('general')
        if 'announce' in channel_name.lower():
            tags.append('announcements')
        
        if tags:
            subnet_config['tags'] = tags
        
        subnets.append(subnet_config)
    
    # Create YAML structure
    config = {'subnets': subnets}
    
    # Write to file
    with open(output_file, 'w') as f:
        f.write("# Auto-generated subnet configuration\n")
        f.write("# Generated from Discord server channels\n\n")
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"\n✓ Generated config with {len(subnets)} channels")
    print(f"✓ Saved to: {output_file}")
    
    return subnets


def main():
    """Main function."""
    # Get configuration from environment
    server_id = os.getenv('DISCORD_SERVER_ID')
    token = os.getenv('DCE_TOKEN')
    
    if not server_id:
        print("Error: DISCORD_SERVER_ID not found in .env file")
        return 1
    
    if not token:
        print("Error: DCE_TOKEN not found in .env file")
        return 1
    
    print("=" * 80)
    print("Discord Channel Auto-Discovery")
    print("=" * 80)
    print()
    
    # Fetch channels
    channels = get_all_channels(server_id, token)
    
    if channels is None:
        print("\nFailed to fetch channels. Check your token and server ID.")
        return 1
    
    print(f"Found {len(channels)} total channels")
    
    # Generate config
    output_file = Path(__file__).parent.parent / 'config' / 'subnets.yaml'
    
    print(f"\nGenerating subnets.yaml...")
    subnets = generate_subnets_config(channels, output_file)
    
    print("\n" + "=" * 80)
    print("Preview of channels found:")
    print("=" * 80)
    
    # Show preview
    for i, subnet in enumerate(subnets[:10], 1):
        print(f"{i}. {subnet['name']} (ID: {subnet['channel_id']})")
    
    if len(subnets) > 10:
        print(f"... and {len(subnets) - 10} more channels")
    
    print("\n" + "=" * 80)
    print("✓ Configuration complete!")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Review config/subnets.yaml")
    print("2. Edit to keep only channels you want to track")
    print("3. Run: python scripts/scheduled_export.py")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())









