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
    sop_category = Column(String(100), nullable=False, index=True)
    sop_description = Column(Text, nullable=True)
    sop_severity = Column(String(20), nullable=False, index=True)
    sop_steps = Column(JSONType, nullable=False)
    tools_required = Column(JSONType, nullable=True)
    sop_recommendations = Column(Text, nullable=True)
    team_name = Column(String(100), nullable=False, index=True)
    create_by = Column(String(100), nullable=False)
    update_by = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    def _process_sop_steps(self, value):
        """自定义处理sop_steps字段 - 解析为Python对象"""
        return self._parse_json_field(value, default=[])
    
    def _process_tools_required(self, value):
        """自定义处理tools_required字段 - 解析为Python对象"""
        return self._parse_json_field(value, default=[])