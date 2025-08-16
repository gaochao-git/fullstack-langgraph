"""
Agent Configuration Model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float
from src.shared.db.models import JSONType, now_shanghai, BaseModel


class AgentConfig(BaseModel):
    """Agent Configuration model for storing complete agent configurations."""
    __tablename__ = "agent_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_id = Column(String(100), unique=True, index=True, nullable=False)
    agent_name = Column(String(200), nullable=False)
    agent_type = Column(String(32), nullable=False, default='故障诊断')      # 智能体分类
    agent_description = Column(Text, nullable=True)                      # 智能体描述
    agent_capabilities = Column(JSONType, nullable=True, default=list)   # 能力列表
    agent_version = Column(String(20), default='1.0.0', nullable=False) # 智能体版本
    agent_status = Column(String(20), default='stopped', nullable=False) # 运行状态
    agent_enabled = Column(String(10), default='yes', nullable=False)        # 是否启用
    agent_icon = Column(String(50), nullable=True, default='Bot') # 智能体图标
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
    # 权限相关字段
    agent_owner = Column(String(100), nullable=False, default='system')  # 智能体所有者
    visibility_type = Column(String(100), nullable=False, default='public')  # 可见权限级别
    visibility_additional_users = Column(Text, nullable=True)  # 额外授权用户列表(JSON)
    favorite_users = Column(Text, nullable=True)  # 主动收藏该智能体的人员列表(JSON)
    create_by = Column(String(100), nullable=False, default='system')
    update_by = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    def _process_agent_capabilities(self, value):
        """自定义处理agent_capabilities字段 - 解析为Python列表"""
        return self._parse_json_field(value, default=[])
    
    def _process_tools_info(self, value):
        """自定义处理tools_info字段 - 解析为Python字典"""
        return self._parse_json_field(value, default={})
    
    def _process_llm_info(self, value):
        """自定义处理llm_info字段 - 解析为Python字典"""
        return self._parse_json_field(value, default={})
    
    def _process_prompt_info(self, value):
        """自定义处理prompt_info字段 - 解析为Python字典"""
        return self._parse_json_field(value, default={})
    
    def _process_visibility_additional_users(self, value):
        """自定义处理visibility_additional_users字段 - 解析为Python列表"""
        import json
        if value is None or value == '':
            return []
        if isinstance(value, list):
            return value
        try:
            return json.loads(value) if isinstance(value, str) else []
        except:
            return []
    
    def _process_favorite_users(self, value):
        """自定义处理favorite_users字段 - 解析为Python列表"""
        import json
        if value is None or value == '':
            return []
        if isinstance(value, list):
            return value
        try:
            return json.loads(value) if isinstance(value, str) else []
        except:
            return []