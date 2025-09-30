"""
SOP Template Model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from src.shared.db.config import Base
from src.shared.db.models import JSONType, now_shanghai, BaseModel
import json


class SOPTemplate(BaseModel):
    """SOP Template model matching sop_prompt_templates table."""
    __tablename__ = "sop_prompt_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sop_id = Column(String(100), unique=True, index=True, nullable=False)
    sop_title = Column(String(500), nullable=False)
    sop_description = Column(Text, nullable=False)  # 包含所有SOP步骤的文本描述（必填）
    create_by = Column(String(100), nullable=False)
    update_by = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)


class SOPProblemRule(BaseModel):
    """SOP问题规则模型"""
    __tablename__ = "sop_problem_rule"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    rule_name = Column(String(200), nullable=False, comment="规则名称")
    sop_id = Column(String(100), nullable=False, index=True, comment="关联SOP ID")
    rules_info = Column(JSONType, nullable=False, comment="规则信息JSON")
    is_enabled = Column(Integer, nullable=False, default=1, comment="是否启用")
    created_by = Column(String(100), nullable=False, comment="创建人")
    updated_by = Column(String(100), nullable=True, comment="更新人")
    create_time = Column(DateTime, default=now_shanghai, nullable=False, comment="创建时间")
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False, comment="更新时间")
    
    def _process_rules_info(self, value):
        """自定义处理rules_info字段 - 解析为Python对象"""
        return self._parse_json_field(value, default={"source_type": "zabbix", "item_keys": []})