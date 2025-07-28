"""AI Model Configuration model."""
import json
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from src.shared.db.config import Base
from src.shared.db.models import now_shanghai


class AIModelConfig(Base):
    """AI Model Configuration model matching ai_model_configs table."""
    __tablename__ = "ai_model_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(String(100), unique=True, index=True, nullable=False)
    model_name = Column(String(200), nullable=False)
    model_provider = Column(String(50), nullable=False, index=True)
    model_type = Column(String(100), nullable=False)
    endpoint_url = Column(String(500), nullable=False)
    api_key_value = Column(Text, nullable=True)
    model_description = Column(Text, nullable=True)
    model_status = Column(String(20), default='inactive', nullable=False, index=True)
    config_data = Column(Text, nullable=True)
    create_by = Column(String(100), nullable=False)
    update_by = Column(String(100), nullable=True)
    create_time = Column(DateTime, default=now_shanghai, nullable=False)
    update_time = Column(DateTime, default=now_shanghai, onupdate=now_shanghai, nullable=False)

    def to_dict(self):
        """Convert model to dictionary."""
        # 处理config_data字段 - 如果是JSON字符串则解析为字典
        config_data = self.config_data
        if isinstance(config_data, str) and config_data:
            try:
                config_data = json.loads(config_data)
            except (json.JSONDecodeError, ValueError):
                config_data = {}
        elif config_data is None:
            config_data = {}

        return {
            'id': self.model_id,
            'name': self.model_name,
            'provider': self.model_provider,
            'model': self.model_type,
            'endpoint': self.endpoint_url,
            'apiKey': self.api_key_value,
            'description': self.model_description,
            'status': self.model_status,
            'config': config_data,
            'createdAt': self.create_time.strftime('%Y-%m-%d %H:%M:%S') if self.create_time else None,
            'updatedAt': self.update_time.strftime('%Y-%m-%d %H:%M:%S') if self.update_time else None,
            'createBy': self.create_by,
            'updateBy': self.update_by,
        }