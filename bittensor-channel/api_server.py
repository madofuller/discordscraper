"""
FastAPI server for serving Discord chat data to your website
Provides REST API endpoints for accessing scraped messages
"""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional, List
import sqlite3
import json
from datetime import datetime
import os

app = FastAPI(title="Discord Chat API", version="1.0.0")

# CORS configuration for website access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-website.com", "http://localhost:3000"],  # Update with your website URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()
API_KEY = os.getenv('API_KEY', 'your-secret-api-key')

DATABASE_PATH = 'discord_messages.db'

# Models
class Message(BaseModel):
    id: str
    channel_id: str
    channel_name: str
    author_name: str
    author_nickname: Optional[str]
    content: str
    timestamp: str
    attachments: List[dict]
    reactions: List[dict]
    is_pinned: bool

class ChannelInfo(BaseModel):
    channel_id: str
    channel_name: str
    message_count: int
    last_message_timestamp: Optional[str]

# Authentication
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return credentials.credentials

# Database helper
def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Endpoints
@app.get("/")
async def root():
    return {"message": "Discord Chat API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/channels", response_model=List[ChannelInfo])
async def get_channels(token: str = Depends(verify_token)):
    """Get list of all monitored channels with message counts"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            channel_id,
            channel_name,
            COUNT(*) as message_count,
            MAX(timestamp) as last_message_timestamp
        FROM messages
        GROUP BY channel_id, channel_name
        ORDER BY channel_name
    ''')

    channels = []
    for row in cursor.fetchall():
        channels.append(ChannelInfo(
            channel_id=row['channel_id'],
            channel_name=row['channel_name'],
            message_count=row['message_count'],
            last_message_timestamp=row['last_message_timestamp']
        ))

    conn.close()
    return channels

@app.get("/messages/{channel_id}", response_model=List[Message])
async def get_messages(
    channel_id: str,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    after: Optional[str] = None,
    before: Optional[str] = None,
    search: Optional[str] = None,
    author_id: Optional[str] = None,
    token: str = Depends(verify_token)
):
    """
    Get messages from a specific channel

    - **channel_id**: Discord channel ID
    - **limit**: Maximum number of messages to return (1-1000)
    - **offset**: Number of messages to skip for pagination
    - **after**: Get messages after this timestamp (ISO format)
    - **before**: Get messages before this timestamp (ISO format)
    - **search**: Search in message content
    - **author_id**: Filter by author ID
    """
    conn = get_db()
    cursor = conn.cursor()

    # Build query
    query = 'SELECT * FROM messages WHERE channel_id = ?'
    params = [channel_id]

    if after:
        query += ' AND timestamp > ?'
        params.append(after)

    if before:
        query += ' AND timestamp < ?'
        params.append(before)

    if search:
        query += ' AND content LIKE ?'
        params.append(f'%{search}%')

    if author_id:
        query += ' AND author_id = ?'
        params.append(author_id)

    query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    cursor.execute(query, params)

    messages = []
    for row in cursor.fetchall():
        messages.append(Message(
            id=row['id'],
            channel_id=row['channel_id'],
            channel_name=row['channel_name'],
            author_name=row['author_name'],
            author_nickname=row['author_nickname'],
            content=row['content'],
            timestamp=row['timestamp'],
            attachments=json.loads(row['attachments']),
            reactions=json.loads(row['reactions']),
            is_pinned=bool(row['is_pinned'])
        ))

    conn.close()
    return messages

@app.get("/messages/{channel_id}/latest", response_model=List[Message])
async def get_latest_messages(
    channel_id: str,
    limit: int = Query(50, ge=1, le=100),
    token: str = Depends(verify_token)
):
    """Get the most recent messages from a channel"""
    return await get_messages(channel_id, limit=limit, offset=0, token=token)

@app.get("/messages/{channel_id}/{message_id}", response_model=Message)
async def get_message(
    channel_id: str,
    message_id: str,
    token: str = Depends(verify_token)
):
    """Get a specific message by ID"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * FROM messages WHERE channel_id = ? AND id = ?',
        (channel_id, message_id)
    )

    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Message not found")

    return Message(
        id=row['id'],
        channel_id=row['channel_id'],
        channel_name=row['channel_name'],
        author_name=row['author_name'],
        author_nickname=row['author_nickname'],
        content=row['content'],
        timestamp=row['timestamp'],
        attachments=json.loads(row['attachments']),
        reactions=json.loads(row['reactions']),
        is_pinned=bool(row['is_pinned'])
    )

@app.get("/search")
async def search_messages(
    q: str = Query(..., min_length=3),
    channel_id: Optional[str] = None,
    limit: int = Query(50, ge=1, le=500),
    token: str = Depends(verify_token)
):
    """Search messages across all channels or specific channel"""
    conn = get_db()
    cursor = conn.cursor()

    query = 'SELECT * FROM messages WHERE content LIKE ?'
    params = [f'%{q}%']

    if channel_id:
        query += ' AND channel_id = ?'
        params.append(channel_id)

    query += ' ORDER BY timestamp DESC LIMIT ?'
    params.append(limit)

    cursor.execute(query, params)

    messages = []
    for row in cursor.fetchall():
        messages.append(Message(
            id=row['id'],
            channel_id=row['channel_id'],
            channel_name=row['channel_name'],
            author_name=row['author_name'],
            author_nickname=row['author_nickname'],
            content=row['content'],
            timestamp=row['timestamp'],
            attachments=json.loads(row['attachments']),
            reactions=json.loads(row['reactions']),
            is_pinned=bool(row['is_pinned'])
        ))

    conn.close()
    return messages

@app.get("/stats/{channel_id}")
async def get_channel_stats(
    channel_id: str,
    token: str = Depends(verify_token)
):
    """Get statistics for a channel"""
    conn = get_db()
    cursor = conn.cursor()

    # Message count
    cursor.execute(
        'SELECT COUNT(*) as count FROM messages WHERE channel_id = ?',
        (channel_id,)
    )
    message_count = cursor.fetchone()['count']

    # Top authors
    cursor.execute('''
        SELECT author_name, author_nickname, COUNT(*) as count
        FROM messages
        WHERE channel_id = ?
        GROUP BY author_id
        ORDER BY count DESC
        LIMIT 10
    ''', (channel_id,))
    top_authors = [dict(row) for row in cursor.fetchall()]

    # Date range
    cursor.execute('''
        SELECT MIN(timestamp) as first, MAX(timestamp) as last
        FROM messages
        WHERE channel_id = ?
    ''', (channel_id,))
    date_range = dict(cursor.fetchone())

    conn.close()

    return {
        'channel_id': channel_id,
        'message_count': message_count,
        'top_authors': top_authors,
        'date_range': date_range
    }

# Run server
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
