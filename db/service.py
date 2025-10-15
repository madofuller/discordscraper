"""Database service layer for Discord scraper."""

import logging
from contextlib import contextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any

from sqlalchemy import create_engine, and_, or_, desc
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import IntegrityError

from .models import Base, Server, Subnet, Channel, User, Message, BackfillJob

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service class for database operations."""

    def __init__(self, connection_string: str, pool_size: int = 5, max_overflow: int = 10):
        """
        Initialize database service.
        
        Args:
            connection_string: PostgreSQL connection string
            pool_size: Number of connections to maintain in the pool
            max_overflow: Maximum overflow connections
        """
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True  # Verify connections before using
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info("Database service initialized")

    def create_tables(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session.
        
        Yields:
            Session: SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()

    # Server operations
    def upsert_server(self, server_id: int, name: str, icon_url: Optional[str] = None) -> Server:
        """Insert or update a server."""
        with self.get_session() as session:
            server = session.query(Server).filter(Server.server_id == server_id).first()
            if server:
                server.name = name
                server.icon_url = icon_url
            else:
                server = Server(server_id=server_id, name=name, icon_url=icon_url)
                session.add(server)
            session.commit()
            session.refresh(server)
            return server

    # Subnet operations
    def upsert_subnet(self, name: str, description: Optional[str] = None, 
                     tags: Optional[List[str]] = None) -> Subnet:
        """Insert or update a subnet."""
        with self.get_session() as session:
            subnet = session.query(Subnet).filter(Subnet.name == name).first()
            if subnet:
                if description:
                    subnet.description = description
                if tags:
                    subnet.tags = tags
            else:
                subnet = Subnet(name=name, description=description, tags=tags)
                session.add(subnet)
            session.commit()
            session.refresh(subnet)
            return subnet

    def get_subnet_by_name(self, name: str) -> Optional[Subnet]:
        """Get subnet by name."""
        with self.get_session() as session:
            return session.query(Subnet).filter(Subnet.name == name).first()

    def get_subnet_by_channel(self, channel_id: int) -> Optional[Subnet]:
        """Get subnet associated with a channel."""
        with self.get_session() as session:
            channel = session.query(Channel).filter(Channel.channel_id == channel_id).first()
            if channel and channel.subnet_id:
                return session.query(Subnet).filter(Subnet.id == channel.subnet_id).first()
            return None

    # Channel operations
    def upsert_channel(self, channel_id: int, server_id: int, name: str,
                      subnet_id: Optional[int] = None, topic: Optional[str] = None,
                      category: Optional[str] = None, position: Optional[int] = None) -> Channel:
        """Insert or update a channel."""
        with self.get_session() as session:
            channel = session.query(Channel).filter(Channel.channel_id == channel_id).first()
            if channel:
                channel.name = name
                channel.subnet_id = subnet_id
                channel.topic = topic
                channel.category = category
                channel.position = position
            else:
                channel = Channel(
                    channel_id=channel_id,
                    server_id=server_id,
                    name=name,
                    subnet_id=subnet_id,
                    topic=topic,
                    category=category,
                    position=position
                )
                session.add(channel)
            session.commit()
            session.refresh(channel)
            return channel

    def link_channel_to_subnet(self, channel_id: int, subnet_name: str) -> bool:
        """Link a channel to a subnet by name."""
        with self.get_session() as session:
            subnet = session.query(Subnet).filter(Subnet.name == subnet_name).first()
            if not subnet:
                logger.error(f"Subnet '{subnet_name}' not found")
                return False
            
            channel = session.query(Channel).filter(Channel.channel_id == channel_id).first()
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return False
            
            channel.subnet_id = subnet.id
            session.commit()
            return True

    # User operations
    def upsert_user(self, user_id: int, username: str, discriminator: Optional[str] = None,
                   display_name: Optional[str] = None, avatar_url: Optional[str] = None,
                   bot: bool = False) -> User:
        """Insert or update a user."""
        with self.get_session() as session:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                user.username = username
                user.discriminator = discriminator
                user.display_name = display_name
                user.avatar_url = avatar_url
                user.bot = bot
            else:
                user = User(
                    user_id=user_id,
                    username=username,
                    discriminator=discriminator,
                    display_name=display_name,
                    avatar_url=avatar_url,
                    bot=bot
                )
                session.add(user)
            session.commit()
            session.refresh(user)
            return user

    # Message operations
    def insert_message(self, message_data: Dict[str, Any]) -> Optional[Message]:
        """
        Insert a message (idempotent - ignores duplicates).
        
        Args:
            message_data: Dictionary with message fields
            
        Returns:
            Message object or None if duplicate
        """
        with self.get_session() as session:
            try:
                message = Message(**message_data)
                session.add(message)
                session.commit()
                session.refresh(message)
                return message
            except IntegrityError:
                session.rollback()
                logger.debug(f"Message {message_data.get('message_id')} already exists")
                return None

    def update_message(self, message_id: int, **kwargs) -> Optional[Message]:
        """Update a message."""
        with self.get_session() as session:
            message = session.query(Message).filter(Message.message_id == message_id).first()
            if message:
                for key, value in kwargs.items():
                    if hasattr(message, key):
                        setattr(message, key, value)
                session.commit()
                session.refresh(message)
                return message
            return None

    def mark_message_deleted(self, message_id: int) -> bool:
        """Mark a message as deleted."""
        with self.get_session() as session:
            message = session.query(Message).filter(Message.message_id == message_id).first()
            if message:
                message.deleted = True
                message.deleted_at = datetime.utcnow()
                session.commit()
                return True
            return False

    def get_messages_by_subnet(self, subnet_name: str, limit: int = 100,
                              offset: int = 0, include_deleted: bool = False) -> List[Message]:
        """Get messages for a specific subnet."""
        with self.get_session() as session:
            query = session.query(Message).join(Channel).join(Subnet).filter(
                Subnet.name == subnet_name
            )
            
            if not include_deleted:
                query = query.filter(Message.deleted == False)
            
            query = query.order_by(desc(Message.timestamp)).limit(limit).offset(offset)
            return query.all()

    def get_messages_by_channel(self, channel_id: int, limit: int = 100,
                               offset: int = 0, include_deleted: bool = False) -> List[Message]:
        """Get messages for a specific channel."""
        with self.get_session() as session:
            query = session.query(Message).filter(Message.channel_id == channel_id)
            
            if not include_deleted:
                query = query.filter(Message.deleted == False)
            
            query = query.order_by(desc(Message.timestamp)).limit(limit).offset(offset)
            return query.all()

    def get_messages_by_timerange(self, start_time: datetime, end_time: datetime,
                                  channel_id: Optional[int] = None,
                                  subnet_name: Optional[str] = None) -> List[Message]:
        """Get messages within a time range."""
        with self.get_session() as session:
            query = session.query(Message).filter(
                and_(
                    Message.timestamp >= start_time,
                    Message.timestamp <= end_time,
                    Message.deleted == False
                )
            )
            
            if channel_id:
                query = query.filter(Message.channel_id == channel_id)
            
            if subnet_name:
                query = query.join(Channel).join(Subnet).filter(Subnet.name == subnet_name)
            
            return query.order_by(desc(Message.timestamp)).all()

    def search_messages(self, search_term: str, subnet_name: Optional[str] = None,
                       limit: int = 50) -> List[Message]:
        """Full-text search on message content."""
        with self.get_session() as session:
            # Using PostgreSQL full-text search
            query = session.query(Message).filter(
                and_(
                    Message.content.ilike(f'%{search_term}%'),
                    Message.deleted == False
                )
            )
            
            if subnet_name:
                query = query.join(Channel).join(Subnet).filter(Subnet.name == subnet_name)
            
            return query.order_by(desc(Message.timestamp)).limit(limit).all()

    # Backfill job operations
    def create_backfill_job(self, channel_id: int) -> BackfillJob:
        """Create a new backfill job."""
        with self.get_session() as session:
            job = BackfillJob(
                channel_id=channel_id,
                start_time=datetime.utcnow(),
                status='pending'
            )
            session.add(job)
            session.commit()
            session.refresh(job)
            return job

    def update_backfill_job(self, job_id: int, **kwargs) -> Optional[BackfillJob]:
        """Update a backfill job."""
        with self.get_session() as session:
            job = session.query(BackfillJob).filter(BackfillJob.id == job_id).first()
            if job:
                for key, value in kwargs.items():
                    if hasattr(job, key):
                        setattr(job, key, value)
                session.commit()
                session.refresh(job)
                return job
            return None

    def get_backfill_jobs(self, channel_id: Optional[int] = None,
                         status: Optional[str] = None) -> List[BackfillJob]:
        """Get backfill jobs with optional filters."""
        with self.get_session() as session:
            query = session.query(BackfillJob)
            
            if channel_id:
                query = query.filter(BackfillJob.channel_id == channel_id)
            
            if status:
                query = query.filter(BackfillJob.status == status)
            
            return query.order_by(desc(BackfillJob.created_at)).all()

    def close(self):
        """Close database connections."""
        self.engine.dispose()
        logger.info("Database connections closed")

