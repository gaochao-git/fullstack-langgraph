"""
Shared Database Models and Utilities
"""

from datetime import datetime
import pytz
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.types import TypeDecorator, Text
import json
from .config import DATABASE_TYPE

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