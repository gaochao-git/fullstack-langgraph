#!/usr/bin/env python3
"""
测试 FastMCP 客户端调用 MCP Gateway 暴露的端点
"""

import asyncio
from fastmcp import Client

async def test_system_tools():
    """测试系统工具"""
    try:
        # 连接到 MCP Gateway 的 system 端点
        # 注意：不要在URL末尾加 /sse，让 FastMCP 自动处理
        async with Client("http://localhost:5235/system") as client:
            print("=== 连接成功 ===")
            
            # 获取可用工具列表
            tools = await client.list_tools()
            print(f"\n=== 可用工具 ({len(tools.tools)} 个) ===")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
            
            # 测试 system_info 工具
            print("\n=== 测试 system_info 工具 ===")
            result = await client.call_tool("system_info", {})
            print(f"结果: {result.content}")
            
            # 测试 execute_command 工具
            print("\n=== 测试 execute_command 工具 ===")
            result = await client.call_tool("execute_command", {
                "command": "whoami"
            })
            print(f"结果: {result.content}")
            
            # 测试 list_files 工具
            print("\n=== 测试 list_files 工具 ===")
            result = await client.call_tool("list_files", {
                "path": ".",
                "show_hidden": False
            })
            print(f"结果: {result.content}")
            
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

async def test_db_tools():
    """测试数据库工具"""
    try:
        # 连接到 MCP Gateway 的 db 端点
        async with Client("http://localhost:5235/db") as client:
            print("\n=== 连接 DB 工具成功 ===")
            
            # 获取可用工具列表
            tools = await client.list_tools()
            print(f"\n=== DB 可用工具 ({len(tools.tools)} 个) ===")
            for tool in tools.tools:
                print(f"- {tool.name}: {tool.description}")
                
    except Exception as e:
        print(f"DB 工具错误: {e}")

async def main():
    """主函数"""
    print("开始测试 FastMCP 客户端调用 MCP Gateway...")
    
    # 测试系统工具
    await test_system_tools()
    
    # 测试数据库工具  
    await test_db_tools()
    
    print("\n测试完成！")

if __name__ == "__main__":
    asyncio.run(main())