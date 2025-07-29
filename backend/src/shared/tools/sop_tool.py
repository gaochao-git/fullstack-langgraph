"""
SOP工具 - 标准操作程序相关工具
"""

import json
from typing import Optional, Dict, Any
from langchain_core.tools import tool
from pydantic import BaseModel, Field

# 导入数据库相关模块  
from src.shared.db.config import get_sync_db
from src.apps.sop.dao import SOPDAO


def get_sop_from_db(sop_id: str) -> Optional[Dict[str, Any]]:
    """从数据库获取单个SOP"""
    try:
        with get_sync_db() as db:
            sop_dao = SOPDAO()
            sop_template = sop_dao.sync_get_by_sop_id(db, sop_id)
            return sop_template.to_dict() if sop_template else None
    except Exception as e:
        print(f"从数据库获取SOP失败: {e}")
        return None


def search_sops_from_db(
    category: Optional[str] = None,
    search: Optional[str] = None,
    severity: Optional[str] = None,
    team_name: Optional[str] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """从数据库搜索SOPs"""
    try:
        with get_sync_db() as db:
            from src.apps.sop.models import SOPTemplate
            
            # 构建查询
            query = db.query(SOPTemplate)
            
            # 添加过滤条件
            if category:
                query = query.filter(SOPTemplate.sop_category == category)
            
            if search:
                query = query.filter(SOPTemplate.sop_title.contains(search))
            
            if severity:
                query = query.filter(SOPTemplate.sop_severity == severity)
                
            if team_name:
                query = query.filter(SOPTemplate.team_name == team_name)
            
            # 获取总数
            total = query.count()
            
            # 分页
            templates = query.limit(limit).offset(0).all()
            
            return {
                "sops": [template.to_dict() for template in templates],
                "total": total
            }
    except Exception as e:
        print(f"从数据库搜索SOPs失败: {e}")
        return {"sops": [], "total": 0}

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
        sop_data = get_sop_from_db(sop_key)
        if sop_data:
            return json.dumps({
                "success": True,
                "sop": sop_data
            }, ensure_ascii=False, indent=2)
        else:
            # 如果没有找到，搜索相似的SOP
            search_result = search_sops_from_db(search=sop_key, limit=10)
            available_sops = [sop.get("sop_id", "") for sop in search_result.get("sops", [])]
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

@tool("get_sop_content", args_schema=GetSOPContentInput)
def get_sop_content(sop_key: str) -> str:
    """获取SOP内容并更新诊断状态
    
    Args:
        sop_key: SOP的键名，如"SOP-SYS-101"或"SOP-DB-001"
    
    Returns:
        JSON格式的SOP内容和状态信息
    """
    try:
        sop_data = get_sop_from_db(sop_key)
        if sop_data:
            # 处理JSON字段
            sop_steps = sop_data.get("sop_steps", [])
            tools_required = sop_data.get("tools_required", [])
            
            # 如果是字符串，尝试解析为JSON
            if isinstance(sop_steps, str):
                try:
                    sop_steps = json.loads(sop_steps)
                except:
                    sop_steps = []
            
            if isinstance(tools_required, str):
                try:
                    tools_required = json.loads(tools_required)
                except:
                    tools_required = []
            
            # 提取SOP内容
            sop_content = {
                "id": sop_data.get("sop_id", ""),
                "title": sop_data.get("sop_title", ""),
                "category": sop_data.get("sop_category", ""),
                "description": sop_data.get("sop_description", ""),
                "severity": sop_data.get("sop_severity", ""),
                "steps": sop_steps,
                "symptoms": sop_data.get("sop_symptoms", "").split(",") if sop_data.get("sop_symptoms") else [],
                "tools_needed": tools_required
            }
            
            return json.dumps({
                "success": True,
                "sop_content": sop_content,
                "sop_state": "loaded",
                "message": f"SOP内容获取成功：{sop_key}"
            }, ensure_ascii=False, indent=2)
        else:
            # 如果没有找到，搜索相似的SOP
            search_result = search_sops_from_db(search=sop_key, limit=10)
            available_sops = [sop.get("sop_id", "") for sop in search_result.get("sops", [])]
            return json.dumps({
                "success": False,
                "sop_content": None,
                "sop_state": "invalid",
                "error": f"SOP '{sop_key}' 未找到",
                "available_sops": available_sops,
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
        search_result = search_sops_from_db(category=category, limit=50)
        sops = search_result.get("sops", [])
        
        sop_list = []
        for sop in sops:
            sop_list.append({
                "key": sop.get("sop_id", ""),
                "id": sop.get("sop_id", ""),
                "title": sop.get("sop_title", ""),
                "category": sop.get("sop_category", ""),
                "description": sop.get("sop_description", ""),
                "severity": sop.get("sop_severity", "")
            })
        
        return json.dumps({
            "success": True,
            "sops": sop_list,
            "total": search_result.get("total", len(sop_list))
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
        search_result = search_sops_from_db(search=keyword, limit=20)
        sops = search_result.get("sops", [])
        
        sop_list = []
        for sop in sops:
            sop_list.append({
                "key": sop.get("sop_id", ""),
                "id": sop.get("sop_id", ""),
                "title": sop.get("sop_title", ""),
                "category": sop.get("sop_category", ""),
                "description": sop.get("sop_description", ""),
                "severity": sop.get("sop_severity", "")
            })
        
        return json.dumps({
            "success": True,
            "keyword": keyword,
            "sops": sop_list,
            "total": search_result.get("total", len(sop_list))
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)

# 导出工具列表
sop_tools = [get_sop_detail, get_sop_content, list_sops, search_sops] 