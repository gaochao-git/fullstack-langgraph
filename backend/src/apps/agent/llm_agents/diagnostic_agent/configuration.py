"""
诊断智能体配置类 - 纯配置容器
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from langchain_core.runnables import RunnableConfig
from ..agent_utils import get_llm_config_for_agent


class Configuration(BaseModel):
    """诊断智能体的配置容器"""
    
    # Agent基础信息
    agent_id: str = Field(default="diagnostic_agent")
    
    # 特殊配置（诊断智能体特有）
    question_analysis_temperature: float = Field(default=1.0, description="问题分析温度")
    tool_planning_temperature: float = Field(default=0.1, description="工具规划温度")
    final_report_temperature: float = Field(default=0.0, description="最终报告温度")
    number_of_initial_queries: int = Field(default=3, description="初始查询数量")
    max_research_loops: int = Field(default=2, description="最大研究循环数")
    max_diagnosis_steps: int = Field(default=10, description="最大诊断步骤数")
    
    # 运行时选择的模型（可选）
    selected_model: Optional[str] = None
    
    @classmethod
    def from_runnable_config(cls, config: Optional[RunnableConfig] = None) -> "Configuration":
        """从运行配置创建实例"""
        configurable = config.get("configurable", {}) if config else {}
        
        return cls(
            agent_id=configurable.get("agent_id", "diagnostic_agent"),
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