"""
User and UserThread Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, UniqueConstraint
from src.shared.db.config import Base
from src.shared.db.models import JSONType, now_shanghai
import json


class User(Base):
    """User model matching users table."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(100), unique=True, index=True, nullable=False)
    display_name = Column(String(200), nullable=True)
    email = Column(String(255), nullable=True)
    user_type = Column(String(20), default='regular', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    preferences = Column(JSONType, nullable=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    def to_dict(self):
        """Convert model to dictionary."""
        preferences = self.preferences or {}
        if isinstance(preferences, str):
            try:
                preferences = json.loads(preferences)
            except:
                preferences = {}

        return {
            'id': self.id,
            'user_name': self.user_name,
            'display_name': self.display_name,
            'email': self.email,
            'user_type': self.user_type,
            'is_active': self.is_active,
            'last_login': self.last_login.strftime('%Y-%m-%d %H:%M:%S') if self.last_login else None,
            'avatar_url': self.avatar_url,
            'preferences': preferences,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }


class UserThread(Base):
    """User Thread model matching user_threads table."""
    __tablename__ = "user_threads"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_name = Column(String(100), nullable=False, index=True)
    thread_id = Column(String(255), nullable=False, index=True)
    thread_title = Column(String(500), nullable=True)
    agent_id = Column(String(100), nullable=True)
    is_archived = Column(Boolean, default=False, nullable=False)
    message_count = Column(Integer, default=0, nullable=False)
    last_message_time = Column(DateTime, nullable=True)
    create_at = Column(DateTime, default=now_shanghai, nullable=False)
    update_at = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    __table_args__ = (
        UniqueConstraint('user_name', 'thread_id', name='uk_user_thread'),
    )

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'user_name': self.user_name,
            'thread_id': self.thread_id,
            'thread_title': self.thread_title,
            'agent_id': self.agent_id,
            'is_archived': self.is_archived,
            'message_count': self.message_count,
            'last_message_time': self.last_message_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_message_time else None,
            'create_at': self.create_at.strftime('%Y-%m-%d %H:%M:%S') if self.create_at else None,
            'update_at': self.update_at.strftime('%Y-%m-%d %H:%M:%S') if self.update_at else None,
        }