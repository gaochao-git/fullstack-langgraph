"""
示例智能体配置类 - 纯配置容器
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from langchain_core.runnables import RunnableConfig
from ..agent_utils import get_llm_config_for_agent

# Agent 装饰器配置，首次注册使用，如果后续需要更新，需要手动更新数据库
INIT_AGENT_CONFIG = {
    "agent_id": "example_agent",
    "description": "示例助手 - 展示自定义工作流",
    "agent_type": "内置",
    "capabilities": ["文本分析", "字数统计", "工作流演示", "条件路由"],
    "version": "1.0.0",
    "icon": "WorkflowOutlined",
    "owner": "system"
}


class Configuration(BaseModel):
    """示例智能体的配置容器"""
    
    # 运行时选择的模型（可选）
    selected_model: Optional[str] = None
    
    # 示例智能体特有配置（如果需要）
    enable_debug: bool = Field(default=False, description="是否启用调试模式")
    max_text_length: int = Field(default=10000, description="最大处理文本长度")
    
    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """从运行配置创建实例"""
        configurable = config.get("configurable", {}) if config else {}
        
        return cls(
            selected_model=configurable.get("selected_model"),
            enable_debug=configurable.get("enable_debug", False),
            max_text_length=configurable.get("max_text_length", 10000)
        )
    
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置 - 直接使用 agent_utils 的方法"""
        return get_llm_config_for_agent(
            agent_id=INIT_AGENT_CONFIG["agent_id"],  # 内置智能体使用文件中定义的常量
            selected_model=self.selected_model
        )