import os
from pydantic import BaseModel, Field
from typing import Any, Optional
from langchain_core.runnables import RunnableConfig
from src.shared.db.config import get_sync_db
from src.shared.core.logging import get_logger
from ..llm_utils import get_model_config, get_prompt_config, create_llm_from_config

logger = get_logger(__name__)


class Configuration(BaseModel):
    """通用Agent配置类 - 极简版本"""

    # 基础配置
    agent_id: str = Field(default="generic_agent")
    agent_name: str = Field(default="通用智能体")
    
    # 模型配置（用于临时覆盖）
    model_name: Optional[str] = Field(default=None)
    model_temperature: Optional[float] = Field(default=None)
    
    # 私有字段，存储数据库会话
    _db_session: Optional[Any] = None

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """从RunnableConfig创建配置实例"""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        
        # 获取agent_id
        agent_id = configurable.get("agent_id", "generic_agent")
        
        # 获取agent名称（从数据库提示词配置中提取）
        db_gen = get_sync_db()
        db = next(db_gen)
        agent_name = "通用智能体"
        
        try:
            prompt_config = get_prompt_config(agent_id, db)
            # 从系统提示词中提取agent名称
            system_prompt = prompt_config.get("system_prompt", "")
            if "名为" in system_prompt:
                try:
                    name_start = system_prompt.index("名为") + 2
                    name_end = system_prompt.find("。", name_start)
                    if name_end > name_start:
                        agent_name = system_prompt[name_start:name_end]
                except:
                    pass
        except:
            pass
        
        # 创建实例
        instance = cls(
            agent_id=agent_id,
            agent_name=agent_name,
            model_name=configurable.get("selected_model"),
            model_temperature=configurable.get("temperature")
        )
        
        # 保存数据库会话供后续使用
        instance._db_session = db
        
        return instance

    def create_llm(self, model_name: str = None, temperature: float = None):
        """创建LLM实例"""
        # 获取数据库会话
        if hasattr(self, '_db_session') and self._db_session:
            db = self._db_session
            should_close = False
        else:
            db_gen = get_sync_db()
            db = next(db_gen)
            should_close = True
        
        try:
            # 使用公共方法创建LLM
            return create_llm_from_config(
                agent_id=self.agent_id,
                db=db,
                selected_model=model_name or self.model_name,
                temperature_override=temperature if temperature is not None else self.model_temperature
            )
        finally:
            if should_close:
                db.close()
    
    def __del__(self):
        """清理数据库会话"""
        if hasattr(self, '_db_session') and self._db_session:
            try:
                self._db_session.close()
            except:
                pass