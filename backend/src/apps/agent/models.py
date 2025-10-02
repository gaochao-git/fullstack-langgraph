"""
Agent Configuration Model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, BigInteger, Index, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.sql import func
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
    agent_enabled = Column(String(10), default='yes', nullable=False)        # 是否启用
    agent_icon = Column(String(50), nullable=True, default='Bot') # 智能体图标
    is_builtin = Column(String(10), default='no', nullable=False)    # 是否为内置智能体
    tools_info = Column(JSONType, nullable=True, default=dict)     # 工具配置
    llm_info = Column(JSONType, nullable=True, default=dict)       # 大模型配置
    prompt_info = Column(JSONType, nullable=True, default=dict)    # 提示词配置
    memory_info = Column(JSONType, nullable=True, default=dict)    # 记忆配置
    # 运行统计
    total_runs = Column(Integer, default=0, nullable=False)
    success_rate = Column(Float, default=0.0, nullable=False)
    avg_response_time = Column(Float, default=0.0, nullable=False)
    last_used = Column(DateTime, nullable=True)
    # 反馈统计
    thumbs_up_count = Column(Integer, default=0, nullable=False, comment="点赞数")
    thumbs_down_count = Column(Integer, default=0, nullable=False, comment="点踩数")
    # 系统字段
    config_version = Column(String(20), default='1.0', nullable=False)
    # 权限相关字段
    agent_owner = Column(String(100), nullable=False, default='system')  # 智能体所有者
    visibility_type = Column(String(100), nullable=False, default='public')  # 可见权限级别
    visibility_additional_users = Column(Text, nullable=True)  # 额外授权用户列表(JSON)
    favorite_users = Column(Text, nullable=True)  # 主动收藏该智能体的人员列表(JSON)
    # agent_key 字段已移除，密钥管理通过 agent_permission 表进行
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
    
    def _process_memory_info(self, value):
        """自定义处理memory_info字段 - 解析为Python字典"""
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


class AgentDocumentUpload(BaseModel):
    """智能体文档上传表"""
    __tablename__ = "agent_document_upload"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID，自增")
    file_id = Column(String(36), nullable=False, unique=True, comment="文件唯一标识符")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(BigInteger, nullable=False, comment="文件大小(字节)")
    file_type = Column(String(10), nullable=False, comment="文件扩展名")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    
    # 文档处理相关
    process_status = Column(Integer, nullable=False, default=0, comment="处理状态:0->uploaded,1->processing,2->ready,3->failed")
    error_message = Column(Text, comment="错误信息")
    
    # 文档内容和元数据
    doc_content = Column(Text, comment="提取的文档内容(限制长度)")
    doc_chunks = Column(Text, comment="文档分块内容")
    doc_metadata = Column(Text, comment="文档元数据(字符数、分块数等)")
    
    # 处理时间
    upload_time = Column(DateTime, server_default=func.now(), comment="上传时间")
    process_start_time = Column(DateTime, comment="处理开始时间")
    process_end_time = Column(DateTime, comment="处理结束时间")
    
    # 标准字段
    create_by = Column(String(100), nullable=False, default='', comment="创建人用户名")
    update_by = Column(String(100), nullable=False, default='', comment="最后更新人用户名")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_doc_file_id', 'file_id'),
        Index('idx_doc_create_by', 'create_by'),
        Index('idx_doc_status', 'process_status'),
        Index('idx_doc_create_time', 'create_time'),
    )


class AgentDocumentSession(BaseModel):
    """智能体会话文档关联表"""
    __tablename__ = "agent_document_session"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID，自增")
    thread_id = Column(String(36), nullable=False, comment="会话线程ID")
    file_id = Column(String(36), nullable=False, comment="文件ID")
    agent_id = Column(String(36), nullable=False, comment="智能体ID")
    
    # 标准字段
    create_by = Column(String(100), nullable=False, default='system', comment="创建人用户名")
    update_by = Column(String(100), comment="最后更新人用户名")
    create_time = Column(DateTime, nullable=False, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 索引
    __table_args__ = (
        Index('idx_session_thread', 'thread_id'),
        Index('idx_session_file', 'file_id'),
        Index('idx_session_agent', 'agent_id'),
        Index('idx_session_thread_file', 'thread_id', 'file_id', unique=True),
    )


class AgentPermission(BaseModel):
    """智能体权限表 - 管理agent_key与agent_id和user_name的关联"""
    __tablename__ = 'agent_permission'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment='主键ID，自增')
    agent_id = Column(String(100), nullable=False, comment='智能体id')
    agent_key = Column(String(64), nullable=True, unique=True, index=True, comment='分配的密钥')
    user_name = Column(String(64), nullable=True, comment='分配的用户名')
    is_active = Column(Boolean, nullable=False, default=True, comment='是否处于活跃状态')
    mark_comment = Column(String(100), nullable=False, default='', comment='工单号')
    create_by = Column(String(100), nullable=False, default='system', comment='创建人用户名')
    update_by = Column(String(100), nullable=True, comment='最后更新人用户名')
    create_time = Column(DateTime, nullable=False, default=now_shanghai, comment='创建时间')
    update_time = Column(DateTime, nullable=False, default=now_shanghai, onupdate=now_shanghai, comment='更新时间')
    
    __table_args__ = (
        UniqueConstraint('agent_id', 'user_name', name='agent_id_user'),
        Index('idx_permission_agent', 'agent_id'),
        Index('idx_permission_user', 'user_name'),
    )


class AgentMessageFeedback(BaseModel):
    """智能体消息反馈记录表"""
    __tablename__ = "agent_message_feedbacks"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键id")
    thread_id = Column(String(255), nullable=False, comment="会话ID", index=True)
    message_id = Column(String(255), nullable=False, comment="消息ID")
    agent_id = Column(String(100), nullable=False, comment="智能体ID", index=True)
    user_name = Column(String(100), nullable=False, comment="用户名")
    feedback_type = Column(String(20), nullable=False, comment="反馈类型: thumbs_up 或 thumbs_down")
    feedback_content = Column(Text, nullable=True, comment="反馈内容(预留)")
    create_by = Column(String(100), nullable=False, default='system', comment="创建人用户名")
    update_by = Column(String(100), nullable=True, comment="最后更新人用户名")
    create_time = Column(DateTime, default=now_shanghai, nullable=False, comment="创建时间")
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False, comment="更新时间")
    
    __table_args__ = (
        UniqueConstraint('user_name', 'message_id', name='unique_user_message_feedback'),
        Index('idx_agent_id', 'agent_id'),
        Index('idx_thread_id', 'thread_id'),
        {'comment': '智能体消息反馈记录表'}
    )


class AgentRunLog(BaseModel):
    """智能体运行日志表"""
    __tablename__ = "agent_run_logs"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    agent_id = Column(String(100), nullable=False, comment="智能体ID", index=True)
    thread_id = Column(String(255), nullable=False, comment="会话ID", index=True)
    user_name = Column(String(100), nullable=False, comment="运行用户名", index=True)
    run_status = Column(String(20), nullable=False, default='running', comment="运行状态: running, success, failed")
    start_time = Column(DateTime, nullable=False, default=now_shanghai, comment="开始运行时间")
    end_time = Column(DateTime, nullable=True, comment="结束运行时间")
    duration_ms = Column(Integer, nullable=True, comment="运行时长(毫秒)")
    error_message = Column(Text, nullable=True, comment="错误信息")
    token_usage = Column(Integer, nullable=True, comment="Token使用量")
    message_count = Column(Integer, nullable=False, default=0, comment="消息数量")
    ip_address = Column(String(50), nullable=True, comment="用户IP地址")
    user_agent = Column(Text, nullable=True, comment="用户浏览器信息")
    create_time = Column(DateTime, default=now_shanghai, nullable=False, comment="创建时间")
    
    __table_args__ = (
        Index('idx_agent_user_time', 'agent_id', 'user_name', 'start_time'),
        Index('idx_run_status', 'run_status'),
        {'comment': '智能体运行日志表'}
    )