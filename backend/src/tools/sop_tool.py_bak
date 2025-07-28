"""
SOP工具 - 标准操作程序相关工具
"""

import json
import os
from langchain_core.tools import tool
from pydantic import BaseModel, Field

def load_sop_data():
    """从知识库加载SOP数据"""
    sop_data = {}
    
    # SOP文件路径
    sop_files = [
        "src/knowledge_base/diagnostic_sop/system_sop.json",
        "src/knowledge_base/diagnostic_sop/mysql_sop.json"
    ]
    
    for file_path in sop_files:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                    sop_data.update(file_data)
        except Exception as e:
            print(f"加载SOP文件 {file_path} 失败: {e}")
    
    return sop_data

# 全局SOP数据
SOP_DATA = load_sop_data()

# Tool Schemas
class GetSOPDetailInput(BaseModel):
    """获取SOP详情工具的输入参数"""
    sop_key: str = Field(description="SOP键名，如SOP-SYS-101或SOP-DB-001")

class GetSOPContentInput(BaseModel):
    """获取SOP内容工具的输入参数"""
    sop_key: str = Field(description="SOP键名，如SOP-SYS-101或SOP-DB-001")

class ListSOPsInput(BaseModel):
    """列出所有SOP工具的输入参数"""
    category: str = Field(default="", description="SOP分类，如system、mysql")

# SOP Tools
@tool("get_sop_detail", args_schema=GetSOPDetailInput)
def get_sop_detail(sop_key: str) -> str:
    """获取SOP的详细信息
    
    Args:
        sop_key: SOP的键名，如"SOP-SYS-101"或"SOP-DB-001"
    
    Returns:
        JSON格式的SOP详细信息
    """
    try:
        if sop_key in SOP_DATA:
            return json.dumps({
                "success": True,
                "sop": SOP_DATA[sop_key]
            }, ensure_ascii=False, indent=2)
        else:
            available_sops = list(SOP_DATA.keys())
            return json.dumps({
                "success": False,
                "error": f"SOP '{sop_key}' 未找到",
                "available_sops": available_sops[:10],  # 只显示前10个
                "sop_key": sop_key
            }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "sop_key": sop_key
        }, ensure_ascii=False)

@tool("get_sop_content", args_schema=GetSOPContentInput)
def get_sop_content(sop_key: str) -> str:
    """获取SOP内容并更新诊断状态
    
    Args:
        sop_key: SOP的键名，如"SOP-SYS-101"或"SOP-DB-001"
    
    Returns:
        JSON格式的SOP内容和状态信息
    """
    try:
        if sop_key in SOP_DATA:
            sop_data = SOP_DATA[sop_key]
            # 提取SOP内容
            sop_content = {
                "id": sop_data.get("id", ""),
                "title": sop_data.get("title", ""),
                "category": sop_data.get("category", ""),
                "description": sop_data.get("description", ""),
                "severity": sop_data.get("severity", ""),
                "steps": sop_data.get("steps", []),
                "symptoms": sop_data.get("symptoms", []),
                "tools_needed": sop_data.get("tools_needed", [])
            }
            
            return json.dumps({
                "success": True,
                "sop_content": sop_content,
                "sop_state": "loaded",
                "message": f"SOP内容获取成功：{sop_key}"
            }, ensure_ascii=False, indent=2)
        else:
            available_sops = list(SOP_DATA.keys())
            return json.dumps({
                "success": False,
                "sop_content": None,
                "sop_state": "invalid",
                "error": f"SOP '{sop_key}' 未找到",
                "available_sops": available_sops[:10],
                "message": f"SOP验证失败：{sop_key}"
            }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "sop_content": None,
            "sop_state": "error",
            "error": str(e),
            "message": f"SOP验证异常：{sop_key} - {str(e)}"
        }, ensure_ascii=False, indent=2)

@tool("list_sops", args_schema=ListSOPsInput)
def list_sops(category: str = "") -> str:
    """列出所有可用的SOP
    
    Args:
        category: SOP分类，如system、mysql
    
    Returns:
        JSON格式的SOP列表
    """
    try:
        if category:
            filtered_sops = {k: v for k, v in SOP_DATA.items() 
                           if v.get("category", "").lower() == category.lower()}
        else:
            filtered_sops = SOP_DATA
        
        sop_list = []
        for key, sop in filtered_sops.items():
            sop_list.append({
                "key": key,
                "id": sop.get("id", ""),
                "title": sop.get("title", ""),
                "category": sop.get("category", ""),
                "description": sop.get("description", ""),
                "severity": sop.get("severity", "")
            })
        
        return json.dumps({
            "success": True,
            "sops": sop_list,
            "total": len(sop_list)
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)

@tool("search_sops")
def search_sops(keyword: str) -> str:
    """根据关键词搜索SOP
    
    Args:
        keyword: 搜索关键词
    
    Returns:
        JSON格式的匹配SOP列表
    """
    try:
        keyword_lower = keyword.lower()
        matched_sops = {}
        
        for key, sop in SOP_DATA.items():
            # 在标题、描述、症状中搜索
            title = sop.get("title", "").lower()
            description = sop.get("description", "").lower()
            symptoms = " ".join(sop.get("symptoms", [])).lower()
            
            if (keyword_lower in title or 
                keyword_lower in description or 
                keyword_lower in symptoms):
                matched_sops[key] = sop
        
        sop_list = []
        for key, sop in matched_sops.items():
            sop_list.append({
                "key": key,
                "id": sop.get("id", ""),
                "title": sop.get("title", ""),
                "category": sop.get("category", ""),
                "description": sop.get("description", ""),
                "severity": sop.get("severity", "")
            })
        
        return json.dumps({
            "success": True,
            "keyword": keyword,
            "sops": sop_list,
            "total": len(sop_list)
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)

# 导出工具列表
sop_tools = [get_sop_detail, get_sop_content, list_sops, search_sops] 