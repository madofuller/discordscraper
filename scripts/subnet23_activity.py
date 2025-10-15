#!/usr/bin/env python3
"""Query most active users on Subnet 23 channel."""

import sys
sys.path.insert(0, '.')

from db.service import DatabaseService
from dotenv import load_dotenv
from sqlalchemy import text
import os

load_dotenv()

def main():
    # Initialize database service
    connection_string = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    db_service = DatabaseService(connection_string)
    
    # Query for subnet 23 activity
    query = """
    SELECT 
        u.username,
        u.display_name,
        COUNT(m.message_id) as message_count,
        MIN(m.timestamp) as first_message,
        MAX(m.timestamp) as last_message,
        COUNT(DISTINCT DATE(m.timestamp)) as active_days
    FROM messages m
    JOIN users u ON m.user_id = u.user_id
    JOIN channels c ON m.channel_id = c.channel_id
    WHERE c.name ILIKE '%23%nuance%' OR c.name ILIKE '%nuance%23%'
    GROUP BY u.user_id, u.username, u.display_name
    HAVING COUNT(m.message_id) > 0
    ORDER BY message_count DESC
    LIMIT 20;
    """
    
    with db_service.get_session() as session:
        result = session.execute(text(query))
        rows = result.fetchall()
        
        if not rows:
            print("❌ No messages found for Subnet 23 (nuance)")
            print("\nLet me check what channels exist...")
            
            # Find channels with '23' in the name
            channel_query = """
            SELECT name, channel_id 
            FROM channels 
            WHERE name ILIKE '%23%'
            ORDER BY name;
            """
            channel_result = session.execute(text(channel_query))
            channels = channel_result.fetchall()
            
            if channels:
                print(f"\nFound {len(channels)} channel(s) with '23' in the name:")
                for ch in channels:
                    print(f"  - {ch[0]} (ID: {ch[1]})")
            else:
                print("\n❌ No channels found with '23' in the name")
            return
        
        print("=" * 80)
        print(f"{'MOST ACTIVE USERS ON SUBNET 23 (NUANCE)':^80}")
        print("=" * 80)
        print(f"\n{'Rank':<6} {'Username':<25} {'Display Name':<25} {'Messages':<10} {'Days Active':<12}")
        print("-" * 80)
        
        for idx, row in enumerate(rows, 1):
            username = row[0] or "N/A"
            display_name = row[1] or "N/A"
            msg_count = row[2]
            active_days = row[5]
            
            # Handle special characters for Windows console
            username = username.encode('ascii', 'replace').decode('ascii')
            display_name = display_name.encode('ascii', 'replace').decode('ascii')
            
            # Truncate long names
            username = username[:24] if len(username) > 24 else username
            display_name = display_name[:24] if len(display_name) > 24 else display_name
            
            print(f"{idx:<6} {username:<25} {display_name:<25} {msg_count:<10} {active_days:<12}")
        
        print("\n" + "=" * 80)
        print(f"Total unique users: {len(rows)}")
        print(f"Total messages: {sum(row[2] for row in rows):,}")

if __name__ == "__main__":
    main()

