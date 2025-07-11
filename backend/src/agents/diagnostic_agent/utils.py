"""
故障诊断代理工具函数模块
包含各种辅助工具函数
"""

import logging

logger = logging.getLogger(__name__)


def merge_field(new_value, old_value, field_name=None):
    # 合并信息：优先使用新信息，无新信息时保持原值
    # 如果新值有效且不是待提取，使用新值
    if new_value and new_value != "待提取" and new_value.strip():
        return new_value
    # 如果旧值有效且不是待提取，保持旧值
    elif old_value and old_value != "待提取" and old_value.strip():
        return old_value
    # 特殊处理：如果是时间字段且没有明确时间，使用当前时间
    elif field_name == "fault_time":
        return current_date
    # 否则返回待提取
    else:
        return "待提取"
