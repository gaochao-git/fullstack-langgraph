#!/usr/bin/env python3
"""
SOP Tools MCP Server
标准操作程序(SOP)工具MCP服务器
"""

import json
import logging
from typing import Dict, Any, Optional, List
import os
import pymysql
from fastmcp import FastMCP
from ..common.base_config import MCPServerConfig

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("SOP Tools Server")

# 加载配置
config = MCPServerConfig('sop_server')

def _create_mysql_connection():
    """创建新的MySQL连接，每次调用都重新连接"""
    try:
        connection_config = {
            'host': config.get('db_host', config.get('host')),  # 兼容旧配置
            'port': config.get('db_port', 3306),
            'user': config.get('db_username', config.get('username')),  # 兼容旧配置
            'password': config.get('db_password', config.get('password')),  # 兼容旧配置
            'charset': 'utf8mb4',
            'autocommit': True,
            'database': config.get('db_database', config.get('database', 'omind')),  # 兼容旧配置
            'connect_timeout': 20  # 增加连接超时时间
        }
        
        connection = pymysql.connect(**connection_config)
        logger.info(f"MySQL连接成功，主机: {connection_config['host']}, 数据库: {connection_config['database']}")
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
async def get_sop_content(sop_id: str) -> str:
    """获取SOP内容

    Args:
        sop_id: SOP的唯一标识符，如"SOP-SYS-101"或"SOP-DB-001"

    Returns:
        JSON格式的SOP内容
    """
    try:
        logger.info(f"Getting SOP content for: {sop_id}")
        query = """
        SELECT sop_id, sop_title, sop_description
        FROM sop_prompt_templates
        WHERE sop_id = %s
        LIMIT 1
        """
        results = _execute_query(query, (sop_id,))
        logger.info(f"Query results: {len(results) if results else 0} rows found")

        if results:
            sop_data = results[0]

            return json.dumps({
                "status": "ok",
                "data": {
                    "sop_id": sop_data.get("sop_id", ""),
                    "sop_title": sop_data.get("sop_title", ""),
                    "sop_description": sop_data.get("sop_description", "")
                },
                "msg": f"SOP内容获取成功"
            }, ensure_ascii=False, indent=2)
        else:
            return json.dumps({
                "status": "error",
                "data": None,
                "msg": f"SOP '{sop_id}' 未找到"
            }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "data": None,
            "msg": f"获取SOP失败: {str(e)}"
        }, ensure_ascii=False, indent=2)

@mcp.tool()
async def list_sops() -> str:
    """列出所有可用的SOP

    Returns:
        JSON格式的SOP列表（仅包含ID和标题）
    """
    try:
        query = """
        SELECT sop_id, sop_title
        FROM sop_prompt_templates
        """
        results = _execute_query(query)
        logger.info(f"Query results: {len(results) if results else 0} rows found")
        return json.dumps({
            "status": "ok",
            "data": results,
            "total": len(results),
            "msg": "获取SOP列表成功"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return json.dumps({
            "status": "error",
            "data": None,
            "msg": str(e)
        }, ensure_ascii=False)

if __name__ == "__main__":
    # 获取端口
    port = config.get('port', 3005)
    
    logger.info(f"Starting {config.display_name} on port {port}")
    logger.info(f"SOP database config: host={config.get('host')}, database={config.get('database', 'omind')}")
    
    # 测试数据库连接
    try:
        conn = _create_mysql_connection()
        conn.close()
        logger.info("SOP数据库连接测试成功")
    except Exception as e:
        logger.error(f"SOP数据库连接测试失败: {e}")
    
    # 使用SSE传输方式启动服务器
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)