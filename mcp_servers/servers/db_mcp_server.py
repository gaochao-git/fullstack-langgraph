#!/usr/bin/env python3
"""
Database Tools MCP Server
基于现有MySQL工具实现的MCP服务器
"""

import json
import logging
from typing import Dict, Any, Optional
import os
import pymysql
from fastmcp import FastMCP
from base_config import MCPServerConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("Database Tools Server")

# 加载配置
config = MCPServerConfig('db_query')

def _create_mysql_connection():
    """创建新的MySQL连接，每次调用都重新连接"""
    try:
        connection_config = {
            'host': config.get('host'),
            'port': config.get('port'),
            'user': config.get('username'),
            'password': config.get('password'),
            'charset': 'utf8mb4',
            'autocommit': True,
            'database': config.get('database', 'information_schema')
        }
        
        connection = pymysql.connect(**connection_config)
        logger.info(f"MySQL连接成功，主机: {config.get('host')}, 用户: {config.get('username')}")
        return connection
        
    except Exception as e:
        logger.error(f"MySQL连接失败: {e}")
        raise Exception(f"无法建立MySQL连接: {str(e)}")

@mcp.tool()
async def execute_mysql_query(
    connection_name: str = "default",
    query: str = "",
    limit: int = 100
) -> str:
    """执行诊断SQL查询。用于执行自定义的数据库诊断查询。
    
    Args:
        connection_name: MySQL连接名称
        query: SQL查询语句
        limit: 结果限制数量
    
    Returns:
        包含查询结果的JSON字符串
    """
    # 安全检查：只允许SELECT查询和特定的SHOW语句
    query_upper = query.strip().upper()
    allowed_commands = ['SELECT', 'SHOW', 'EXPLAIN', 'DESCRIBE', 'DESC', 'KILL']
    
    if not any(query_upper.startswith(cmd) for cmd in allowed_commands):
        return json.dumps({
            "error": "Only SELECT, SHOW, EXPLAIN, and DESCRIBE statements are allowed for diagnostic queries"
        })
    
    connection = None
    try:
        connection = _create_mysql_connection()
        cursor = connection.cursor(pymysql.cursors.DictCursor)
        
        # 添加LIMIT子句以防止返回过多数据
        if query_upper.startswith('SELECT') and 'LIMIT' not in query_upper:
            query += f" LIMIT {limit}"
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        # 获取列信息
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        cursor.close()
        
        return json.dumps({
            "query": query,
            "columns": columns,
            "row_count": len(results),
            "results": results
        }, indent=2, default=str)  # default=str 处理datetime等类型
        
    except Exception as e:
        logger.error(f"Error executing diagnostic query: {e}")
        return json.dumps({"error": f"Failed to execute query: {str(e)}"})
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    # 获取端口（从环境变量或配置）
    port = int(os.environ.get('MCP_SERVER_PORT', config.port))
    
    logger.info(f"Starting {config.display_name} on port {port}")
    logger.info(f"Database config: host={config.get('host')}, user={config.get('username')}")
    
    # 测试数据库连接
    try:
        conn = _create_mysql_connection()
        conn.close()
        logger.info("数据库连接测试成功")
    except Exception as e:
        logger.error(f"数据库连接测试失败: {e}")
    
    # 使用SSE传输方式启动服务器
    mcp.run(transport="streamable-http", port=port)