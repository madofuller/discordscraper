"""
Import historical DiscordChatExporter JSON exports into the database.
This script processes all JSON export files from a directory.
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from db.service import DatabaseService
from utils.config_loader import load_config

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Path(__file__).parent.parent / 'logs' / 'import_historical.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def import_json_file(db_service, json_file_path, server_id):
    """
    Import a single DiscordChatExporter JSON file.
    
    Args:
        db_service: Database service instance
        json_file_path: Path to JSON export file
        server_id: Discord server ID
        
    Returns:
        Number of messages imported
    """
    logger.info(f"Processing: {json_file_path.name}")
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extract channel info
        channel_data = data.get('channel', {})
        channel_id = int(channel_data.get('id', 0))
        channel_name = channel_data.get('name', 'Unknown')
        
        # Extract messages
        messages = data.get('messages', [])
        logger.info(f"  Channel: {channel_name} (ID: {channel_id})")
        logger.info(f"  Total messages in file: {len(messages)}")
        
        # Ensure channel exists in database
        db_service.upsert_channel(
            channel_id=channel_id,
            server_id=server_id,
            name=channel_name,
            topic=channel_data.get('topic')
        )
        
        # Import messages
        imported_count = 0
        skipped_count = 0
        
        for msg_data in messages:
            try:
                # Extract author info
                author = msg_data.get('author', {})
                author_id = int(author.get('id', 0))
                
                # Upsert user
                db_service.upsert_user(
                    user_id=author_id,
                    username=author.get('name', 'Unknown'),
                    discriminator=author.get('discriminator'),
                    display_name=author.get('nickname'),
                    avatar_url=author.get('avatarUrl'),
                    bot=author.get('isBot', False)
                )
                
                # Parse timestamp
                timestamp_str = msg_data.get('timestamp', msg_data.get('timestampEdited'))
                if timestamp_str:
                    # Handle timezone offset
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                else:
                    logger.warning(f"  No timestamp for message {msg_data.get('id')}, skipping")
                    continue
                
                edited_timestamp = None
                if msg_data.get('timestampEdited'):
                    edited_timestamp = datetime.fromisoformat(
                        msg_data['timestampEdited'].replace('Z', '+00:00')
                    )
                
                # Prepare message data
                message_data = {
                    'message_id': int(msg_data['id']),
                    'channel_id': channel_id,
                    'user_id': author_id,
                    'content': msg_data.get('content', ''),
                    'timestamp': timestamp,
                    'edited_timestamp': edited_timestamp,
                    'message_type': msg_data.get('type', 'Default'),
                    'mentions': [int(m['id']) for m in msg_data.get('mentions', [])],
                    'attachments': msg_data.get('attachments', []),
                    'embeds': msg_data.get('embeds', []),
                    'reactions': msg_data.get('reactions', []),
                    'reference_message_id': int(msg_data['reference']['messageId']) 
                        if msg_data.get('reference') and msg_data['reference'].get('messageId') 
                        else None
                }
                
                # Insert message (idempotent - will skip if already exists)
                result = db_service.insert_message(message_data)
                if result:
                    imported_count += 1
                else:
                    skipped_count += 1
                    
            except Exception as e:
                logger.error(f"  Error importing message {msg_data.get('id')}: {e}")
                continue
        
        logger.info(f"  ✓ Imported: {imported_count} new messages")
        logger.info(f"  ⊘ Skipped: {skipped_count} duplicate messages")
        
        return imported_count
        
    except Exception as e:
        logger.error(f"  ✗ Failed to process {json_file_path.name}: {e}", exc_info=True)
        return 0


def main():
    """Main import function."""
    try:
        logger.info("=" * 80)
        logger.info("Historical Export Import")
        logger.info("=" * 80)
        
        # Load config
        config = load_config()
        db_config = config['database']
        discord_config = config['discord']
        
        # Build connection string
        connection_string = (
            f"postgresql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        # Initialize database service
        logger.info("Initializing database service...")
        db_service = DatabaseService(connection_string=connection_string)
        
        # Get server ID
        server_id = int(discord_config['server_id'])
        
        # Find all JSON export files
        export_dir = Path(__file__).parent.parent / 'bittensor-channel'
        json_files = list(export_dir.glob('Bittensor*.json'))
        
        logger.info(f"Found {len(json_files)} export files to import")
        logger.info("")
        
        if not json_files:
            logger.warning("No export files found in bittensor-channel/")
            return 1
        
        # Import each file
        total_imported = 0
        for i, json_file in enumerate(json_files, 1):
            logger.info(f"[{i}/{len(json_files)}] Processing {json_file.name}")
            imported = import_json_file(db_service, json_file, server_id)
            total_imported += imported
            logger.info("")
        
        logger.info("=" * 80)
        logger.info(f"Import completed successfully")
        logger.info(f"Total files processed: {len(json_files)}")
        logger.info(f"Total new messages imported: {total_imported}")
        logger.info("=" * 80)
        
        # Close connections
        db_service.close()
        
        return 0
        
    except Exception as e:
        logger.error(f"Import failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())









