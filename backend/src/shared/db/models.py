"""
Shared Database Models and Utilities
"""

from datetime import datetime
import pytz
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.types import TypeDecorator, Text
from sqlalchemy import Column, Integer, DateTime
import json
from .config import DATABASE_TYPE, Base

# 定义上海时区
SHANGHAI_TZ = pytz.timezone('Asia/Shanghai')


def now_shanghai():
    """返回上海时区的当前时间"""
    return datetime.now(SHANGHAI_TZ).replace(tzinfo=None)


class JSONType(TypeDecorator):
    """Cross-database JSON type."""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        elif dialect.name == 'mysql':
            return dialect.type_descriptor(JSON())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is not None:
            if dialect.name in ('postgresql', 'mysql'):
                return value
            else:
                return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            if dialect.name in ('postgresql', 'mysql'):
                return value
            else:
                return json.loads(value)
        return value


class BaseModel(Base):
    """统一的模型基类 - 提供通用的数据序列化方法"""
    __abstract__ = True
    
    def _parse_json_field(self, field_value, default=None):
        """
        统一的JSON字段解析方法
        
        Args:
            field_value: 字段值 (可能是字符串、字典、列表或None)
            default: 默认值
            
        Returns:
            解析后的Python对象
        """
        if field_value is None:
            return default
        
        if isinstance(field_value, str) and field_value.strip():
            try:
                return json.loads(field_value)
            except (json.JSONDecodeError, ValueError):
                return default
        
        # 如果已经是dict或list，直接返回
        if isinstance(field_value, (dict, list)):
            return field_value
            
        return default
    
    def _format_datetime(self, dt_value):
        """
        统一的时间格式化方法
        
        Args:
            dt_value: datetime对象
            
        Returns:
            格式化后的时间字符串 (YYYY-MM-DD HH:mm:ss) 或 None
        """
        if dt_value is None:
            return None
        
        if isinstance(dt_value, datetime):
            return dt_value.strftime('%Y-%m-%d %H:%M:%S')
        
        return str(dt_value)
    
    def to_dict(self, exclude_fields=None, include_relations=False):
        """
        统一的字典转换方法
        
        Args:
            exclude_fields: 要排除的字段列表
            include_relations: 是否包含关联关系 (暂未实现)
            
        Returns:
            字典格式的模型数据
        """
        exclude_fields = exclude_fields or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name in exclude_fields:
                continue
            
            value = getattr(self, column.name, None)
            
            # 时间字段格式化
            if isinstance(value, datetime):
                result[column.name] = self._format_datetime(value)
            # JSON字段解析 (可以被子类重写)
            elif hasattr(self, f'_process_{column.name}'):
                # 允许子类自定义特定字段的处理方法
                process_method = getattr(self, f'_process_{column.name}')
                result[column.name] = process_method(value)
            else:
                result[column.name] = value
        
        return result
    
    def to_json(self, exclude_fields=None, **kwargs):
        """
        统一的JSON转换方法
        
        Args:
            exclude_fields: 要排除的字段列表
            **kwargs: 传递给json.dumps的其他参数
            
        Returns:
            JSON字符串
        """
        data = self.to_dict(exclude_fields=exclude_fields)
        
        # 默认的JSON序列化参数
        json_kwargs = {
            'ensure_ascii': False,  # 支持中文
            'default': str,         # 处理无法序列化的对象
            'separators': (',', ':')  # 紧凑格式
        }
        json_kwargs.update(kwargs)
        
        return json.dumps(data, **json_kwargs)
    
    @classmethod
    def bulk_to_dict(cls, instances, exclude_fields=None):
        """
        批量转换为字典列表
        
        Args:
            instances: 模型实例列表
            exclude_fields: 要排除的字段列表
            
        Returns:
            字典列表
        """
        if not instances:
            return []
        
        # 处理单个对象的情况
        if not hasattr(instances, '__iter__') or isinstance(instances, (str, dict)):
            instances = [instances]
        
        return [
            instance.to_dict(exclude_fields=exclude_fields) 
            for instance in instances 
            if hasattr(instance, 'to_dict')
        ]
    
    @classmethod
    def bulk_to_json(cls, instances, exclude_fields=None, **kwargs):
        """
        批量转换为JSON字符串
        
        Args:
            instances: 模型实例列表
            exclude_fields: 要排除的字段列表
            **kwargs: 传递给json.dumps的其他参数
            
        Returns:
            JSON字符串
        """
        data = cls.bulk_to_dict(instances, exclude_fields=exclude_fields)
        
        # 默认的JSON序列化参数
        json_kwargs = {
            'ensure_ascii': False,
            'default': str,
            'separators': (',', ':')
        }
        json_kwargs.update(kwargs)
        
        return json.dumps(data, **json_kwargs)