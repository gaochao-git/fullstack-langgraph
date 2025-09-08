#!/usr/bin/env python3
"""
测试简化后的敏感数据扫描工具
"""

import asyncio
from servers.sensitive_scan_mcp_server import scan_document

async def test_simple_scan():
    print("=" * 50)
    print("测试敏感数据扫描工具")
    print("=" * 50)
    
    # 测试单个文件
    print("\n测试1: 扫描单个文件")
    print("-" * 50)
    result = await scan_document(["f99e779b-3266-4cc4-9df1-bc6972b511ec"])
    print(result)
    
    # 测试批量扫描
    print("\n\n测试2: 批量扫描多个文件")
    print("-" * 50)
    test_file_ids = [
        "f99e779b-3266-4cc4-9df1-bc6972b511ec",
        "dd6a7ade-8840-4f5d-8f8e-f6b16d1c86ed",
        "dbc7b277-16c9-4025-82e8-440b491c4b82"
    ]
    
    result = await scan_document(test_file_ids)
    print(result)

if __name__ == "__main__":
    asyncio.run(test_simple_scan())