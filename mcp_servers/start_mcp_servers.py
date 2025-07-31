#!/usr/bin/env python3
"""
OpenAPI MCP服务器启动脚本
支持从数据库动态加载配置并生成MCP服务器
"""

import asyncio
import argparse
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'servers'))

from convert_mcp_server import MultiRouteMCPServer


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='OpenAPI MCP服务器')
    parser.add_argument('--host', default='0.0.0.0', help='服务器主机地址')
    parser.add_argument('--port', type=int, default=8100, help='服务器端口')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细日志')
    return parser.parse_args()


async def main():
    """主函数"""
    args = parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🚀 启动OpenAPI MCP服务器集群...")
    print(f"📡 服务地址: http://{args.host}:{args.port}")
    print("🔗 访问根路径查看所有可用的MCP端点")
    print("⚡ 每个OpenAPI配置对应一个独立的MCP端点")
    print()
    
    server = MultiRouteMCPServer()
    
    try:
        await server.start_server(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())