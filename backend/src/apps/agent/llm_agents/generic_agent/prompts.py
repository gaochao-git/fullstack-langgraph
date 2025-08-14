"""
提示词管理模块，多转了一层，为了保持和官方一样的目录结构
"""
from ..prompt_utils import get_system_prompt_from_db

# 直接使用统一的数据库获取方法
get_system_prompt = get_system_prompt_from_db


