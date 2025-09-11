from datetime import datetime
from langchain.tools import tool
import json
import pytz

@tool("get_current_time")
def get_current_time(timezone: str) -> str:
    """
    获取当前时间
    
    Args:
        timezone: 时区名称，必须为 "Asia/Shanghai"
        
    Returns:
        JSON格式的时间信息，包含上海时区的当前时间
    """
    # 验证时区参数
    if timezone != "Asia/Shanghai":
        return json.dumps({
            "error": f"不支持的时区 '{timezone}'，只接受 'Asia/Shanghai'"
        }, ensure_ascii=False)
    
    # 获取上海时区
    tz = pytz.timezone("Asia/Shanghai")
    # 获取当前时间
    current_time = datetime.now(tz)
    
    return json.dumps({
        "current_time": current_time.strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": timezone,
        "utc_offset": current_time.strftime("%z"),
        "day_of_week": current_time.strftime("%A"),
        "timestamp": int(current_time.timestamp())
    }, ensure_ascii=False)