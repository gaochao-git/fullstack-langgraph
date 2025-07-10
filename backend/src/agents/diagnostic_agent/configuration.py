import os
from pydantic import BaseModel, Field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig


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
            case _:
                # Default fallback
                api_key = os.environ.get("DEEPSEEK_API_KEY") or os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError(f"No API key found for {self.model_base_url}. Please set the appropriate environment variable or configure model_api_key.")
        
        return api_key

    def create_llm(self, model_name: str = None, temperature: float = None) -> 'ChatOpenAI':
        """Create a ChatOpenAI instance with the configured settings."""
        from langchain_openai import ChatOpenAI
        
        return ChatOpenAI(
            model=model_name or self.query_generator_model,
            temperature=temperature if temperature is not None else self.model_temperature,
            max_retries=self.model_max_retries,
            api_key=self.get_api_key(),
            base_url=self.model_base_url,
        )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {
            name: os.environ.get(name.upper(), configurable.get(name))
            for name in cls.model_fields.keys()
        }

        # Filter out None values
        values = {k: v for k, v in raw_values.items() if v is not None}

        return cls(**values)
