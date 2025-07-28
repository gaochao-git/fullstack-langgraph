"""
MySQL工具 - 使用LangChain工具框架
"""

import pymysql
import json
from typing import Dict, Any, List, Optional
import logging
from langchain.tools import tool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

def _create_mysql_connection():
    """创建新的MySQL连接，每次调用都重新连接"""
    # 默认连接参数，按优先级排序
    default_configs = [
        {"host": "82.156.146.51", "username": "gaochao", "password": "fffjjj"},
        {"host": "82.156.146.51", "username": "root", "password": "123456"},
        {"host": "82.156.146.51", "username": "mysql", "password": "mysql"}
    ]
    
    for config in default_configs:
        try:
            connection_config = {
                'host': config["host"],
                'port': 3306,
                'user': config["username"],
                'password': config["password"],
                'charset': 'utf8mb4',
                'autocommit': True,
                'database': 'information_schema'
            }
            
            connection = pymysql.connect(**connection_config)
            logger.info(f"MySQL连接成功，用户: {config['username']}")
            return connection
            
        except Exception as e:
            logger.debug(f"尝试用户 {config['username']} 失败: {e}")
            continue
    
    raise Exception("无法建立MySQL连接，请检查数据库服务状态和凭据")

class CustomQueryInput(BaseModel):
    """自定义查询输入参数"""
    connection_name: str = Field(default="default", description="连接名称")
    query: str = Field(description="SQL查询语句")
    limit: int = Field(default=100, description="结果限制数量")

@tool("execute_mysql_query", args_schema=CustomQueryInput)
def execute_mysql_query(
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
    allowed_commands = ['SELECT', 'SHOW', 'EXPLAIN', 'DESCRIBE', 'DESC']
    
    if not any(query_upper.startswith(cmd) for cmd in allowed_commands):
        return json.dumps({
            "error": "Only SELECT, SHOW, EXPLAIN, and DESCRIBE statements are allowed for diagnostic queries"
        })
    
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

# 导出所有工具
mysql_tools = [
    execute_mysql_query
]
