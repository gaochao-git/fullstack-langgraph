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
import aiohttp
import asyncio
from concurrent.futures import ThreadPoolExecutor

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
API_TIMEOUT = config.get("api_timeout", 300)  # 5分钟超时

# 创建异步HTTP客户端会话
async_session = None


def get_async_session():
    """获取异步HTTP会话"""
    global async_session
    if async_session is None:
        async_session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
        )
    return async_session


async def call_backend_api(method: str, endpoint: str, **kwargs) -> Dict:
    """
    调用后端API
    
    Args:
        method: HTTP方法 (GET, POST等)
        endpoint: API端点路径
        **kwargs: 其他参数(json, params等)
        
    Returns:
        API响应数据
    """
    session = get_async_session()
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        async with session.request(method, url, **kwargs) as response:
            data = await response.json()
            
            if response.status >= 400:
                raise Exception(f"API错误 ({response.status}): {data.get('detail', 'Unknown error')}")
            
            # 处理统一响应格式
            if isinstance(data, dict) and "status" in data:
                if data["status"] == "error":
                    raise Exception(f"业务错误: {data.get('msg', 'Unknown error')}")
                return data.get("data", data)
            
            return data
            
    except aiohttp.ClientError as e:
        logger.error(f"调用API失败 {method} {url}: {e}")
        raise Exception(f"网络错误: {str(e)}")
    except Exception as e:
        logger.error(f"处理API响应失败: {e}")
        raise


def sync_call_api(method: str, endpoint: str, **kwargs) -> Dict:
    """同步调用API（用于非异步工具函数）"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(call_backend_api(method, endpoint, **kwargs))
    finally:
        loop.close()


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
        result = sync_call_api(
            "POST", 
            "/api/v1/scan/tasks",
            json={"file_ids": file_ids}
        )
        
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
        result = sync_call_api(
            "GET", 
            f"/api/v1/scan/tasks/{task_id}/progress"
        )
        
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
def list_scan_tasks(limit: Optional[int] = 10) -> str:
    """
    列出扫描任务列表
    
    Args:
        limit: 返回的任务数量限制，默认10
    
    Returns:
        任务列表
    """
    try:
        # 调用后端API获取任务列表
        result = sync_call_api(
            "GET", 
            "/api/v1/scan/tasks",
            params={"page": 1, "size": limit}
        )
        
        # 处理分页响应
        tasks = result.get("items", [])
        total_tasks = result.get("total", 0)
        
        # 简化任务信息
        task_list = []
        for task in tasks:
            progress = task.get("progress", {})
            task_info = {
                "task_id": task["task_id"],
                "status": task["status"],
                "created_time": task.get("create_time"),
                "total_files": task["total_files"],
                "progress": progress.get("message", "未知进度")
            }
            
            # 添加统计信息
            if task["status"] in ["processing", "completed"]:
                task_info["processed_files"] = task.get("processed_files", 0)
                task_info["failed_files"] = task.get("failed_files", 0)
            
            task_list.append(task_info)
        
        return json.dumps({
            "success": True,
            "total_tasks": total_tasks,
            "returned_tasks": len(task_list),
            "tasks": task_list
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_scan_result(task_id: str) -> str:
    """
    获取扫描任务的结果（包含所有文件的扫描结果）
    
    Args:
        task_id: 任务ID
    
    Returns:
        扫描结果信息
    """
    try:
        # 调用后端API获取任务结果
        result = sync_call_api(
            "GET", 
            f"/api/v1/scan/tasks/{task_id}/result"
        )
        
        return json.dumps({
            "success": True,
            "task_id": task_id,
            "status": result.get("status"),
            "summary": result.get("summary"),
            "files": result.get("files", []),
            "completed_time": result.get("completed_time")
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"获取任务结果失败: {e}")
        return json.dumps({
            "success": False,
            "error": str(e)
        }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_file_scan_details(task_id: str, file_id: str) -> str:
    """
    获取特定文件的扫描详情
    
    Args:
        task_id: 任务ID
        file_id: 文件ID
    
    Returns:
        文件扫描详情
    """
    try:
        # 先获取完整的任务结果
        result = sync_call_api(
            "GET", 
            f"/api/v1/scan/tasks/{task_id}/result"
        )
        
        # 查找特定文件
        files = result.get("files", [])
        file_info = None
        for f in files:
            if f.get("file_id") == file_id:
                file_info = f
                break
        
        if not file_info:
            return json.dumps({
                "success": False,
                "error": f"文件不存在于此任务中: {file_id}"
            }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "success": True,
            "task_id": task_id,
            "file_id": file_id,
            "status": file_info.get("status"),
            "jsonl_path": file_info.get("jsonl_path"),
            "html_path": file_info.get("html_path"),
            "error": file_info.get("error"),
            "start_time": file_info.get("start_time"),
            "end_time": file_info.get("end_time")
        }, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"获取文件扫描详情失败: {e}")
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


async def cleanup_session():
    """清理HTTP会话"""
    global async_session
    if async_session:
        await async_session.close()
        async_session = None


if __name__ == "__main__":
    # 启动服务器
    port = config.get("port", 3008)
    logger.info(f"启动 {config.display_name} (端口: {port})")
    logger.info(f"后端API地址: {API_BASE_URL}")
    logger.info(f"API超时时间: {API_TIMEOUT}秒")
    logger.info("支持的工具：")
    logger.info("  - scan_documents: 创建扫描任务")
    logger.info("  - check_scan_progress: 查看任务进度")
    logger.info("  - list_scan_tasks: 列出任务列表")
    logger.info("  - get_scan_result: 获取任务结果")
    logger.info("  - get_file_scan_details: 获取特定文件的扫描详情")
    logger.info("  - sleep_interval: 暂停指定秒数（0-300秒）")
    
    try:
        mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
    finally:
        # 清理资源
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(cleanup_session())
        loop.close()