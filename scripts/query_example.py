"""Example script showing how to query messages from the database."""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from db.service import DatabaseService
from utils.config_loader import load_config

# Load environment variables
load_dotenv()


def main():
    """Example queries."""
    # Load config
    config = load_config()
    db_config = config['database']
    
    # Build connection string
    connection_string = (
        f"postgresql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    
    # Initialize database service
    db = DatabaseService(connection_string=connection_string)
    
    print("=" * 80)
    print("Discord Scraper Query Examples")
    print("=" * 80)
    
    # Example 1: Get recent messages by subnet
    print("\n1. Recent messages from subnet-1:")
    print("-" * 80)
    messages = db.get_messages_by_subnet("subnet-1", limit=5)
    for msg in messages:
        print(f"[{msg.timestamp}] User {msg.user_id}: {msg.content[:100]}")
    
    # Example 2: Get messages from last 24 hours
    print("\n2. Messages from last 24 hours:")
    print("-" * 80)
    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow()
    messages = db.get_messages_by_timerange(start_time, end_time)
    print(f"Found {len(messages)} messages in the last 24 hours")
    
    # Example 3: Search messages
    print("\n3. Search for 'bittensor':")
    print("-" * 80)
    messages = db.search_messages("bittensor", limit=5)
    for msg in messages:
        print(f"[{msg.timestamp}] {msg.content[:100]}")
    
    # Example 4: Get message statistics
    print("\n4. Database statistics:")
    print("-" * 80)
    with db.get_session() as session:
        from db.models import Message, Channel, Subnet
        from sqlalchemy import func
        
        # Total messages
        total = session.query(func.count(Message.message_id)).scalar()
        print(f"Total messages: {total}")
        
        # Messages by subnet
        stats = session.query(
            Subnet.name,
            func.count(Message.message_id).label('count')
        ).join(Channel).join(Message).group_by(Subnet.name).all()
        
        print("\nMessages by subnet:")
        for subnet_name, count in stats:
            print(f"  {subnet_name}: {count}")
    
    # Close database
    db.close()
    print("\n" + "=" * 80)


if __name__ == '__main__':
    main()

