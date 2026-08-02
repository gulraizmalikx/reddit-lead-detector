"""
Reddit Lead Models
Database schema for Reddit-sourced leads
"""
from sqlalchemy import Column, String, Integer, Float, DateTime, Boolean, Text, JSON
from datetime import datetime
from database import Base

class RedditLead(Base):
    """
    Lead sourced from Reddit monitoring
    """
    __tablename__ = "reddit_leads"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    # Reddit source info
    reddit_username = Column(String(255), nullable=False, index=True)
    reddit_post_url = Column(String(500), nullable=False, unique=True)
    post_title = Column(String(500))
    post_body = Column(Text)
    subreddit = Column(String(100), index=True)

    # Lead analysis
    is_property_inquiry = Column(Boolean, default=False, index=True)
    confidence_score = Column(Float, default=0)
    lead_quality = Column(String(50), default='low', index=True)
    intent = Column(String(100))

    # Property preferences
    property_type = Column(String(100))
    budget_range = Column(String(100))
    location_preference = Column(String(500))
    timeline = Column(String(100))
    key_needs = Column(JSON, default=[])

    # Contact information
    email = Column(String(255), index=True)
    phone = Column(String(20))
    profile_url = Column(String(500))

    # Metadata
    summary = Column(Text)
    status = Column(String(50), default='new', index=True)
    lead_score = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    contacted_at = Column(DateTime)
    last_interaction = Column(DateTime)
    contacted_via = Column(String(50))

    # Conversion tracking
    is_converted = Column(Boolean, default=False)
    conversion_notes = Column(Text)

    def __repr__(self):
        return f"<RedditLead(username={self.reddit_username}, quality={self.lead_quality})>"


class RedditMonitoringLog(Base):
    """
    Log of monitoring cycles
    """
    __tablename__ = "reddit_monitoring_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))

    cycle_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    posts_fetched = Column(Integer, default=0)
    posts_analyzed = Column(Integer, default=0)
    leads_found = Column(Integer, default=0)
    high_quality_leads = Column(Integer, default=0)
    errors = Column(Text)

    def __repr__(self):
        return f"<RedditMonitoringLog(cycle={self.cycle_timestamp}, leads={self.leads_found})>"
