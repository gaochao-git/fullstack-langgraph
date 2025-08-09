import os
from pydantic import BaseModel, Field
from typing import Any, Optional, List, Dict
from langchain_core.runnables import RunnableConfig
from src.apps.agent.service.agent_config_service import AgentConfigService
from src.shared.db.config import get_sync_db
from langchain_openai import ChatOpenAI


class Configuration(BaseModel):
    """通用Agent配置类，支持完全可配置化的Agent创建"""

    # === 基础Agent配置 ===
    agent_id: str = Field(
        default="generic_agent",
        metadata={"description": "Agent的唯一标识符"}
    )
    
    agent_name: str = Field(
        default="通用智能体",
        metadata={"description": "Agent的显示名称"}
    )
    
    agent_description: str = Field(
        default="可配置的通用智能体，支持多种模型和工具",
        metadata={"description": "Agent的描述信息"}
    )

    # === 模型配置 ===
    model_provider: str = Field(
        default="deepseek",
        metadata={"description": "模型提供商: deepseek, openai, ollama, qwen"}
    )
    
    model_name: str = Field(
        default="deepseek-chat",
        metadata={"description": "使用的具体模型名称"}
    )
    
    model_temperature: float = Field(
        default=0.1,
        metadata={"description": "模型温度参数，控制输出随机性"}
    )
    
    model_max_tokens: Optional[int] = Field(
        default=4000,
        metadata={"description": "模型最大输出token数"}
    )
    
    model_max_retries: int = Field(
        default=3,
        metadata={"description": "模型调用最大重试次数"}
    )

    # === 工作流配置 ===
    workflow_type: str = Field(
        default="react",
        metadata={"description": "工作流类型: react(推理行动), custom(自定义图)"}
    )
    
    max_iterations: int = Field(
        default=10,
        metadata={"description": "最大执行步骤数"}
    )
    
    enable_memory: bool = Field(
        default=True,
        metadata={"description": "是否启用对话记忆"}
    )
    
    enable_streaming: bool = Field(
        default=True,
        metadata={"description": "是否启用流式输出"}
    )

    # === 工具配置 ===
    enabled_tool_categories: List[str] = Field(
        default=["search", "calculation", "text_processing"],
        metadata={"description": "启用的工具类别列表"}
    )
    
    custom_tools: List[str] = Field(
        default=[],
        metadata={"description": "自定义工具列表"}
    )
    
    enable_mcp_tools: bool = Field(
        default=True,
        metadata={"description": "是否启用MCP工具集成"}
    )
    
    require_approval_tools: List[str] = Field(
        default=[],
        metadata={"description": "需要人工审批的工具列表"}
    )

    # === 提示词配置 ===
    system_prompt_template: Optional[str] = Field(
        default=None,
        metadata={"description": "自定义系统提示词模板"}
    )
    
    role_description: str = Field(
        default="你是一个有用的AI助手，能够使用各种工具来帮助用户解决问题。",
        metadata={"description": "Agent的角色描述"}
    )
    
    personality_traits: List[str] = Field(
        default=["helpful", "professional", "accurate"],
        metadata={"description": "Agent的性格特征"}
    )

    # === 安全配置 ===
    enable_content_filter: bool = Field(
        default=True,
        metadata={"description": "是否启用内容过滤"}
    )
    
    max_tool_calls_per_turn: int = Field(
        default=5,
        metadata={"description": "每轮对话最大工具调用次数"}
    )
    
    timeout_seconds: int = Field(
        default=300,
        metadata={"description": "执行超时时间（秒）"}
    )

    # === 实验性功能 ===
    enable_self_reflection: bool = Field(
        default=False,
        metadata={"description": "是否启用自我反思功能"}
    )
    
    enable_parallel_execution: bool = Field(
        default=False,
        metadata={"description": "是否启用并行执行"}
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """从RunnableConfig创建配置实例，支持数据库配置覆盖"""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        
        # 获取agent_id，优先使用configurable中的值
        agent_id = configurable.get("agent_id", "generic_agent")
        
        # 从数据库加载配置
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            db_config = AgentConfigService.get_agent_config(agent_id, db)
        finally:
            db.close()
        
        # 合并配置优先级: configurable > 数据库 > 环境变量 > 默认值
        raw_values: Dict[str, Any] = {}
        
        # 1. 先应用默认值（通过Pydantic字段定义）
        for name, field_info in cls.model_fields.items():
            default_value = field_info.default
            if default_value is not None:
                raw_values[name] = default_value
        
        # 2. 应用环境变量
        for name in cls.model_fields.keys():
            env_value = os.environ.get(f"AGENT_{name.upper()}")
            if env_value is not None:
                # 简单类型转换
                if name in ["model_temperature"]:
                    raw_values[name] = float(env_value)
                elif name in ["model_max_tokens", "model_max_retries", "max_iterations", "max_tool_calls_per_turn", "timeout_seconds"]:
                    raw_values[name] = int(env_value)
                elif name in ["enable_memory", "enable_streaming", "enable_mcp_tools", "enable_content_filter", "enable_self_reflection", "enable_parallel_execution"]:
                    raw_values[name] = env_value.lower() in ["true", "1", "yes"]
                elif name in ["enabled_tool_categories", "custom_tools", "require_approval_tools", "personality_traits"]:
                    raw_values[name] = env_value.split(",") if env_value else []
                else:
                    raw_values[name] = env_value
        
        # 3. 应用数据库配置
        if db_config:
            raw_values.update(db_config)
        
        # 4. 应用运行时configurable配置
        raw_values.update(configurable)
        
        # 过滤None值
        values = {k: v for k, v in raw_values.items() if v is not None}
        
        return cls(**values)
    
    def get_api_key(self) -> str:
        """获取API密钥，参考diagnostic_agent的实现"""
        # 这里简化处理，主要使用环境变量
        api_key = None
        
        if self.model_provider.lower() == "deepseek":
            api_key = os.environ.get("DEEPSEEK_API_KEY")
        elif self.model_provider.lower() == "openai":
            api_key = os.environ.get("OPENAI_API_KEY")
        else:
            # 默认尝试DEEPSEEK_API_KEY
            api_key = os.environ.get("DEEPSEEK_API_KEY")
        
        if not api_key:
            raise ValueError(f"No API key found for provider {self.model_provider}. Please set the appropriate environment variable.")
        
        return api_key

    def create_llm(self, model_name: Optional[str] = None, temperature: Optional[float] = None):
        """创建LLM实例，参考diagnostic_agent的实现"""
        
        # 使用传入的参数或配置中的默认值
        actual_model = model_name or self.model_name
        actual_temp = temperature if temperature is not None else self.model_temperature
        
        # 获取base_url - 根据provider设置默认值
        base_url = "https://api.deepseek.com" if self.model_provider.lower() == "deepseek" else "https://api.openai.com/v1"
        
        print(f"🤖 创建通用Agent LLM实例:")
        print(f"   提供商: {self.model_provider}")
        print(f"   模型: {actual_model}")
        print(f"   温度: {actual_temp}")
        print(f"   API端点: {base_url}")
        
        return ChatOpenAI(
            model=actual_model,
            temperature=actual_temp,
            max_tokens=self.model_max_tokens,
            max_retries=self.model_max_retries,
            api_key=self.get_api_key(),
            base_url=base_url,
        )

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典，用于保存到数据库"""
        return self.model_dump(exclude_none=True)
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型相关配置"""
        return {
            "provider": self.model_provider,
            "model": self.model_name,
            "temperature": self.model_temperature,
            "max_tokens": self.model_max_tokens,
            "max_retries": self.model_max_retries
        }
    
    def get_tool_config(self) -> Dict[str, Any]:
        """获取工具相关配置"""
        return {
            "enabled_categories": self.enabled_tool_categories,
            "custom_tools": self.custom_tools,
            "enable_mcp": self.enable_mcp_tools,
            "require_approval": self.require_approval_tools,
            "max_calls_per_turn": self.max_tool_calls_per_turn
        }
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流相关配置"""
        return {
            "type": self.workflow_type,
            "max_iterations": self.max_iterations,
            "enable_memory": self.enable_memory,
            "enable_streaming": self.enable_streaming,
            "timeout_seconds": self.timeout_seconds
        }