#!/usr/bin/env python3
"""
SOP Tools MCP Server
标准操作程序(SOP)工具MCP服务器
"""

import json
import logging
from typing import Dict, Any, Optional, List
import sys
import os

# 添加父目录到系统路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastmcp import FastMCP
import pymysql
from load_config import get_sop_config

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("SOP Tools Server")

def _create_mysql_connection():
    """创建新的MySQL连接，每次调用都重新连接"""
    # 从统一配置获取SOP数据库配置
    sop_config = get_sop_config()
    
    try:
        connection_config = {
            'host': sop_config['host'],
            'port': sop_config['port'],
            'user': sop_config['username'],
            'password': sop_config['password'],
            'charset': 'utf8mb4',
            'autocommit': True,
            'database': sop_config.get('database', 'omind')
        }
        
        connection = pymysql.connect(**connection_config)
        logger.info(f"MySQL连接成功，主机: {sop_config['host']}, 数据库: {sop_config.get('database')}")
        return connection
        
    except Exception as e:
        logger.error(f"MySQL连接失败: {e}")
        raise Exception(f"无法建立MySQL连接: {str(e)}")

def _execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """执行查询并返回结果"""
    connection = None
    try:
        connection = _create_mysql_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        logger.debug(f"Executing query: {query}")
        logger.debug(f"With params: {params}")
        
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        results = cursor.fetchall()
        cursor.close()
        logger.debug(f"Query returned {len(results)} rows")
        return results
        
    except Exception as e:
        logger.error(f"查询执行失败: {e}")
        logger.error(f"Query was: {query}")
        logger.error(f"Params were: {params}")
        return []
    finally:
        if connection:
            connection.close()

@mcp.tool()
async def get_sop_detail(sop_key: str) -> str:
    """获取SOP的详细信息
    
    Args:
        sop_key: SOP的键名，如"SOP-SYS-101"或"SOP-DB-001"
    
    Returns:
        JSON格式的SOP详细信息
    """
    try:
        query = """
        SELECT * FROM sop_prompt_templates 
        WHERE sop_id = %s
        LIMIT 1
        """
        results = _execute_query(query, (sop_key,))
        
        if results:
            sop_data = results[0]
            # 处理JSON字段
            for field in ['sop_steps', 'tools_required']:
                if field in sop_data and isinstance(sop_data[field], str):
                    try:
                        sop_data[field] = json.loads(sop_data[field])
                    except:
                        sop_data[field] = []
            
            return json.dumps({
                "success": True,
                "sop": sop_data
            }, ensure_ascii=False, indent=2, default=str)
        else:
            # 如果没有找到，搜索相似的SOP
            search_query = """
            SELECT sop_id FROM sop_prompt_templates 
            WHERE sop_title LIKE %s
            LIMIT 10
            """
            search_results = _execute_query(search_query, (f'%{sop_key}%',))
            available_sops = [r['sop_id'] for r in search_results]
            
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

@mcp.tool()
async def get_sop_content(sop_key: str) -> str:
    """获取SOP内容并更新诊断状态
    
    Args:
        sop_key: SOP的键名，如"SOP-SYS-101"或"SOP-DB-001"
    
    Returns:
        JSON格式的SOP内容和状态信息
    """
    try:
        logger.info(f"Getting SOP content for: {sop_key}")
        query = """
        SELECT sop_id, sop_title, sop_category, sop_description, 
               sop_severity, sop_steps, tools_required
        FROM sop_prompt_templates 
        WHERE sop_id = %s
        LIMIT 1
        """
        results = _execute_query(query, (sop_key,))
        logger.info(f"Query results: {len(results) if results else 0} rows found")
        
        if results:
            sop_data = results[0]
            
            # 处理JSON字段
            sop_steps = sop_data.get("sop_steps", [])
            tools_required = sop_data.get("tools_required", [])
            
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
            search_query = """
            SELECT sop_id FROM sop_prompt_templates 
            WHERE sop_title LIKE %s
            LIMIT 10
            """
            search_results = _execute_query(search_query, (f'%{sop_key}%',))
            available_sops = [r['sop_id'] for r in search_results]
            
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

@mcp.tool()
async def list_sops(category: str = "") -> str:
    """列出所有可用的SOP
    
    Args:
        category: SOP分类，如system、mysql
    
    Returns:
        JSON格式的SOP列表
    """
    try:
        if category:
            query = """
            SELECT sop_id, sop_title, sop_category, sop_description, sop_severity 
            FROM sop_prompt_templates
            WHERE sop_category = %s
            LIMIT 50
            """
            results = _execute_query(query, (category,))
        else:
            query = """
            SELECT sop_id, sop_title, sop_category, sop_description, sop_severity 
            FROM sop_prompt_templates
            LIMIT 50
            """
            results = _execute_query(query)
        
        sop_list = []
        for sop in results:
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
            "total": len(sop_list)
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)

@mcp.tool()
async def search_sops(keyword: str) -> str:
    """根据关键词搜索SOP
    
    Args:
        keyword: 搜索关键词
    
    Returns:
        JSON格式的匹配SOP列表
    """
    try:
        query = """
        SELECT sop_id, sop_title, sop_category, sop_description, sop_severity 
        FROM sop_prompt_templates
        WHERE sop_title LIKE %s OR sop_description LIKE %s
        LIMIT 20
        """
        pattern = f'%{keyword}%'
        results = _execute_query(query, (pattern, pattern))
        
        sop_list = []
        for sop in results:
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
            "total": len(sop_list)
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False)

if __name__ == "__main__":
    # 使用SSE传输方式启动服务器
    mcp.run(transport="streamable-http", host="0.0.0.0", port=3005)