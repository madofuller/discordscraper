"""
Quick database viewer to see what's in your Discord scraper database.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from db.service import DatabaseService
from db.models import Server, Channel, Message, User, Subnet
from sqlalchemy import func

load_dotenv()

def view_database():
    """Display database statistics and recent data."""
    
    # Connect to database
    db_config = {
        'user': 'postgres',
        'password': 'postgres',
        'host': 'localhost',
        'port': '5432',
        'database': 'discord_scraper'
    }
    
    connection_string = (
        f"postgresql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    
    db = DatabaseService(connection_string=connection_string)
    
    print("=" * 80)
    print("DISCORD SCRAPER DATABASE OVERVIEW")
    print("=" * 80)
    print()
    
    with db.get_session() as session:
        # Statistics
        total_messages = session.query(Message).count()
        total_users = session.query(User).count()
        total_channels = session.query(Channel).count()
        total_servers = session.query(Server).count()
        
        print(f"📊 STATISTICS:")
        print(f"   Messages: {total_messages:,}")
        print(f"   Users:    {total_users:,}")
        print(f"   Channels: {total_channels:,}")
        print(f"   Servers:  {total_servers:,}")
        print()
        
        # Date range
        if total_messages > 0:
            oldest = session.query(Message).order_by(Message.timestamp.asc()).first()
            newest = session.query(Message).order_by(Message.timestamp.desc()).first()
            
            print(f"📅 DATE RANGE:")
            print(f"   Oldest message: {oldest.timestamp}")
            print(f"   Newest message: {newest.timestamp}")
            print()
        
        # Top 10 most active channels
        print(f"🔥 TOP 10 MOST ACTIVE CHANNELS:")
        top_channels = (
            session.query(
                Channel.name,
                func.count(Message.message_id).label('count')
            )
            .join(Message, Message.channel_id == Channel.channel_id)
            .group_by(Channel.name)
            .order_by(func.count(Message.message_id).desc())
            .limit(10)
            .all()
        )
        
        for i, (name, count) in enumerate(top_channels, 1):
            print(f"   {i:2d}. {name:30s} {count:6,} messages")
        print()
        
        # Top 10 most active users
        print(f"👥 TOP 10 MOST ACTIVE USERS:")
        top_users = (
            session.query(
                User.username,
                func.count(Message.message_id).label('count')
            )
            .join(Message, Message.user_id == User.user_id)
            .group_by(User.username)
            .order_by(func.count(Message.message_id).desc())
            .limit(10)
            .all()
        )
        
        for i, (username, count) in enumerate(top_users, 1):
            print(f"   {i:2d}. {username:30s} {count:6,} messages")
        print()
        
        # Recent messages
        print(f"💬 5 MOST RECENT MESSAGES:")
        recent = (
            session.query(Message, User, Channel)
            .join(User, Message.user_id == User.user_id)
            .join(Channel, Message.channel_id == Channel.channel_id)
            .order_by(Message.timestamp.desc())
            .limit(5)
            .all()
        )
        
        for msg, user, channel in recent:
            content_preview = msg.content[:60] + "..." if len(msg.content) > 60 else msg.content
            print(f"   [{msg.timestamp}] #{channel.name}")
            print(f"   {user.username}: {content_preview}")
            print()
    
    print("=" * 80)
    print("\n💡 TIP: To query specific data, use scripts/query_example.py")
    print("   Or connect with pgAdmin, DBeaver, or psql\n")
    
    db.close()


if __name__ == '__main__':
    try:
        view_database()
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure PostgreSQL is running and the database exists.")
        sys.exit(1)

