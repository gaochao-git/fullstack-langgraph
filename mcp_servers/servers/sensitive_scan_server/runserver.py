#!/usr/bin/env python3
"""
敏感数据扫描 MCP 服务器（简化版）
"""

import os
import sys
import logging
from typing import List, Dict, Optional
from datetime import datetime
import uuid
from pathlib import Path
import threading
import json
import time

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

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入LangExtractScanner
from langextract_sensitive_scanner import LangExtractSensitiveScanner

# 初始化Scanner
scanner = LangExtractSensitiveScanner(
    model_id=config.get("langextract_model", "Qwen/Qwen3-30B-A3B-Instruct-2507"),
    api_key=config.get("langextract_api_key"),
    base_url=config.get("langextract_base_url", "https://api.siliconflow.cn/v1")
)

# 输出目录
OUTPUT_DIR = Path(config.get("visualization_output_dir", "/tmp/scan_visualizations"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 任务存储（生产环境应该使用Redis或数据库）
task_storage: Dict[str, Dict] = {}
task_lock = threading.Lock()


def read_file_content(file_id: str) -> str:
    """根据 file_id 读取文件内容"""
    # 从配置获取文档存储路径
    doc_storage_path = Path(config.get("document_storage_path", "/tmp/documents/uploads"))
    
    if not doc_storage_path.exists():
        raise FileNotFoundError(f"文档存储路径不存在: {doc_storage_path}")
    
    # 查找文件
    files = list(doc_storage_path.glob(f"{file_id}.*"))
    if not files:
        # 在子目录中查找
        files = list(doc_storage_path.glob(f"**/{file_id}.*"))
    
    if not files:
        raise FileNotFoundError(f"找不到文件: {file_id}")
    
    # 查找解析后的文件
    parsed_files = [f for f in files if f.name == f"{file_id}.parse.txt"]
    if not parsed_files:
        raise FileNotFoundError(f"找不到解析文件: {file_id}.parse.txt")
    
    # 读取解析后的文件内容
    return parsed_files[0].read_text(encoding='utf-8')


def process_scan_task(task_id: str, file_ids: List[str]):
    """后台处理扫描任务"""
    try:
        # 更新任务状态
        with task_lock:
            task_storage[task_id]["status"] = "processing"
            task_storage[task_id]["start_time"] = datetime.now().isoformat()
        
        # 读取所有文件内容
        file_contents = []
        total_files = len(file_ids)
        
        for i, file_id in enumerate(file_ids, 1):
            try:
                # 更新进度
                with task_lock:
                    task_storage[task_id]["progress"] = {
                        "phase": "reading",
                        "current": i,
                        "total": total_files,
                        "message": f"读取文件 {i}/{total_files}: {file_id[:8]}..."
                    }
                
                content = read_file_content(file_id)
                file_contents.append({
                    "file_id": file_id,
                    "content": content
                })
            except Exception as e:
                logger.error(f"读取文件 {file_id} 失败: {e}")
                with task_lock:
                    errors = task_storage[task_id].get("errors", [])
                    errors.append(f"读取文件 {file_id} 失败: {str(e)}")
                    task_storage[task_id]["errors"] = errors
        
        if not file_contents:
            raise Exception("没有可扫描的文件")
        
        # 扫描文档
        all_results = []
        processed_files = len(file_contents)
        
        for i, file_item in enumerate(file_contents, 1):
            try:
                # 更新进度
                with task_lock:
                    task_storage[task_id]["progress"] = {
                        "phase": "scanning",
                        "current": i,
                        "total": processed_files,
                        "message": f"扫描文件 {i}/{processed_files}: {file_item['file_id'][:8]}..."
                    }
                
                # 调用核心扫描模块
                scan_result = scanner.scan_single_document(
                    file_id=file_item["file_id"],
                    text=file_item["content"]
                )
                
                # 处理扫描结果
                if scan_result["success"]:
                    if scan_result["document"]:
                        all_results.append(scan_result["document"])
                        sensitive_count = scan_result["extractions"]
                        logger.info(f"    找到 {sensitive_count} 个敏感信息")
                        
                        # 更新统计
                        with task_lock:
                            task_storage[task_id]["statistics"]["sensitive_items"] += sensitive_count
                            task_storage[task_id]["statistics"]["processed_files"] += 1
                else:
                    raise Exception(scan_result.get("error", "扫描失败"))
                        
            except Exception as e:
                logger.error(f"扫描文件 {file_item['file_id']} 时出错: {e}")
                with task_lock:
                    errors = task_storage[task_id].get("errors", [])
                    errors.append(f"扫描文件 {file_item['file_id']} 失败: {str(e)}")
                    task_storage[task_id]["errors"] = errors
        
        if not all_results:
            raise Exception("扫描未产生任何结果")
        
        # 保存结果
        with task_lock:
            task_storage[task_id]["progress"] = {
                "phase": "saving",
                "current": 1,
                "total": 1,
                "message": "保存扫描结果..."
            }
        
        result_id = task_storage[task_id]["result_id"]
        output_path = OUTPUT_DIR / f"{result_id}.jsonl"
        
        # 使用 scanner 保存结果（需要在 scanner 中添加这个方法）
        scanner.save_results(
            all_results,
            output_path=str(output_path)
        )
        
        # 生成可视化
        try:
            html_path = OUTPUT_DIR / f"{result_id}.html"
            visualization_path = scanner.generate_visualization(
                str(output_path),
                str(html_path)
            )
        except Exception as e:
            logger.warning(f"生成可视化时出错: {e}")
            visualization_path = None
        
        # 更新任务为完成状态
        with task_lock:
            task_storage[task_id]["status"] = "completed"
            task_storage[task_id]["end_time"] = datetime.now().isoformat()
            task_storage[task_id]["result"] = {
                "output_path": str(output_path),
                "visualization_path": visualization_path,
                "total_files": len(file_ids),
                "processed_files": len(all_results),
                "total_sensitive_items": task_storage[task_id]["statistics"]["sensitive_items"]
            }
            task_storage[task_id]["progress"] = {
                "phase": "completed",
                "current": 1,
                "total": 1,
                "message": "扫描完成"
            }
            
    except Exception as e:
        logger.error(f"任务 {task_id} 处理失败: {e}")
        with task_lock:
            task_storage[task_id]["status"] = "failed"
            task_storage[task_id]["end_time"] = datetime.now().isoformat()
            task_storage[task_id]["error"] = str(e)
            task_storage[task_id]["progress"] = {
                "phase": "failed",
                "current": 0,
                "total": 0,
                "message": f"任务失败: {str(e)}"
            }


@mcp.tool()
def scan_documents(file_ids: List[str]) -> str:
    """
    扫描文档中的敏感信息（异步任务）
    
    Args:
        file_ids: 文件ID列表
    
    Returns:
        任务ID和状态信息
    """
    # 生成任务ID和结果ID
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    result_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # 创建任务记录
    with task_lock:
        task_storage[task_id] = {
            "task_id": task_id,
            "result_id": result_id,
            "status": "pending",
            "file_ids": file_ids,
            "total_files": len(file_ids),
            "created_time": datetime.now().isoformat(),
            "progress": {
                "phase": "pending",
                "current": 0,
                "total": len(file_ids),
                "message": "任务已创建，等待处理..."
            },
            "statistics": {
                "sensitive_items": 0,
                "processed_files": 0
            },
            "errors": []
        }
    
    # 启动后台线程处理任务
    thread = threading.Thread(
        target=process_scan_task,
        args=(task_id, file_ids),
        daemon=True
    )
    thread.start()
    
    logger.info(f"创建扫描任务: {task_id}，包含 {len(file_ids)} 个文件")
    
    # 立即返回任务信息
    return json.dumps({
        "success": True,
        "task_id": task_id,
        "message": f"扫描任务已创建，任务ID: {task_id}",
        "total_files": len(file_ids),
        "check_progress_hint": f"使用 check_scan_progress('{task_id}') 查看进度"
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
    with task_lock:
        if task_id not in task_storage:
            return json.dumps({
                "success": False,
                "error": f"任务不存在: {task_id}"
            }, ensure_ascii=False, indent=2)
        
        task = task_storage[task_id].copy()
    
    # 构建响应
    response = {
        "success": True,
        "task_id": task_id,
        "status": task["status"],
        "created_time": task["created_time"],
        "total_files": task["total_files"],
        "progress": task["progress"],
        "statistics": task["statistics"]
    }
    
    # 添加时间信息
    if "start_time" in task:
        response["start_time"] = task["start_time"]
    if "end_time" in task:
        response["end_time"] = task["end_time"]
    
    # 添加错误信息
    if task.get("errors"):
        response["errors"] = task["errors"]
    if task.get("error"):
        response["error"] = task["error"]
    
    # 如果任务完成，添加结果信息
    if task["status"] == "completed" and "result" in task:
        response["result"] = task["result"]
    
    return json.dumps(response, ensure_ascii=False, indent=2)


@mcp.tool()
def list_scan_tasks(limit: Optional[int] = 10) -> str:
    """
    列出扫描任务列表
    
    Args:
        limit: 返回的任务数量限制，默认10
    
    Returns:
        任务列表
    """
    with task_lock:
        # 获取所有任务并按创建时间倒序排序
        tasks = list(task_storage.values())
        tasks.sort(key=lambda x: x["created_time"], reverse=True)
        
        # 限制返回数量
        if limit:
            tasks = tasks[:limit]
        
        # 简化任务信息
        task_list = []
        for task in tasks:
            task_info = {
                "task_id": task["task_id"],
                "status": task["status"],
                "created_time": task["created_time"],
                "total_files": task["total_files"],
                "progress": task["progress"]["message"]
            }
            
            # 添加统计信息
            if task["status"] in ["processing", "completed"]:
                task_info["sensitive_items"] = task["statistics"]["sensitive_items"]
                task_info["processed_files"] = task["statistics"]["processed_files"]
            
            task_list.append(task_info)
    
    return json.dumps({
        "success": True,
        "total_tasks": len(task_storage),
        "returned_tasks": len(task_list),
        "tasks": task_list
    }, ensure_ascii=False, indent=2)


@mcp.tool()
def get_scan_result(task_id: str) -> str:
    """
    获取扫描任务的结果文件路径
    
    Args:
        task_id: 任务ID
    
    Returns:
        扫描结果信息
    """
    with task_lock:
        if task_id not in task_storage:
            return json.dumps({
                "success": False,
                "error": f"任务不存在: {task_id}"
            }, ensure_ascii=False, indent=2)
        
        task = task_storage[task_id]
        
        if task["status"] != "completed":
            return json.dumps({
                "success": False,
                "error": f"任务未完成，当前状态: {task['status']}",
                "progress": task["progress"]
            }, ensure_ascii=False, indent=2)
        
        if "result" not in task:
            return json.dumps({
                "success": False,
                "error": "任务已完成但无结果数据"
            }, ensure_ascii=False, indent=2)
        
        return json.dumps({
            "success": True,
            "task_id": task_id,
            "result": task["result"],
            "statistics": task["statistics"],
            "completed_time": task.get("end_time")
        }, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    # 启动服务器
    port = config.get("port", 3008)
    logger.info(f"启动 {config.display_name} (端口: {port})")
    logger.info(f"文档存储路径: {config.get('document_storage_path')}")
    logger.info(f"输出目录: {config.get('visualization_output_dir')}")
    logger.info(f"模型: {config.get('langextract_model')}")
    logger.info("支持的工具：")
    logger.info("  - scan_documents: 创建扫描任务")
    logger.info("  - check_scan_progress: 查看任务进度")
    logger.info("  - list_scan_tasks: 列出任务列表")
    logger.info("  - get_scan_result: 获取任务结果")
    
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)