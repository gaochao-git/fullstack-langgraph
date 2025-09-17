#!/usr/bin/env python3
"""
敏感数据扫描 MCP 服务器（调用后端API版）
"""

import os
import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from pathlib import Path
import json
import time
import requests

from fastmcp import FastMCP

# 配置logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加父目录到 Python 路径以导入公共模块
sys.path.insert(0, str(Path(__file__).parent.parent))

# 导入配置
from common.base_config import MCPServerConfig

# 加载配置
config = MCPServerConfig('sensitive_scan_server')

# 初始化MCP服务
mcp = FastMCP(config.display_name)

# 后端API配置
API_BASE_URL = config.get("api_base_url", "http://localhost:8000")
API_KEY = config.get("api_key", "")  # API密钥
API_TIMEOUT = config.get("api_timeout", 300)  # 5分钟超时


@mcp.tool()
def scan_documents(file_ids: List[str]) -> str:
    """
    扫描文档中的敏感信息（异步任务）
    
    Args:
        file_ids: 文件ID列表
    
    Returns:
        任务ID和状态信息
    """
    try:
        # 调用后端API创建扫描任务
        import requests
        headers = {}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/scan/tasks",
            json={"file_ids": file_ids},
            headers=headers,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "error":
            raise Exception(f"业务错误: {data.get('msg', 'Unknown error')}")
        
        result = data.get("data", data)
        task_id = result.get("task_id")
        
        logger.info(f"创建扫描任务: {task_id}，包含 {len(file_ids)} 个文件")
        
        return json.dumps({
            "success": True,
            "task_id": task_id,
            "message": f"扫描任务已创建，任务ID: {task_id}",
            "total_files": len(file_ids),
            "check_progress_hint": f"使用 check_scan_progress('{task_id}') 查看进度"
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"创建扫描任务失败: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def check_scan_progress(task_id: str) -> str:
    """
    查看扫描任务进度
    
    Args:
        task_id: 任务ID
    
    Returns:
        任务进度信息
    """
    try:
        # 调用后端API获取任务进度
        import requests
        headers = {}
        if API_KEY:
            headers["Authorization"] = f"Bearer {API_KEY}"
        
        response = requests.get(
            f"{API_BASE_URL}/api/v1/scan/tasks/{task_id}/progress",
            headers=headers,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "error":
            raise Exception(f"业务错误: {data.get('msg', 'Unknown error')}")
        
        result = data.get("data", data)
        
        # 构建响应
        response = {
            "success": True,
            "task_id": task_id,
            "status": result.get("status"),
            "total_files": result.get("total_files"),
            "processed_files": result.get("processed_files"),
            "failed_files": result.get("failed_files"),
            "progress": result.get("progress", {}),
            "statistics": result.get("statistics", {}),
            "create_time": result.get("create_time")
        }
        
        # 添加时间信息
        if result.get("start_time"):
            response["start_time"] = result["start_time"]
        if result.get("end_time"):
            response["end_time"] = result["end_time"]
        
        # 添加错误信息
        if result.get("errors"):
            response["errors"] = result["errors"]
        
        # 添加文件状态摘要
        if result.get("file_status_summary"):
            response["file_status_summary"] = result["file_status_summary"]
        
        return json.dumps(response, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"获取任务进度失败: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def sleep_interval(seconds: int) -> str:
    """
    暂停指定的时间，用于控制处理节奏或等待外部系统响应
    
    Args:
        seconds: 要暂停的秒数（0-300秒）
    
    Returns:
        暂停完成信息
    """
    # 限制最大暂停时间为5分钟
    if seconds < 0:
        seconds = 0
    elif seconds > 300:
        seconds = 300
    
    # 执行暂停
    time.sleep(seconds)
    
    return json.dumps({
        "success": True,
        "message": f"已暂停{seconds}秒"
    }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 启动服务器
    port = config.get("port", 3008)
    logger.info(f"启动 {config.display_name} (端口: {port})")
    logger.info(f"后端API地址: {API_BASE_URL}")
    logger.info(f"API超时时间: {API_TIMEOUT}秒")
    logger.info("支持的工具：")
    logger.info("  - scan_documents: 创建扫描任务")
    logger.info("  - check_scan_progress: 查看任务进度")
    logger.info("  - sleep_interval: 暂停指定秒数（0-300秒）")
    
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)