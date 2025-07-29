"""
Agent Configuration Model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from src.shared.db.config import Base
from src.shared.db.models import JSONType, now_shanghai
import json


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
            'agent_description': self.agent_description or '',
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