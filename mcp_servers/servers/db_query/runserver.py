#!/usr/bin/env python3
"""
Database Diagnostic Tools MCP Server
专门用于数据库故障诊断的只读查询服务器
"""

import json
import logging
from typing import Dict, Any, Optional, List
import os
import re
import requests
from fastmcp import FastMCP
from ..common.base_config import MCPServerConfig
from .diagnostic_queries import (
    MYSQL_DIAGNOSTIC_QUERIES,
    POSTGRESQL_DIAGNOSTIC_QUERIES,
    ALLOWED_QUERY_PATTERNS,
    DANGEROUS_KEYWORDS
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("Database Diagnostic Tools Server")

# 加载配置
config = MCPServerConfig('db_query')

# API配置
API_BASE_URL = config.get('api_base_url', 'http://172.20.10.2:8111')
API_TOKEN = config.get('api_token', 'app-tbCzKza1riIJ6M3Grn4nWSQa')

@mcp.tool()
async def get_all_table_names_and_comments(
    instance_name: str,
    schema_name: str
) -> str:
    """获取数据库中所有表的名称和注释信息。
    
    Args:
        instance_name: 数据库实例名称（格式: host_port，如: 82.156.146.51_3306）
        schema_name: 数据库schema名称（如: cloud4db）
    
    Returns:
        包含表名和注释的JSON字符串
    """
    url = f"{API_BASE_URL}/api/web_console/v1/get_all_table_names_and_comments/"
    
    payload = {
        "instance_name": instance_name,
        "schema_name": schema_name
    }
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return json.dumps(data, indent=2, ensure_ascii=False)
        
    except requests.exceptions.Timeout:
        logger.error(f"请求超时: {url}")
        return json.dumps({
            "error": "请求超时",
            "message": "获取表信息超时，请稍后重试"
        }, ensure_ascii=False)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return json.dumps({
            "error": "请求失败",
            "message": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"未预期的错误: {e}")
        return json.dumps({
            "error": "内部错误",
            "message": str(e)
        }, ensure_ascii=False)

@mcp.tool()
async def get_table_structure(
    instance_name: str,
    schema_name: str,
    table_names: str
) -> str:
    """获取指定表的结构信息。
    
    Args:
        instance_name: 数据库实例名称（格式: host_port，如: 82.156.146.51_3306）
        schema_name: 数据库schema名称（如: cloud4db）
        table_names: 表名，逗号分隔的字符串，如: "table1,table2,table3"
    
    Returns:
        包含表结构信息的JSON字符串
    """
    # 假设有一个获取表结构的API端点
    url = f"{API_BASE_URL}/api/web_console/v1/get_table_structures/"
    
    payload = {
        "instance_name": instance_name,
        "schema_name": schema_name,
        "table_names": table_names
    }
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return json.dumps(data, indent=2, ensure_ascii=False)
        
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return json.dumps({
            "error": "请求失败",
            "message": str(e),
            "status_code": getattr(e.response, 'status_code', None) if hasattr(e, 'response') else None
        }, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"未预期的错误: {e}")
        return json.dumps({
            "error": "内部错误",
            "message": str(e)
        }, ensure_ascii=False)

@mcp.tool()
async def execute_diagnostic_query(
    instance_name: str,
    schema_name: str,
    query_type: str,
    db_type: str = "mysql"
) -> str:
    """执行预定义的诊断查询，用于故障排查。
    
    Args:
        instance_name: 数据库实例名称（格式: host_port）
        schema_name: 数据库schema名称
        query_type: 诊断查询类型，可选值：
            - connection_status: 连接状态检查
            - active_processes: 活跃进程列表
            - slow_queries: 慢查询检查
            - table_locks: 表锁情况
            - innodb_status_summary: InnoDB状态摘要
            - recent_errors: 最近的错误
            - connection_errors: 连接错误统计
            等
        db_type: 数据库类型，mysql 或 postgresql，默认mysql
    
    Returns:
        查询结果的JSON字符串
    """
    # 选择对应的查询模板
    if db_type.lower() == "mysql":
        queries = MYSQL_DIAGNOSTIC_QUERIES
    elif db_type.lower() == "postgresql":
        queries = POSTGRESQL_DIAGNOSTIC_QUERIES
    else:
        return json.dumps({
            "error": "不支持的数据库类型",
            "message": f"数据库类型 {db_type} 不支持，仅支持 mysql 和 postgresql"
        }, ensure_ascii=False)
    
    # 检查查询类型是否存在
    if query_type not in queries:
        available_queries = list(queries.keys())
        return json.dumps({
            "error": "无效的查询类型",
            "message": f"查询类型 '{query_type}' 不存在",
            "available_queries": available_queries,
            "hint": "请从 available_queries 中选择一个有效的查询类型"
        }, ensure_ascii=False)
    
    # 获取查询信息
    query_info = queries[query_type]
    sql = query_info["sql"]
    
    # 替换参数（如果有）
    if "?" in sql:
        sql = sql.replace("?", f"'{schema_name}'")
    
    # 调用API执行查询
    url = f"{API_BASE_URL}/api/web_console/v1/execute_readonly_query/"
    
    payload = {
        "instance_name": instance_name,
        "schema_name": schema_name,
        "sql": sql,
        "query_type": "diagnostic",
        "query_name": query_info["name"]
    }
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # 添加查询描述信息
        result = {
            "query_name": query_info["name"],
            "description": query_info["description"],
            "data": data.get("data", []),
            "row_count": len(data.get("data", [])),
            "execution_time": data.get("execution_time", "N/A")
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"执行诊断查询失败: {e}")
        return json.dumps({
            "error": "查询执行失败",
            "message": str(e),
            "query_type": query_type,
            "hint": "请检查数据库连接和权限设置"
        }, ensure_ascii=False)

@mcp.tool()
async def list_diagnostic_queries(
    db_type: str = "mysql"
) -> str:
    """列出所有可用的诊断查询类型。
    
    Args:
        db_type: 数据库类型，mysql 或 postgresql，默认mysql
    
    Returns:
        可用诊断查询的列表
    """
    if db_type.lower() == "mysql":
        queries = MYSQL_DIAGNOSTIC_QUERIES
    elif db_type.lower() == "postgresql":
        queries = POSTGRESQL_DIAGNOSTIC_QUERIES
    else:
        return json.dumps({
            "error": "不支持的数据库类型",
            "supported_types": ["mysql", "postgresql"]
        }, ensure_ascii=False)
    
    query_list = []
    for key, info in queries.items():
        query_list.append({
            "query_type": key,
            "name": info["name"],
            "description": info["description"]
        })
    
    return json.dumps({
        "db_type": db_type,
        "total_queries": len(query_list),
        "queries": query_list
    }, indent=2, ensure_ascii=False)

@mcp.tool()
async def check_database_health(
    instance_name: str,
    schema_name: str,
    db_type: str = "mysql"
) -> str:
    """执行数据库健康检查，运行一组关键诊断查询。
    
    Args:
        instance_name: 数据库实例名称
        schema_name: 数据库schema名称  
        db_type: 数据库类型，mysql 或 postgresql
    
    Returns:
        健康检查报告
    """
    health_checks = []
    
    # 定义关键健康检查项
    if db_type.lower() == "mysql":
        check_queries = [
            "connection_status",
            "active_processes",
            "slow_queries",
            "connection_errors"
        ]
    else:
        check_queries = [
            "connection_status",
            "active_queries",
            "blocking_queries"
        ]
    
    # 执行每个健康检查
    for query_type in check_queries:
        try:
            result = await execute_diagnostic_query(
                instance_name, 
                schema_name, 
                query_type, 
                db_type
            )
            health_checks.append({
                "check": query_type,
                "status": "success",
                "result": json.loads(result)
            })
        except Exception as e:
            health_checks.append({
                "check": query_type,
                "status": "failed",
                "error": str(e)
            })
    
    # 生成健康报告摘要
    summary = {
        "instance": instance_name,
        "schema": schema_name,
        "db_type": db_type,
        "total_checks": len(health_checks),
        "successful_checks": sum(1 for c in health_checks if c["status"] == "success"),
        "failed_checks": sum(1 for c in health_checks if c["status"] == "failed"),
        "health_status": "healthy" if all(c["status"] == "success" for c in health_checks) else "unhealthy",
        "checks": health_checks
    }
    
    return json.dumps(summary, indent=2, ensure_ascii=False)

def is_safe_query(sql: str) -> bool:
    """检查SQL是否为安全的只读查询。
    
    Args:
        sql: 要检查的SQL语句
        
    Returns:
        bool: 如果查询安全返回True，否则返回False
    """
    # 转换为大写以便检查
    sql_upper = sql.upper().strip()
    
    # 检查是否包含危险关键词
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            logger.warning(f"检测到危险关键词: {keyword}")
            return False
    
    # 检查是否匹配允许的查询模式
    for pattern in ALLOWED_QUERY_PATTERNS:
        if re.match(pattern, sql, re.IGNORECASE | re.DOTALL):
            return True
    
    logger.warning(f"查询不匹配允许的模式: {sql[:50]}...")
    return False

@mcp.tool()
async def execute_readonly_sql(
    instance_name: str,
    schema_name: str,
    sql: str,
    limit: int = 100
) -> str:
    """执行自定义的只读SQL查询（仅用于故障诊断）。
    
    Args:
        instance_name: 数据库实例名称
        schema_name: 数据库schema名称
        sql: 要执行的SQL语句（仅支持SELECT/SHOW/DESCRIBE等只读操作）
        limit: 结果行数限制，默认100
    
    Returns:
        查询结果
    """
    # 安全检查
    if not is_safe_query(sql):
        return json.dumps({
            "error": "查询被拒绝",
            "message": "仅允许执行只读查询（SELECT, SHOW, DESCRIBE, EXPLAIN）",
            "hint": "如需执行写操作，请通过正规流程申请"
        }, ensure_ascii=False)
    
    # 添加LIMIT限制（如果是SELECT且没有LIMIT）
    sql_upper = sql.upper()
    if "SELECT" in sql_upper and "LIMIT" not in sql_upper:
        sql = f"{sql.rstrip(';')} LIMIT {limit}"
    
    # 调用API执行查询
    url = f"{API_BASE_URL}/api/web_console/v1/execute_readonly_query/"
    
    payload = {
        "instance_name": instance_name,
        "schema_name": schema_name,
        "sql": sql,
        "query_type": "custom_diagnostic",
        "limit": limit
    }
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        result = {
            "success": True,
            "data": data.get("data", []),
            "columns": data.get("columns", []),
            "row_count": len(data.get("data", [])),
            "limited_to": limit,
            "execution_time": data.get("execution_time", "N/A"),
            "warning": "结果可能被限制在前{}行".format(limit) if len(data.get("data", [])) >= limit else None
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"执行SQL查询失败: {e}")
        return json.dumps({
            "error": "查询执行失败",
            "message": str(e),
            "sql": sql[:200] + "..." if len(sql) > 200 else sql
        }, ensure_ascii=False)

if __name__ == "__main__":
    # 获取端口
    port = config.get('port', 3001)
    
    logger.info(f"Starting {config.display_name} on port {port}")
    logger.info(f"API Base URL: {API_BASE_URL}")
    logger.info("=" * 60)
    logger.info("Available diagnostic tools:")
    logger.info("  - list_diagnostic_queries: 列出所有可用的诊断查询")
    logger.info("  - execute_diagnostic_query: 执行预定义的安全诊断查询")
    logger.info("  - check_database_health: 执行数据库健康检查")
    logger.info("  - execute_readonly_sql: 执行自定义只读SQL（有安全检查）")
    logger.info("  - get_all_table_names_and_comments: 获取表信息")
    logger.info("  - get_table_structure: 获取表结构")
    logger.info("=" * 60)
    logger.info("安全提示：本服务器仅支持只读查询，所有写操作将被拒绝")
    
    # 测试API连接
    try:
        test_url = f"{API_BASE_URL}/api/health"  # 假设有健康检查端点
        response = requests.get(test_url, timeout=5)
        logger.info(f"API连接测试成功: {response.status_code}")
    except Exception as e:
        logger.warning(f"API连接测试失败: {e}")
        logger.warning("继续启动服务器，但请确保API服务可用")
    
    # 使用SSE传输方式启动服务器
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)