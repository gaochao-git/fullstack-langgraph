"""
SOP Template Model
"""

from sqlalchemy import Column, Integer, String, Text, DateTime
from src.shared.db.config import Base
from src.shared.db.models import JSONType, now_shanghai
import json


class SOPTemplate(Base):
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

    def to_dict(self):
        """Convert model to dictionary."""
        return {
            'id': self.id,
            'sop_id': self.sop_id,
            'sop_title': self.sop_title,
            'sop_category': self.sop_category,
            'sop_description': self.sop_description,
            'sop_severity': self.sop_severity,
            'sop_steps': json.dumps(self.sop_steps) if isinstance(self.sop_steps, (dict, list)) else self.sop_steps,
            'tools_required': json.dumps(self.tools_required) if isinstance(self.tools_required, (dict, list)) else self.tools_required,
            'sop_recommendations': self.sop_recommendations,
            'team_name': self.team_name,
            'create_by': self.create_by,
            'update_by': self.update_by,
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
        }