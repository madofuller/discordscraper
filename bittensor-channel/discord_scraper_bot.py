"""
Live Discord Chat Scraper using discord.py
Monitors channels in real-time and stores messages in a database
"""

import discord
from discord.ext import commands
import json
import sqlite3
from datetime import datetime
import asyncio
import os
from typing import Optional

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
DATABASE_PATH = 'discord_messages.db'
CHANNELS_TO_MONITOR = [
    # Add channel IDs you want to monitor
    # Example: 1191833510021955695,  # subnet 23
]

class DiscordMessageLogger(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        super().__init__(command_prefix='!', intents=intents)

        self.init_database()

    def init_database(self):
        """Initialize SQLite database for storing messages"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                channel_id TEXT,
                channel_name TEXT,
                guild_id TEXT,
                guild_name TEXT,
                author_id TEXT,
                author_name TEXT,
                author_discriminator TEXT,
                author_nickname TEXT,
                content TEXT,
                timestamp DATETIME,
                edited_timestamp DATETIME,
                attachments TEXT,
                embeds TEXT,
                mentions TEXT,
                reactions TEXT,
                is_pinned BOOLEAN,
                reference_id TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS last_sync (
                channel_id TEXT PRIMARY KEY,
                last_message_id TEXT,
                last_sync_time DATETIME
            )
        ''')

        conn.commit()
        conn.close()

    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Monitoring {len(CHANNELS_TO_MONITOR)} channels')

        # Optionally sync historical messages on startup
        # await self.sync_historical_messages()

    async def on_message(self, message):
        """Log every message in monitored channels"""
        if message.channel.id not in CHANNELS_TO_MONITOR:
            return

        # Don't log bot's own messages
        if message.author == self.user:
            return

        await self.log_message(message)

    async def on_message_edit(self, before, after):
        """Log message edits"""
        if after.channel.id not in CHANNELS_TO_MONITOR:
            return

        await self.log_message(after, is_edit=True)

    async def on_raw_reaction_add(self, payload):
        """Log reactions"""
        if payload.channel_id not in CHANNELS_TO_MONITOR:
            return

        await self.update_message_reactions(payload.message_id, payload.channel_id)

    async def log_message(self, message: discord.Message, is_edit: bool = False):
        """Store message in database"""
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Prepare message data
        attachments_json = json.dumps([{
            'url': att.url,
            'filename': att.filename,
            'size': att.size
        } for att in message.attachments])

        embeds_json = json.dumps([embed.to_dict() for embed in message.embeds])

        mentions_json = json.dumps([{
            'id': str(user.id),
            'name': user.name,
            'discriminator': user.discriminator
        } for user in message.mentions])

        reactions_json = json.dumps([{
            'emoji': str(reaction.emoji),
            'count': reaction.count
        } for reaction in message.reactions])

        cursor.execute('''
            INSERT OR REPLACE INTO messages
            (id, channel_id, channel_name, guild_id, guild_name,
             author_id, author_name, author_discriminator, author_nickname,
             content, timestamp, edited_timestamp, attachments, embeds,
             mentions, reactions, is_pinned, reference_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            str(message.id),
            str(message.channel.id),
            message.channel.name,
            str(message.guild.id),
            message.guild.name,
            str(message.author.id),
            message.author.name,
            message.author.discriminator,
            message.author.nick if hasattr(message.author, 'nick') else None,
            message.content,
            message.created_at.isoformat(),
            message.edited_at.isoformat() if message.edited_at else None,
            attachments_json,
            embeds_json,
            mentions_json,
            reactions_json,
            message.pinned,
            str(message.reference.message_id) if message.reference else None
        ))

        conn.commit()
        conn.close()

        print(f"{'Updated' if is_edit else 'Logged'} message from {message.author.name} in #{message.channel.name}")

    async def update_message_reactions(self, message_id: int, channel_id: int):
        """Update reactions for a message"""
        try:
            channel = self.get_channel(channel_id)
            message = await channel.fetch_message(message_id)

            reactions_json = json.dumps([{
                'emoji': str(reaction.emoji),
                'count': reaction.count
            } for reaction in message.reactions])

            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE messages SET reactions = ? WHERE id = ?',
                (reactions_json, str(message_id))
            )
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating reactions: {e}")

    async def sync_historical_messages(self, limit: int = 1000):
        """Sync historical messages from monitored channels"""
        print("Syncing historical messages...")

        for channel_id in CHANNELS_TO_MONITOR:
            try:
                channel = self.get_channel(channel_id)
                if not channel:
                    print(f"Channel {channel_id} not found")
                    continue

                print(f"Syncing #{channel.name}...")

                # Get last synced message ID
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    'SELECT last_message_id FROM last_sync WHERE channel_id = ?',
                    (str(channel_id),)
                )
                result = cursor.fetchone()
                after_id = int(result[0]) if result else None
                conn.close()

                # Fetch messages
                after_obj = discord.Object(id=after_id) if after_id else None
                async for message in channel.history(limit=limit, after=after_obj, oldest_first=True):
                    await self.log_message(message)
                    await asyncio.sleep(0.1)  # Rate limiting

                # Update last sync
                conn = sqlite3.connect(DATABASE_PATH)
                cursor = conn.cursor()
                cursor.execute(
                    '''INSERT OR REPLACE INTO last_sync
                       (channel_id, last_message_id, last_sync_time)
                       VALUES (?, ?, ?)''',
                    (str(channel_id), str(message.id), datetime.utcnow().isoformat())
                )
                conn.commit()
                conn.close()

                print(f"Synced #{channel.name}")
            except Exception as e:
                print(f"Error syncing channel {channel_id}: {e}")

# Run the bot
if __name__ == '__main__':
    bot = DiscordMessageLogger()
    bot.run(DISCORD_TOKEN)
