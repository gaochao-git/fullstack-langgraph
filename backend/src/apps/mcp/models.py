"""
MCP Server Model
"""

from sqlalchemy import Column, Integer, BigInteger, String, Text, DateTime, UniqueConstraint, Index
from sqlalchemy.dialects.mysql import TINYINT
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai, BaseModel
import json


class MCPServer(Base):
    """MCP Server model matching mcp_servers table."""
    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    server_id = Column(String(100), unique=True, index=True, nullable=False)
    server_name = Column(String(200), nullable=False)
    server_uri = Column(String(500), nullable=False)
    transport_type = Column(String(50), default='streamable-http', nullable=False)
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
            'transport_type': self.transport_type,
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


class MCPConfig(BaseModel):
    """MCP Gateway配置模型 - 对应新的mcp_configs表"""
    __tablename__ = "mcp_configs"

    id = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    config_id = Column(String(100), nullable=False, unique=True, comment="配置id")
    name = Column(String(50), nullable=False, comment="配置名称")
    tenant = Column(String(50), nullable=False, comment="租户名称")
    routers = Column(Text, nullable=True, comment="路由配置")
    servers = Column(Text, nullable=True, comment="server配置")
    tools = Column(Text, nullable=True, comment="工具配置")
    prompts = Column(Text, nullable=True, comment="提示词配置")
    mcp_servers = Column(Text, nullable=True, comment="mcpserver配置")
    is_deleted = Column(TINYINT, nullable=False, default=0, comment="是否删除:0未删除,1已删除")
    create_by = Column(String(100), nullable=False, comment="创建者")
    update_by = Column(String(100), nullable=True, comment="更新者")
    create_time = Column(DateTime, default=now_shanghai, nullable=False, comment="创建时间")
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False, comment="更新时间")

    __table_args__ = (
        UniqueConstraint('config_id', name='idx_config_id'),
        UniqueConstraint('tenant', 'name', name='uniq_tenant_name'),
        Index('idx_mcp_configs_is_deleted', 'is_deleted'),
    )

    def _process_routers(self, value):
        """自定义处理routers字段 - 解析为Python对象"""
        return self._parse_json_field(value, default=[])
    
    def _process_servers(self, value):
        """自定义处理servers字段 - 解析为Python对象"""
        return self._parse_json_field(value, default=[])
    
    def _process_tools(self, value):
        """自定义处理tools字段 - 解析为Python对象"""
        tools_list = self._parse_json_field(value, default=[])
        
        # 处理每个工具中的headers字段，确保它是对象而不是字符串
        for tool in tools_list:
            if isinstance(tool, dict) and 'headers' in tool:
                headers = tool['headers']
                if isinstance(headers, str) and headers:
                    try:
                        # 将headers字符串解析为JSON对象
                        tool['headers'] = self._parse_json_field(headers, default={})
                    except:
                        # 如果解析失败，设为空对象
                        tool['headers'] = {}
                elif not isinstance(headers, dict):
                    tool['headers'] = {}
        
        return tools_list
    
    def _process_prompts(self, value):
        """自定义处理prompts字段 - 解析为Python对象"""
        return self._parse_json_field(value, default=[])
    
    def _process_mcp_servers(self, value):
        """自定义处理mcp_servers字段 - 解析为Python对象"""
        return self._parse_json_field(value, default=[])

    def to_gateway_config(self):
        """转换为MCP Gateway配置格式"""
        return {
            "id": self.id,
            "config_id": self.config_id,
            "name": self.name,
            "tenant": self.tenant,
            "createdAt": self.create_time.strftime('%Y-%m-%dT%H:%M:%S+08:00') if self.create_time else None,
            "updatedAt": self.update_time.strftime('%Y-%m-%dT%H:%M:%S+08:00') if self.update_time else None,
            "routers": self._process_routers(self.routers),
            "servers": self._process_servers(self.servers),
            "tools": self._process_tools(self.tools),
            "prompts": self._process_prompts(self.prompts),
            "mcpServers": self._process_mcp_servers(self.mcp_servers),
        }

