from datetime import datetime
from langchain.tools import tool
import json

@tool("get_current_time")
def get_current_time() -> str:
    """
    获取当前服务器时间（格式：YYYY-MM-DD HH:MM:SS）
    Returns:
        JSON格式的日期详细信息
    """
    return json.dumps({
            "current_time":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })