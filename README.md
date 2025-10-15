# Discord Scraper for Bittensor Subnets

A comprehensive Discord message scraping system designed to collect, store, and provide access to community discussions across Bittensor subnet channels. This system combines historical data backfilling with real-time message collection, storing everything in PostgreSQL for easy querying and future website integration.

## Features

- **Historical Backfill**: Import past messages using DiscordChatExporter
- **Real-Time Collection**: Live Discord bot captures new messages as they're posted
- **Scheduled Exports**: Alternative approach for users without admin permissions (no bot needed)
- **Subnet-Based Organization**: Messages organized by subnet for easy filtering
- **Full Message Metadata**: Captures attachments, embeds, reactions, edits, and deletions
- **PostgreSQL Storage**: Reliable, queryable database with full-text search
- **Lambda-Ready API**: Future-proof endpoints for website integration
- **Scalable Architecture**: Handles single or multiple Discord servers

## Two Deployment Options

### Option 1: Real-Time Bot (Requires Admin)
Best for: Admins or those with permission to add a bot to the server
- ✅ Real-time message capture
- ✅ Edit/delete tracking
- ✅ Instant updates
- ⚠️ Requires bot invite permissions

**See**: [SETUP_GUIDE.md](SETUP_GUIDE.md)

### Option 2: Scheduled Exports (No Admin Needed)
Best for: Users without admin permissions
- ✅ No bot required
- ✅ Fully automated
- ✅ Same database/API
- ⚠️ Not real-time (scheduled updates)

**See**: [QUICKSTART_SCHEDULED.md](QUICKSTART_SCHEDULED.md) or [SCHEDULED_SETUP_GUIDE.md](SCHEDULED_SETUP_GUIDE.md)

## Architecture

### Components

1. **Database Layer** (`db/`)
   - PostgreSQL schema with optimized indexes
   - SQLAlchemy models for all entities
   - Service layer for database operations

2. **Discord Bot** (`bot/`)
   - Real-time message collection via Discord Gateway API
   - Automatic server/channel synchronization
   - Handles message edits and deletions

3. **Backfill Scripts** (`scripts/`)
   - DiscordChatExporter wrapper for historical data
   - Database setup and initialization
   - Subnet configuration management

4. **API Handlers** (`api/`)
   - Lambda-ready query endpoints
   - RESTful message retrieval
   - Subnet-based filtering

## Setup

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- DiscordChatExporter CLI ([Download here](https://github.com/Tyrrrz/DiscordChatExporter))

### Installation

1. **Clone the repository**
   ```bash
   cd discordscraper
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup PostgreSQL**
   
   Option A: Using Docker (recommended for local development)
   ```bash
   docker-compose up -d postgres
   ```
   
   Option B: Use existing PostgreSQL instance
   - Create a database named `discord_scraper`
   - Note the connection details for configuration

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` with your credentials:
   ```env
   # Discord
   DISCORD_BOT_TOKEN=your_bot_token_here
   DISCORD_SERVER_ID=your_server_id_here
   
   # Database
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=discord_scraper
   DB_USER=postgres
   DB_PASSWORD=your_password
   
   # DiscordChatExporter
   DCE_PATH=path/to/DiscordChatExporter.Cli.exe
   DCE_TOKEN=your_discord_token
   ```

5. **Configure subnet mappings**
   
   Edit `config/subnets.yaml`:
   ```yaml
   subnets:
     - name: "subnet-1"
       channel_id: "1234567890123456789"
       description: "Subnet 1 discussions"
       tags: ["ai", "compute"]
     
     - name: "subnet-2"
       channel_id: "9876543210987654321"
       description: "Subnet 2 discussions"
       tags: ["storage"]
   ```

6. **Initialize the database**
   ```bash
   python scripts/setup_db.py
   ```

### Discord Bot Setup

1. **Create a Discord Application**
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Click "New Application"
   - Go to "Bot" section and click "Add Bot"

2. **Configure Bot Permissions**
   Required permissions:
   - Read Messages/View Channels
   - Read Message History
   - Send Messages (optional, for bot commands)

3. **Enable Intents**
   In the Bot settings, enable:
   - Server Members Intent
   - Message Content Intent

4. **Invite Bot to Server**
   - Go to OAuth2 > URL Generator
   - Select scopes: `bot`
   - Select permissions: `Read Messages`, `Read Message History`
   - Use generated URL to invite bot to your server

## Usage

### Running the Real-Time Bot

Start the bot to begin collecting messages in real-time:

```bash
python run_bot.py
```

The bot will:
- Connect to Discord
- Sync server and channel information
- Start collecting new messages
- Store everything in PostgreSQL

### Running Historical Backfill

Import historical messages from configured channels:

```bash
python scripts/backfill.py
```

This will:
- Export messages using DiscordChatExporter
- Parse exported JSON files
- Import messages to database
- Track backfill job status

### Querying Messages

You can query messages directly from the database or use the API handlers.

#### Direct Database Query (Python)

```python
from db.service import DatabaseService
from datetime import datetime, timedelta

# Initialize database
db = DatabaseService("postgresql://user:pass@localhost/discord_scraper")

# Get recent messages for a subnet
messages = db.get_messages_by_subnet("subnet-1", limit=50)

# Get messages in a time range
start = datetime.now() - timedelta(days=7)
end = datetime.now()
messages = db.get_messages_by_timerange(start, end, subnet_name="subnet-1")

# Search messages
messages = db.search_messages("bittensor", subnet_name="subnet-1")
```

#### Using SQL

```sql
-- Get recent subnet messages
SELECT * FROM subnet_messages 
WHERE subnet_name = 'subnet-1' 
ORDER BY timestamp DESC 
LIMIT 100;

-- Search message content
SELECT * FROM messages 
WHERE content ILIKE '%bittensor%' 
  AND deleted = FALSE
ORDER BY timestamp DESC;

-- Get message count by subnet
SELECT s.name, COUNT(m.message_id) as message_count
FROM subnets s
JOIN channels c ON s.id = c.subnet_id
JOIN messages m ON c.channel_id = m.channel_id
WHERE m.deleted = FALSE
GROUP BY s.name;
```

## Database Schema

### Main Tables

- **`servers`**: Discord server metadata
- **`subnets`**: Subnet configuration and mappings
- **`channels`**: Channel information with subnet links
- **`users`**: Discord user cache
- **`messages`**: All messages with full metadata
- **`backfill_jobs`**: Backfill job tracking

### Key Features

- **Idempotent inserts**: Duplicate messages are automatically ignored
- **Full-text search**: Optimized indexes for content search
- **Soft deletes**: Deleted messages are marked, not removed
- **Audit trail**: Created/updated timestamps on all tables

## API Endpoints (Lambda-Ready)

The `api/handler.py` file contains Lambda-ready functions for website integration:

### Query Messages

```python
GET /messages?subnet=subnet-1&from=2024-01-01T00:00:00Z&to=2024-01-31T23:59:59Z&limit=50
```

Parameters:
- `subnet`: Subnet name
- `channel_id`: Specific channel ID (optional)
- `from`: Start timestamp (ISO format)
- `to`: End timestamp (ISO format)
- `limit`: Max results (default 100)
- `offset`: Pagination offset
- `search`: Full-text search term

Response:
```json
{
  "messages": [
    {
      "message_id": "123456789",
      "channel_id": "987654321",
      "user_id": "111111111",
      "content": "Message text",
      "timestamp": "2024-01-15T10:30:00Z",
      "attachments": [],
      "embeds": [],
      "reactions": []
    }
  ],
  "count": 1,
  "limit": 50,
  "offset": 0
}
```

## Future Website Integration

The system is designed for easy integration with Bittensor.ai:

1. **Deploy Lambda Functions**: Use `api/handler.py` functions
2. **Setup API Gateway**: Configure REST API endpoints
3. **Frontend Integration**: Call API endpoints to display messages
4. **Real-Time Updates**: Bot continues to collect data in background

Example frontend query:
```javascript
// Fetch recent subnet discussions
const response = await fetch(
  'https://api.bittensor.ai/messages?subnet=subnet-1&limit=100'
);
const data = await response.json();
```

## Project Structure

```
discordscraper/
├── bot/
│   ├── __init__.py
│   └── discord_bot.py          # Real-time Discord bot
├── db/
│   ├── __init__.py
│   ├── schema.sql              # PostgreSQL schema
│   ├── models.py               # SQLAlchemy models
│   └── service.py              # Database operations
├── scripts/
│   ├── __init__.py
│   ├── backfill.py             # Historical data import
│   └── setup_db.py             # Database initialization
├── api/
│   ├── __init__.py
│   └── handler.py              # Lambda-ready endpoints
├── config/
│   ├── config.yaml             # Main configuration
│   └── subnets.yaml            # Subnet mappings
├── logs/                       # Application logs
├── exports/                    # DiscordChatExporter output
├── requirements.txt            # Python dependencies
├── docker-compose.yml          # Local PostgreSQL
├── run_bot.py                  # Bot entry point
└── README.md
```

## Monitoring and Maintenance

### Logs

Application logs are stored in `logs/discord_bot.log`. Monitor for:
- Connection errors
- Database issues
- Failed message processing

### Database Maintenance

Periodic maintenance tasks:

```sql
-- Vacuum and analyze
VACUUM ANALYZE messages;

-- Check table sizes
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Reindex for performance
REINDEX TABLE messages;
```

### Backfill Job Status

Check backfill job status:

```python
from db.service import DatabaseService

db = DatabaseService("postgresql://user:pass@localhost/discord_scraper")
jobs = db.get_backfill_jobs(status='failed')

for job in jobs:
    print(f"Job {job.id}: {job.error_message}")
```

## Troubleshooting

### Bot Not Connecting

1. Check bot token is correct in `.env`
2. Verify bot is invited to the server
3. Ensure Message Content Intent is enabled

### Database Connection Errors

1. Verify PostgreSQL is running: `docker-compose ps`
2. Check connection details in `.env`
3. Test connection: `psql -h localhost -U postgres -d discord_scraper`

### DiscordChatExporter Not Working

1. Verify DCE_PATH points to correct executable
2. Ensure DCE_TOKEN is valid
3. Check exports directory exists and is writable

### Missing Messages

1. Check bot has permission to read channel
2. Verify channel is mapped in `subnets.yaml`
3. Check backfill job status for errors

## Development

### Running Tests

```bash
pytest tests/
```

### Code Formatting

```bash
black .
flake8 .
```

### Adding New Subnets

1. Edit `config/subnets.yaml`
2. Add new subnet configuration
3. Restart the bot or run `setup_db.py` again
4. Optionally run backfill for the new channel

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues or questions:
- GitHub Issues: [Your repo URL]
- Discord: [Your Discord server]
- Email: [Your contact email]

