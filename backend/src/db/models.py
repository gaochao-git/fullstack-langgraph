"""Database models for SOP management."""
from datetime import datetime
import pytz

# 定义上海时区
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')

def now_shanghai():
    """返回上海时区的当前时间"""
    return datetime.now(SHANGHAI_TZ).replace(tzinfo=None)
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, UniqueConstraint
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
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

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
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

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


class AgentConfig(Base):
    """Agent Configuration model for storing complete agent configurations."""
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_name = Column(String(200), nullable=False)
    agent_description = Column(Text, nullable=True)                      # 智能体描述
    agent_capabilities = Column(JSONType, nullable=True, default=list)   # 能力列表
    agent_version = Column(String(20), default='1.0.0', nullable=False) # 智能体版本
    agent_status = Column(String(20), default='stopped', nullable=False) # 运行状态
    agent_enabled = Column(String(10), default='yes', nullable=False)        # 是否启用
    is_builtin = Column(String(10), default='no', nullable=False)    # 是否为内置智能体
    tools_info = Column(JSONType, nullable=True, default=dict)     # 工具配置
    llm_info = Column(JSONType, nullable=True, default=dict)       # 大模型配置
    prompt_info = Column(JSONType, nullable=True, default=dict)    # 提示词配置
    # 运行统计
    total_runs = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)
    avg_response_time = Column(Float, default=0.0, nullable=False)
    last_used = Column(DateTime, nullable=True)
    # 系统字段
    config_version = Column(String(20), default='1.0', nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    create_by = Column(String(100), nullable=False, default='system')
    update_by = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    def to_dict(self):
        """Convert model to dictionary."""
        # 解析工具配置
        tools_config = self.tools_info or {}
        if isinstance(tools_config, str):
            try:
                tools_config = json.loads(tools_config)
            except:
                tools_config = {}
        elif tools_config is None:
            tools_config = {}
        
        # 解析大模型配置
        llm_config = self.llm_info or {}
        if isinstance(llm_config, str):
            try:
                llm_config = json.loads(llm_config)
            except:
                llm_config = {}
        elif llm_config is None:
            llm_config = {}
        
        # 解析提示词配置
        prompt_config = self.prompt_info or {}
        if isinstance(prompt_config, str):
            try:
                prompt_config = json.loads(prompt_config)
            except:
                prompt_config = {}
        elif prompt_config is None:
            prompt_config = {}
        
        system_tools = tools_config.get('system_tools', []) if isinstance(tools_config, dict) else []
        mcp_tools_config = tools_config.get('mcp_tools', []) if isinstance(tools_config, dict) else []
        
        # 从mcp_tools配置中提取启用的服务器和所有MCP工具
        enabled_servers = []
        all_mcp_tools = []
        
        if isinstance(mcp_tools_config, list):
            for server in mcp_tools_config:
                if isinstance(server, dict):
                    if server.get('tools'):
                        enabled_servers.append(server.get('server_id', ''))
                    all_mcp_tools.extend(server.get('tools', []))
        
        # 解析能力列表
        capabilities = self.agent_capabilities or []
        if isinstance(capabilities, str):
            try:
                capabilities = json.loads(capabilities)
            except:
                capabilities = []
        elif capabilities is None:
            capabilities = []

        return {
            'id': self.id,
            'agent_id': self.agent_id,
            'name': self.agent_id,  # 前端兼容
            'agent_name': self.agent_name,
            'display_name': self.agent_name,  # 前端兼容
            'description': self.agent_description or '',
            'capabilities': capabilities,
            'version': self.agent_version,
            'status': self.agent_status,
            'enabled': self.agent_enabled == 'yes' if isinstance(self.agent_enabled, str) else self.agent_enabled,
            'is_builtin': self.is_builtin,  # 直接返回字符串 'yes'/'no'
            # 运行统计
            'total_runs': self.total_runs,
            'success_rate': self.success_rate,
            'avg_response_time': self.avg_response_time,
            'last_used': self.last_used.strftime('%Y-%m-%d %H:%M:%S') if self.last_used else None,
            # 工具配置（保持前端兼容性）
            'enabled_servers': enabled_servers,
            'selected_tools': system_tools + all_mcp_tools,
            'system_tools': system_tools,
            'mcp_tools': all_mcp_tools,
            'mcp_tools_config': mcp_tools_config,
            # MCP配置（前端兼容）
            'mcp_config': {
                'enabled_servers': enabled_servers,
                'selected_tools': system_tools + all_mcp_tools,
                'total_tools': len(system_tools) + len(all_mcp_tools)
            },
            # 完整配置信息
            'tools_info': tools_config,
            'llm_info': llm_config,
            'prompt_info': prompt_config,
            'config_version': self.config_version,
            'is_active': self.is_active,
            'create_by': self.create_by,
            'update_by': self.update_by,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }


class AIModelConfig(Base):
    """AI Model Configuration model matching ai_model_configs table."""
    __tablename__ = "ai_model_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(String(100), unique=True, index=True, nullable=False)
    model_name = Column(String(200), nullable=False)
    model_provider = Column(String(50), nullable=False, index=True)
    model_type = Column(String(100), nullable=False)
    endpoint_url = Column(String(500), nullable=False)
    api_key_value = Column(Text, nullable=True)
    model_description = Column(Text, nullable=True)
    model_status = Column(String(20), default='inactive', nullable=False, index=True)
    config_data = Column(Text, nullable=True)
    create_by = Column(String(100), nullable=False)
    update_by = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    def to_dict(self):
        """Convert model to dictionary."""
        # 处理config_data字段 - 如果是JSON字符串则解析为字典
        config_data = self.config_data
        if isinstance(config_data, str) and config_data:
            try:
                config_data = json.loads(config_data)
            except (json.JSONDecodeError, ValueError):
                config_data = {}
        elif config_data is None:
            config_data = {}

        return {
            'id': self.model_id,
            'name': self.model_name,
            'provider': self.model_provider,
            'model': self.model_type,
            'endpoint': self.endpoint_url,
            'apiKey': self.api_key_value,
            'description': self.model_description,
            'status': self.model_status,
            'config': config_data,
            'createdAt': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'updatedAt': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'createBy': self.create_by,
            'updateBy': self.update_by,
        }


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