"""
Automated Discord Chat Export using DiscordChatExporter CLI
Periodically exports channels and processes them for website upload
"""

import subprocess
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
import schedule

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_TOKEN_HERE')
EXPORT_DIR = Path('exports')
PROCESSED_DIR = Path('processed')
DCE_PATH = r'C:\path\to\DiscordChatExporter.Cli.exe'  # Update this path

# Channels to monitor
CHANNELS = {
    '1191833510021955695': 'nuance-23',  # Example: subnet 23
    # Add more channels here
}

# Export settings
EXPORT_FORMAT = 'Json'  # Json, HtmlDark, HtmlLight, PlainText, Csv
EXPORT_INTERVAL_MINUTES = 15  # How often to export

EXPORT_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)

class DiscordExporter:
    def __init__(self):
        self.last_message_ids = self.load_last_message_ids()

    def load_last_message_ids(self):
        """Load last processed message IDs"""
        tracking_file = PROCESSED_DIR / 'last_message_ids.json'
        if tracking_file.exists():
            with open(tracking_file, 'r') as f:
                return json.load(f)
        return {}

    def save_last_message_ids(self):
        """Save last processed message IDs"""
        tracking_file = PROCESSED_DIR / 'last_message_ids.json'
        with open(tracking_file, 'w') as f:
            json.dump(self.last_message_ids, f, indent=2)

    def export_channel(self, channel_id: str, channel_name: str):
        """Export a single channel using DiscordChatExporter"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = EXPORT_DIR / f'{channel_name}_{timestamp}.json'

        # Build command
        cmd = [
            DCE_PATH,
            'export',
            '-t', DISCORD_TOKEN,
            '-c', channel_id,
            '-f', EXPORT_FORMAT,
            '-o', str(output_file)
        ]

        # Add "after" parameter for incremental exports
        if channel_id in self.last_message_ids:
            last_id = self.last_message_ids[channel_id]
            cmd.extend(['--after', last_id])
        else:
            # First time - get messages from last 7 days
            after_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            cmd.extend(['--after', after_date])

        try:
            print(f'Exporting {channel_name} (ID: {channel_id})...')
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                print(f'Successfully exported to {output_file}')
                return output_file
            else:
                print(f'Export failed: {result.stderr}')
                return None
        except Exception as e:
            print(f'Error exporting channel: {e}')
            return None

    def process_export(self, export_file: Path):
        """Process exported JSON file"""
        if not export_file or not export_file.exists():
            return

        try:
            with open(export_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'messages' not in data or not data['messages']:
                print('No new messages in export')
                return

            messages = data['messages']
            print(f'Processing {len(messages)} messages')

            # Update last message ID
            channel_id = data.get('channel', {}).get('id')
            if channel_id and messages:
                self.last_message_ids[channel_id] = messages[-1]['id']
                self.save_last_message_ids()

            # Process messages for your website
            processed_data = self.transform_messages(messages, data)

            # Save processed data
            processed_file = PROCESSED_DIR / f"{export_file.stem}_processed.json"
            with open(processed_file, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)

            print(f'Processed data saved to {processed_file}')

            # Optional: Upload to website
            # self.upload_to_website(processed_data)

        except Exception as e:
            print(f'Error processing export: {e}')

    def transform_messages(self, messages: list, metadata: dict) -> dict:
        """Transform messages into format suitable for your website"""
        transformed = {
            'channel': {
                'id': metadata.get('channel', {}).get('id'),
                'name': metadata.get('channel', {}).get('name'),
                'category': metadata.get('channel', {}).get('category'),
            },
            'guild': {
                'id': metadata.get('guild', {}).get('id'),
                'name': metadata.get('guild', {}).get('name'),
            },
            'exported_at': metadata.get('exportedAt'),
            'message_count': len(messages),
            'messages': []
        }

        for msg in messages:
            transformed_msg = {
                'id': msg.get('id'),
                'timestamp': msg.get('timestamp'),
                'author': {
                    'id': msg.get('author', {}).get('id'),
                    'name': msg.get('author', {}).get('name'),
                    'nickname': msg.get('author', {}).get('nickname'),
                    'avatarUrl': msg.get('author', {}).get('avatarUrl'),
                },
                'content': msg.get('content', ''),
                'attachments': msg.get('attachments', []),
                'embeds': msg.get('embeds', []),
                'reactions': msg.get('reactions', []),
                'isPinned': msg.get('isPinned', False),
                'reference': msg.get('reference'),
            }
            transformed['messages'].append(transformed_msg)

        return transformed

    def upload_to_website(self, data: dict):
        """Upload processed data to your website via API"""
        # Example using requests library
        import requests

        API_URL = 'https://your-website.com/api/discord/messages'
        API_KEY = os.getenv('WEBSITE_API_KEY', 'YOUR_API_KEY')

        try:
            response = requests.post(
                API_URL,
                json=data,
                headers={'Authorization': f'Bearer {API_KEY}'},
                timeout=30
            )

            if response.status_code == 200:
                print('Successfully uploaded to website')
            else:
                print(f'Upload failed: {response.status_code} - {response.text}')
        except Exception as e:
            print(f'Error uploading to website: {e}')

    def run_export_cycle(self):
        """Run a complete export cycle for all channels"""
        print(f'\n=== Starting export cycle at {datetime.now()} ===')

        for channel_id, channel_name in CHANNELS.items():
            export_file = self.export_channel(channel_id, channel_name)
            if export_file:
                self.process_export(export_file)
            time.sleep(2)  # Rate limiting between channels

        print(f'=== Export cycle completed ===\n')

# Main execution
def main():
    exporter = DiscordExporter()

    # Run immediately on start
    exporter.run_export_cycle()

    # Schedule periodic exports
    schedule.every(EXPORT_INTERVAL_MINUTES).minutes.do(exporter.run_export_cycle)

    print(f'Scheduler started. Exporting every {EXPORT_INTERVAL_MINUTES} minutes.')
    print('Press Ctrl+C to stop.')

    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
