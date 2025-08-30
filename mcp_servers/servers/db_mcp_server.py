#!/usr/bin/env python3
"""
Database Tools MCP Server
基于Web Console API的数据库工具MCP服务器
"""

import json
import logging
from typing import Dict, Any, Optional
import os
import requests
from fastmcp import FastMCP
from base_config import MCPServerConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
mcp = FastMCP("Database Tools Server")

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

if __name__ == "__main__":
    # 获取端口（从环境变量或配置）
    port = int(os.environ.get('MCP_SERVER_PORT', config.port))
    
    logger.info(f"Starting {config.display_name} on port {port}")
    logger.info(f"API Base URL: {API_BASE_URL}")
    logger.info(f"Available tools: get_all_table_names_and_comments, get_table_structure")
    
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