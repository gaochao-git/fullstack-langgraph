"""
MCP Server Model
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import TINYINT
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai
import json


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


class OpenAPIMCPConfig(Base):
    """OpenAPI MCP配置模型"""
    __tablename__ = "openapi_mcp_configs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    mcp_server_prefix = Column(String(255), nullable=False, comment="mcpserver前缀")
    mcp_tool_name = Column(String(255), nullable=False, comment="工具名称")
    mcp_tool_enabled = Column(TINYINT, nullable=False, default=0, comment="是否开启:0关闭,1开启")
    openapi_schema = Column(Text, nullable=False, comment="原始OpenAPI规范JSON/YAML")
    auth_config = Column(Text, nullable=False, comment="认证配置")
    extra_config = Column(Text, nullable=False, comment="其他配置")
    is_deleted = Column(TINYINT, nullable=False, default=0, comment="是否删除:0未删除,1已删除")
    create_by = Column(String(100), nullable=False, comment="创建者")
    update_by = Column(String(100), nullable=True, comment="更新者") 
    create_time = Column(DateTime, nullable=False, default=now_shanghai, comment="创建时间")
    update_time = Column(DateTime, nullable=False, default=now_shanghai, onupdate=now_shanghai, comment="更新时间")
    
    __table_args__ = (
        UniqueConstraint('mcp_server_prefix', 'mcp_tool_name', name='uniq_prefix_tool'),
        Index('idx_mcp_tool_name', 'mcp_tool_name'),
        Index('idx_create_time', 'create_time'),
    )

    def to_dict(self):
        """转换为字典格式"""
        result = {
            'id': self.id,
            'mcp_server_prefix': self.mcp_server_prefix,
            'mcp_tool_name': self.mcp_tool_name,
            'mcp_tool_enabled': self.mcp_tool_enabled,
            'openapi_schema': self.openapi_schema,
            'auth_config': self.auth_config,
            'extra_config': self.extra_config,
            'is_deleted': self.is_deleted,
            'create_by': self.create_by,
            'update_by': self.update_by,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None
        }
        
        # 解析JSON字段
        try:
            if self.openapi_schema:
                result['openapi_schema'] = json.loads(self.openapi_schema)
        except (json.JSONDecodeError, TypeError):
            pass
        
        try:
            if self.auth_config:
                result['auth_config'] = json.loads(self.auth_config)
        except (json.JSONDecodeError, TypeError):
            pass
        
        try:
            if self.extra_config:
                result['extra_config'] = json.loads(self.extra_config)
        except (json.JSONDecodeError, TypeError):
            pass
        
        return result