"""
SOP工具 - 标准操作程序相关工具
"""

import json
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# 导入SOP管理器
from tools.sop_manager import get_sop_manager

# 全局SOP管理器实例
sop_manager = get_sop_manager()

# Tool Schemas
class GetSOPDetailInput(BaseModel):
    """获取SOP详情工具的输入参数"""
    sop_key: str = Field(description="SOP键名，如sop_001")

# SOP Tools
@tool("get_sop_detail", args_schema=GetSOPDetailInput)
def get_sop_detail(sop_key: str) -> str:
    """获取SOP的详细信息
    
    Args:
        sop_key: SOP的键名，如"sop_001"
    
    Returns:
        JSON格式的SOP详细信息
    """
    try:
        sop = sop_manager.get_sop(sop_key)
        if sop:
            return json.dumps({
                "success": True,
                "sop": sop
            }, ensure_ascii=False, indent=2)
        else:
            available_sops = list(sop_manager.kb.sop_data.keys())[:10]
            return json.dumps({
                "success": False,
                "error": f"SOP '{sop_key}' 未找到",
                "available_sops": available_sops,
                "sop_key": sop_key
            }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "sop_key": sop_key
        }, ensure_ascii=False)

# 导出工具列表
sop_tools = [get_sop_detail] 