# Discord Chat Scraper Setup Guide

Complete guide to set up live Discord chat scraping and website integration.

## Overview

This system provides two approaches:

1. **Discord Bot (Real-time)** - Uses discord.py to monitor channels in real-time
2. **DiscordChatExporter (Periodic)** - Uses DCE CLI to export channels periodically

Both store data in SQLite and provide a REST API for website integration.

---

## Prerequisites

### 1. Discord Bot Token
- Go to [Discord Developer Portal](https://discord.com/developers/applications)
- Create New Application
- Go to "Bot" tab → Add Bot
- Copy the token
- Enable these Privileged Gateway Intents:
  - Message Content Intent
  - Server Members Intent
  - Presence Intent

### 2. Invite Bot to Your Server
```
https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=68608&scope=bot
```

### 3. Install DiscordChatExporter CLI
Download from: https://github.com/Tyrrrz/DiscordChatExporter
Extract to a known location (e.g., `C:\tools\DiscordChatExporter\`)

### 4. Install Python Dependencies
```bash
pip install -r requirements.txt
```

---

## Setup Instructions

### Method 1: Real-time Bot (Recommended for live updates)

#### Step 1: Configure the Bot
Edit `discord_scraper_bot.py`:

```python
DISCORD_TOKEN = 'your_bot_token_here'
CHANNELS_TO_MONITOR = [
    1191833510021955695,  # subnet 23
    # Add more channel IDs
]
```

#### Step 2: Run the Bot
```bash
python discord_scraper_bot.py
```

The bot will:
- Connect to Discord
- Monitor specified channels
- Store messages in `discord_messages.db`
- Update in real-time as new messages arrive

#### Step 3: Optional - Sync Historical Messages
Uncomment this line in `discord_scraper_bot.py`:
```python
await self.sync_historical_messages()
```

---

### Method 2: Periodic Export with DiscordChatExporter

#### Step 1: Configure the Exporter
Edit `discord_exporter_automation.py`:

```python
DISCORD_TOKEN = 'your_bot_token_here'
DCE_PATH = r'C:\path\to\DiscordChatExporter.Cli.exe'

CHANNELS = {
    '1191833510021955695': 'nuance-23',
    # Add more channels
}

EXPORT_INTERVAL_MINUTES = 15  # Export frequency
```

#### Step 2: Run the Automation
```bash
python discord_exporter_automation.py
```

This will:
- Export channels every X minutes
- Process JSON exports
- Track last message IDs for incremental exports
- Save processed data to `processed/` folder

---

## API Server Setup

#### Step 1: Configure API Server
Edit `api_server.py`:

```python
API_KEY = 'your-secret-api-key-here'

# Update CORS origins
allow_origins=["https://your-website.com", "http://localhost:3000"]
```

#### Step 2: Run the API Server
```bash
python api_server.py
```

API will be available at `http://localhost:8000`

#### Step 3: Test API Endpoints
```bash
# Get channels
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/channels

# Get latest messages
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/messages/CHANNEL_ID/latest

# Search messages
curl -H "Authorization: Bearer your-api-key" http://localhost:8000/search?q=subnet
```

---

## Website Integration

### Option 1: Use Provided HTML Page
1. Open `website_integration.html`
2. Update configuration:
```javascript
const API_BASE_URL = 'http://your-server:8000';
const API_KEY = 'your-secret-api-key';
```
3. Host on your website

### Option 2: JavaScript Integration
```javascript
// Example: Fetch latest messages
async function getLatestMessages(channelId) {
    const response = await fetch(
        `http://your-api-url/messages/${channelId}/latest`,
        {
            headers: {
                'Authorization': 'Bearer your-api-key'
            }
        }
    );
    return await response.json();
}

// Display messages
getLatestMessages('1191833510021955695').then(messages => {
    messages.forEach(msg => {
        console.log(`${msg.author_name}: ${msg.content}`);
    });
});
```

### Option 3: React Integration
```jsx
import { useEffect, useState } from 'react';

function DiscordFeed({ channelId }) {
    const [messages, setMessages] = useState([]);

    useEffect(() => {
        async function fetchMessages() {
            const response = await fetch(
                `http://your-api-url/messages/${channelId}/latest`,
                {
                    headers: {
                        'Authorization': 'Bearer your-api-key'
                    }
                }
            );
            const data = await response.json();
            setMessages(data);
        }

        fetchMessages();
        const interval = setInterval(fetchMessages, 10000); // Refresh every 10s

        return () => clearInterval(interval);
    }, [channelId]);

    return (
        <div>
            {messages.map(msg => (
                <div key={msg.id}>
                    <strong>{msg.author_name}:</strong> {msg.content}
                </div>
            ))}
        </div>
    );
}
```

---

## Production Deployment

### 1. Use Environment Variables
```bash
# .env file
DISCORD_BOT_TOKEN=your_token
API_KEY=your_api_key
DATABASE_PATH=/path/to/discord_messages.db
```

### 2. Run as System Service

#### Windows (using NSSM)
```bash
nssm install DiscordBot python C:\path\to\discord_scraper_bot.py
nssm install DiscordAPI python C:\path\to\api_server.py
nssm start DiscordBot
nssm start DiscordAPI
```

#### Linux (systemd)
Create `/etc/systemd/system/discord-bot.service`:
```ini
[Unit]
Description=Discord Chat Scraper Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/discord-scraper
ExecStart=/usr/bin/python3 discord_scraper_bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable discord-bot
sudo systemctl start discord-bot
```

### 3. Nginx Reverse Proxy
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Use HTTPS
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d api.yourdomain.com
```

---

## API Endpoints Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/channels` | GET | List all channels |
| `/messages/{channel_id}` | GET | Get messages from channel |
| `/messages/{channel_id}/latest` | GET | Get latest messages |
| `/messages/{channel_id}/{message_id}` | GET | Get specific message |
| `/search` | GET | Search messages |
| `/stats/{channel_id}` | GET | Get channel statistics |

### Query Parameters

**`/messages/{channel_id}`**
- `limit`: Max messages (1-1000, default: 100)
- `offset`: Pagination offset
- `after`: Messages after timestamp
- `before`: Messages before timestamp
- `search`: Search in content
- `author_id`: Filter by author

**`/search`**
- `q`: Search query (required, min 3 chars)
- `channel_id`: Limit to specific channel
- `limit`: Max results (1-500, default: 50)

---

## Monitoring & Maintenance

### Check Bot Status
```bash
# Bot logs
tail -f discord_bot.log

# Database size
ls -lh discord_messages.db

# Message count
sqlite3 discord_messages.db "SELECT COUNT(*) FROM messages;"
```

### Database Maintenance
```python
# Vacuum database (reclaim space)
import sqlite3
conn = sqlite3.connect('discord_messages.db')
conn.execute('VACUUM')
conn.close()

# Delete old messages (older than 90 days)
import sqlite3
from datetime import datetime, timedelta

conn = sqlite3.connect('discord_messages.db')
cutoff = (datetime.now() - timedelta(days=90)).isoformat()
conn.execute('DELETE FROM messages WHERE timestamp < ?', (cutoff,))
conn.commit()
conn.close()
```

---

## Troubleshooting

### Bot Not Connecting
- Check token is correct
- Verify bot has proper intents enabled
- Ensure bot is invited to server

### No Messages Appearing
- Check bot has read permissions in channels
- Verify channel IDs are correct
- Check `CHANNELS_TO_MONITOR` list

### API Errors
- Verify API_KEY matches in both server and client
- Check CORS origins include your website
- Ensure database file is accessible

### DiscordChatExporter Issues
- Verify DCE_PATH points to correct executable
- Check token has proper permissions
- Review error messages in console

---

## Security Best Practices

1. **Never commit tokens to git**
   - Use environment variables
   - Add `.env` to `.gitignore`

2. **Secure API access**
   - Use strong API keys
   - Implement rate limiting
   - Use HTTPS in production

3. **Database security**
   - Regular backups
   - Restrict file permissions
   - Encrypt sensitive data

4. **Discord TOS Compliance**
   - Respect user privacy
   - Don't store DMs without consent
   - Follow Discord's data retention policies

---

## Performance Tips

1. **Database Indexing**
```sql
CREATE INDEX idx_channel_timestamp ON messages(channel_id, timestamp);
CREATE INDEX idx_author ON messages(author_id);
CREATE INDEX idx_content ON messages(content);
```

2. **Pagination**
Always use limit/offset for large result sets

3. **Caching**
Implement Redis for frequently accessed data

4. **Separate Read/Write**
Use separate databases for bot writes and API reads

---

## Support

For issues with:
- Discord Bot: https://github.com/Rapptz/discord.py/issues
- DiscordChatExporter: https://github.com/Tyrrrz/DiscordChatExporter/issues
- FastAPI: https://fastapi.tiangolo.com/

---

## License

Ensure compliance with:
- Discord Terms of Service
- Discord Developer Terms
- Your local data protection laws (GDPR, etc.)
