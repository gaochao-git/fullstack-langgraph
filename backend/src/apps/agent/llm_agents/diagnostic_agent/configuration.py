import os
from pydantic import BaseModel, Field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig
from src.apps.agent.service.agent_config_service import AgentConfigService
from src.shared.db.config import get_sync_db
from langchain_openai import ChatOpenAI
from src.shared.core.logging import get_logger
import httpx

logger = get_logger(__name__)


class Configuration(BaseModel):
    """The configuration for the agent."""

    query_generator_model: str = Field(default="deepseek-chat",metadata={"description": "The name of the language model to use for the agent's query generation."})
    reflection_model: str = Field(default="deepseek-chat",metadata={"description": "The name of the language model to use for the agent's reflection."})
    answer_model: str = Field(default="deepseek-chat",metadata={"description": "The name of the language model to use for the agent's answer."})
    # 模型配置参数
    model_api_key: Optional[str] = Field(default=None,metadata={"description": "API key for the model provider. If not provided, will use environment variable."})
    model_base_url: str = Field(default="https://api.deepseek.com",metadata={"description": "Base URL for the model API endpoint."})
    model_temperature: float = Field(default=0.1,metadata={"description": "Temperature for model inference. Lower values are more deterministic."})
    model_max_retries: int = Field(default=2,metadata={"description": "Maximum number of retries for model API calls."})
    # 特殊节点的温度配置
    question_analysis_temperature: float = Field(default=1.0,metadata={"description": "Temperature for question analysis (higher for better extraction)."})
    tool_planning_temperature: float = Field(default=0.1,metadata={"description": "Temperature for tool planning (lower for more deterministic execution)."})
    final_report_temperature: float = Field(default=0.0,metadata={"description": "Temperature for final report generation (lowest for consistency)."})
    number_of_initial_queries: int = Field(default=3,metadata={"description": "The number of initial search queries to generate."})
    max_research_loops: int = Field(default=2,metadata={"description": "The maximum number of research loops to perform."})
    max_diagnosis_steps: int = Field(default=10,metadata={"description": "The maximum number of diagnosis steps to perform."})

    def get_api_key(self) -> str:
        """Get the API key from configuration or environment."""
        if self.model_api_key:
            return self.model_api_key   
        
        # Try different environment variables based on base_url
        api_key = None
        match self.model_base_url:
            case url if "deepseek.com" in url:
                api_key = os.environ.get("DEEPSEEK_API_KEY")
            case url if "openai.com" in url or "api.openai.com" in url:
                api_key = os.environ.get("OPENAI_API_KEY")
            case url if "anthropic.com" in url:
                api_key = os.environ.get("ANTHROPIC_API_KEY")
            case url if "zhipuai.cn" in url:
                api_key = os.environ.get("ZHIPUAI_API_KEY")
            case url if "moonshot.cn" in url:
                api_key = os.environ.get("MOONSHOT_API_KEY")
            case url if "dashscope.aliyuncs.com" in url:
                api_key = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("ALIBABA_CLOUD_API_KEY")
            case _:
                # Default fallback
                api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(f"No API key found for {self.model_base_url}. Please set the appropriate environment variable or configure model_api_key.")
        
        return api_key

    def create_llm(self, model_name: str = None, temperature: float = None) -> 'ChatOpenAI':
        """Create a ChatOpenAI instance with the configured settings."""
        
        # 确定实际使用的模型和参数
        actual_model = model_name or self.query_generator_model
        actual_temperature = temperature if temperature is not None else self.model_temperature
        
        # 记录模型使用信息
        logger.info(f"创建LLM实例: 模型={actual_model}, 温度={actual_temperature}, API端点={self.model_base_url}")
        if self.get_api_key():
            logger.debug(f"API密钥: {self.get_api_key()[:15]}...")
        else:
            logger.warning("API密钥: 未设置")
        
        # 创建自定义 httpx 客户端，忽略 SSL 验证
        http_client = httpx.Client(verify=False)
        
        return ChatOpenAI(
            model=actual_model,
            temperature=actual_temperature,
            max_retries=self.model_max_retries,
            api_key=self.get_api_key(),
            base_url=self.model_base_url,
            http_client=http_client  # 使用自定义 HTTP 客户端
        )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Try to load configuration from database first
        # 优先从configurable获取agent_id
        agent_name = configurable.get("agent_id") 
        if not agent_name:
            # 如果没有agent_id，则使用默认值（用于向后兼容）
            agent_name = "diagnostic_agent"
        
        selected_model = configurable.get("selected_model")
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            db_config = AgentConfigService.get_model_config_from_agent(agent_name, db, selected_model)
        finally:
            db.close()
        # Get raw values from database, environment, or config (in that order)
        raw_values: dict[str, Any] = {}
        for name in cls.model_fields.keys():
            value = None
            
            # Map database config to configuration fields
            if name == "query_generator_model" or name == "reflection_model" or name == "answer_model":
                value = db_config.get("model_name")
            elif name == "model_temperature":
                value = db_config.get("temperature")
            elif name == "model_base_url":
                value = db_config.get("base_url")
            elif name == "model_api_key":
                value = db_config.get("api_key")
            
            # Fallback to environment or configurable
            if value is None:
                value = os.environ.get(name.upper(), configurable.get(name))
                
            raw_values[name] = value

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)
    
    @classmethod
    def from_agent_config(cls, agent_name: str = "diagnostic_agent", selected_model: str = None) -> "Configuration":
        """Create a Configuration instance directly from agent database configuration."""
        db_gen = get_sync_db()
        db = next(db_gen)
        try:
            db_config = AgentConfigService.get_model_config_from_agent(agent_name, db, selected_model)
        finally:
            db.close()
        
        # Map database configuration to Configuration fields
        config_values = {
            "query_generator_model": db_config.get("model_name", "deepseek-chat"),
            "reflection_model": db_config.get("model_name", "deepseek-chat"), 
            "answer_model": db_config.get("model_name", "deepseek-chat"),
            "model_temperature": db_config.get("temperature", 0.1),
            "model_base_url": db_config.get("base_url", "https://api.deepseek.com"),
        }
        
        # Add API key if available from database
        if db_config.get("api_key"):
            config_values["model_api_key"] = db_config.get("api_key")
        
        return cls(**config_values)
