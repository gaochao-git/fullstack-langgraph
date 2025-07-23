"""Database models for SOP management."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.types import TypeDecorator
import json
import os

from .config import Base, DATABASE_TYPE


class JSONType(TypeDecorator):
    """Cross-database JSON type."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        elif dialect.name == 'mysql':
            return dialect.type_descriptor(JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name in ('postgresql', 'mysql'):
                return value
            else:
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if dialect.name in ('postgresql', 'mysql'):
                return value
            else:
                return json.loads(value)
        return value


class SOPTemplate(Base):
    """SOP Template model matching sop_prompt_templates table."""
    __tablename__ = "sop_prompt_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sop_id = Column(String(100), unique=True, index=True, nullable=False)
    sop_title = Column(String(500), nullable=False)
    sop_category = Column(String(100), nullable=False, index=True)
    sop_description = Column(Text, nullable=True)
    sop_severity = Column(String(20), nullable=False, index=True)
    sop_steps = Column(JSONType, nullable=False)
    tools_required = Column(JSONType, nullable=True)
    sop_recommendations = Column(Text, nullable=True)
    team_name = Column(String(100), nullable=False, index=True)
    create_by = Column(String(100), nullable=False)
    update_by = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'sop_id': self.sop_id,
            'sop_title': self.sop_title,
            'sop_category': self.sop_category,
            'sop_description': self.sop_description,
            'sop_severity': self.sop_severity,
            'sop_steps': json.dumps(self.sop_steps) if isinstance(self.sop_steps, (dict, list)) else self.sop_steps,
            'tools_required': json.dumps(self.tools_required) if isinstance(self.tools_required, (dict, list)) else self.tools_required,
            'sop_recommendations': self.sop_recommendations,
            'team_name': self.team_name,
            'create_by': self.create_by,
            'update_by': self.update_by,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }


class MCPServer(Base):
    """MCP Server model matching mcp_servers table."""
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    server_id = Column(String(100), unique=True, index=True, nullable=False)
    server_name = Column(String(200), nullable=False)
    server_uri = Column(String(500), nullable=False)
    server_description = Column(Text, nullable=True)
    is_enabled = Column(String(10), default='on', nullable=False)
    connection_status = Column(String(20), default='disconnected', nullable=False)
    auth_type = Column(String(20), default='', nullable=True)
    auth_token = Column(Text, nullable=True)
    api_key_header = Column(String(100), nullable=True)
    read_timeout_seconds = Column(Integer, default=5, nullable=False)
    server_tools = Column(Text, nullable=True)
    server_config = Column(Text, nullable=True)
    team_name = Column(String(100), nullable=False, index=True)
    create_by = Column(String(100), nullable=False)
    update_by = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert model to dictionary."""
        # 处理server_tools字段 - 如果是JSON字符串则解析为列表
        server_tools = self.server_tools
        if isinstance(server_tools, str) and server_tools:
            try:
                server_tools = json.loads(server_tools)
            except (json.JSONDecodeError, ValueError):
                server_tools = []
        elif server_tools is None:
            server_tools = []
        
        # 处理server_config字段 - 如果是JSON字符串则解析为字典
        server_config = self.server_config
        if isinstance(server_config, str) and server_config:
            try:
                server_config = json.loads(server_config)
            except (json.JSONDecodeError, ValueError):
                server_config = {}
        elif server_config is None:
            server_config = {}
        
        return {
            'id': self.id,
            'server_id': self.server_id,
            'server_name': self.server_name,
            'server_uri': self.server_uri,
            'server_description': self.server_description,
            'is_enabled': self.is_enabled,
            'connection_status': self.connection_status,
            'auth_type': self.auth_type,
            'auth_token': self.auth_token,
            'api_key_header': self.api_key_header,
            'read_timeout_seconds': self.read_timeout_seconds,
            'server_tools': server_tools,
            'server_config': server_config,
            'team_name': self.team_name,
            'create_by': self.create_by,
            'update_by': self.update_by,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }