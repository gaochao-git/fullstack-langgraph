"""
通用智能体配置类 - 纯配置容器
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from langchain_core.runnables import RunnableConfig
from ..agent_utils import get_llm_config_for_agent


class Configuration(BaseModel):
    """通用智能体的配置容器"""
    
    # Agent基础信息
    agent_id: str = Field(default="generic_agent")
    
    # 运行时选择的模型（可选）
    selected_model: Optional[str] = None
    
    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """从运行配置创建实例"""
        configurable = config.get("configurable", {}) if config else {}
        
        return cls(
            agent_id=configurable.get("agent_id", "generic_agent"),
            selected_model=configurable.get("selected_model")
        )
    
    def get_llm_config(self, temperature_override: float = None) -> Dict[str, Any]:
        """获取LLM配置 - 仅返回配置数据"""
        config = get_llm_config_for_agent(
            agent_id=self.agent_id,
            selected_model=self.selected_model
        )
        
        # 如果有温度覆盖，更新配置
        if temperature_override is not None:
            config["temperature"] = temperature_override
            
        return config