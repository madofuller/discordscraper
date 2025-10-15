"""SQLAlchemy models for Discord scraper database."""

from datetime import datetime
from sqlalchemy import (
    Column, BigInteger, Integer, String, Text, Boolean, 
    DateTime, ForeignKey, JSON, ARRAY, Float
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Server(Base):
    """Discord server/guild model."""
    __tablename__ = 'servers'

    server_id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    icon_url = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    channels = relationship("Channel", back_populates="server", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Server(id={self.server_id}, name='{self.name}')>"


class Subnet(Base):
    """Subnet configuration model."""
    __tablename__ = 'subnets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    tags = Column(ARRAY(Text))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    channels = relationship("Channel", back_populates="subnet")

    def __repr__(self):
        return f"<Subnet(id={self.id}, name='{self.name}')>"


class Channel(Base):
    """Discord channel model."""
    __tablename__ = 'channels'

    channel_id = Column(BigInteger, primary_key=True)
    server_id = Column(BigInteger, ForeignKey('servers.server_id', ondelete='CASCADE'), nullable=False)
    subnet_id = Column(Integer, ForeignKey('subnets.id', ondelete='SET NULL'))
    name = Column(String(255), nullable=False)
    topic = Column(Text)
    category = Column(String(255))
    position = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    server = relationship("Server", back_populates="channels")
    subnet = relationship("Subnet", back_populates="channels")
    messages = relationship("Message", back_populates="channel", cascade="all, delete-orphan")
    backfill_jobs = relationship("BackfillJob", back_populates="channel", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Channel(id={self.channel_id}, name='{self.name}')>"


class User(Base):
    """Discord user model."""
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255), nullable=False)
    discriminator = Column(String(10))
    display_name = Column(String(255))
    avatar_url = Column(Text)
    bot = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    messages = relationship("Message", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.user_id}, username='{self.username}')>"


class Message(Base):
    """Discord message model."""
    __tablename__ = 'messages'

    message_id = Column(BigInteger, primary_key=True)
    channel_id = Column(BigInteger, ForeignKey('channels.channel_id', ondelete='CASCADE'), nullable=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    content = Column(Text)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    edited_timestamp = Column(DateTime(timezone=True))
    deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime(timezone=True))
    message_type = Column(String(50), default='default')
    
    # Message metadata
    mentions = Column(ARRAY(BigInteger))
    mention_roles = Column(ARRAY(BigInteger))
    attachments = Column(JSON)
    embeds = Column(JSON)
    reactions = Column(JSON)
    
    # Thread metadata
    thread_id = Column(BigInteger)
    
    # References
    reference_message_id = Column(BigInteger)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    channel = relationship("Channel", back_populates="messages")
    user = relationship("User", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.message_id}, user_id={self.user_id})>"


class BackfillJob(Base):
    """Backfill job tracking model."""
    __tablename__ = 'backfill_jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel_id = Column(BigInteger, ForeignKey('channels.channel_id', ondelete='CASCADE'), nullable=False)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False, default='pending')
    messages_imported = Column(Integer, default=0)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    channel = relationship("Channel", back_populates="backfill_jobs")

    def __repr__(self):
        return f"<BackfillJob(id={self.id}, channel_id={self.channel_id}, status='{self.status}')>"


class SubnetEra(Base):
    """Track subnet project phases and slot changes"""
    __tablename__ = 'subnet_eras'
    
    era_id = Column(Integer, primary_key=True, autoincrement=True)
    subnet_number = Column(Integer, index=True, nullable=False)
    project_name = Column(String(100), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    topic_description = Column(Text)
    confidence_score = Column(Float, default=0.0)
    channel_id = Column(BigInteger, ForeignKey('channels.channel_id', ondelete='CASCADE'))
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    channel = relationship("Channel")
    
    def __repr__(self):
        return f"<SubnetEra(era_id={self.era_id}, subnet={self.subnet_number}, project='{self.project_name}')>"


class MessageInsight(Base):
    """AI-extracted insights from messages"""
    __tablename__ = 'message_insights'
    
    insight_id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(BigInteger, ForeignKey('messages.message_id', ondelete='CASCADE'), index=True, nullable=False)
    
    # Classification
    category = Column(String(50))  # Technical, Investment, Mining, Community, Announcement, Issue
    subcategory = Column(String(100))  # Q&A, Bug Report, Feature Request, etc.
    sentiment = Column(String(20))  # positive, negative, neutral, mixed
    
    # Extracted entities
    mentioned_subnets = Column(ARRAY(Integer))  # [1, 23, 19]
    tao_amounts = Column(ARRAY(Float))  # [100.5, 2000.0]
    apy_mentions = Column(ARRAY(Float))  # [15.5, 20.0]
    technical_terms = Column(ARRAY(String))  # ["validator", "emission", "slippage"]
    
    # Key information flags
    is_setup_guide = Column(Boolean, default=False)
    is_troubleshooting = Column(Boolean, default=False)
    is_announcement = Column(Boolean, default=False)
    is_investment_signal = Column(Boolean, default=False)
    
    # AI analysis
    key_insight = Column(Text)  # One-sentence summary
    importance_score = Column(Float, default=0.0)  # 0-1 scale
    
    analyzed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    message = relationship("Message")
    
    def __repr__(self):
        return f"<MessageInsight(insight_id={self.insight_id}, message_id={self.message_id}, category='{self.category}')>"


class IntelligenceReport(Base):
    """Pre-computed intelligence reports"""
    __tablename__ = 'intelligence_reports'
    
    report_id = Column(Integer, primary_key=True, autoincrement=True)
    report_type = Column(String(50), nullable=False)  # investor, validator, miner, developer, ecosystem
    subnet_number = Column(Integer, nullable=True, index=True)
    
    # Report content
    summary = Column(Text)
    metrics = Column(JSON)  # Flexible structure for different report types
    risk_signals = Column(JSON)
    opportunities = Column(JSON)
    key_quotes = Column(JSON)  # [{message_id, quote, context}, ...]
    
    # Metadata
    time_period = Column(String(20), nullable=False)  # all_time, last_30d, last_90d
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    message_count_analyzed = Column(Integer, default=0)
    source_message_ids = Column(ARRAY(BigInteger))
    
    def __repr__(self):
        return f"<IntelligenceReport(report_id={self.report_id}, type='{self.report_type}', subnet={self.subnet_number})>"

