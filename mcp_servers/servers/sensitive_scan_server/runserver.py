#!/usr/bin/env python3
"""
敏感数据扫描 MCP 服务器（简化版）
"""

import os
import sys
import logging
from typing import List
from datetime import datetime
import uuid
from pathlib import Path

from fastmcp import FastMCP
import langextract as lx

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
    model_id=config.get("langextract_model", "Qwen/QwQ-32B"),
    api_key=config.get("langextract_api_key"),
    base_url=config.get("langextract_base_url", "https://api.siliconflow.cn/v1")
)

# 输出目录
OUTPUT_DIR = Path(config.get("visualization_output_dir", "/tmp/scan_visualizations"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


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


@mcp.tool()
def scan_documents(file_ids: List[str]) -> str:
    """
    扫描文档中的敏感信息
    
    Args:
        file_ids: 文件ID列表
    
    Returns:
        扫描结果文件路径
    """
    # 生成结果ID
    result_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    # 读取所有文件内容
    texts = []
    valid_file_ids = []
    
    for file_id in file_ids:
        try:
            content = read_file_content(file_id)
            texts.append(content)
            valid_file_ids.append(file_id)
        except Exception as e:
            logger.error(f"读取文件 {file_id} 失败: {e}")
    
    if not texts:
        return "错误：没有可扫描的文件"
    
    # 直接调用 langextract 扫描
    results = scanner.scan_files(texts)
    
    # 保存结果
    output_path = OUTPUT_DIR / f"{result_id}.jsonl"
    lx.io.save_annotated_documents(
        results,
        output_dir=str(OUTPUT_DIR),
        output_name=f"{result_id}.jsonl",
        show_progress=False
    )
    
    # 生成可视化
    html_path = OUTPUT_DIR / f"{result_id}.html"
    html_content = lx.visualize(str(output_path))
    html_path.write_text(html_content, encoding='utf-8')
    
    return f"扫描完成\n结果路径: {output_path}\n可视化: {html_path}"


if __name__ == "__main__":
    # 启动服务器
    port = config.get("port", 3008)
    logger.info(f"启动 {config.display_name} (端口: {port})")
    logger.info(f"文档存储路径: {config.get('document_storage_path')}")
    logger.info(f"输出目录: {config.get('visualization_output_dir')}")
    logger.info(f"模型: {config.get('langextract_model')}")
    
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)