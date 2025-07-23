#!/usr/bin/env python3
"""简单的数据库连接测试"""
import asyncio
import sys
import os

# 添加项目根目录到path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.config import get_db
from src.database.models import MCPServer

async def test_db():
    """测试数据库连接"""
    try:
        # 测试数据库连接
        db = next(get_db())
        print("✅ 数据库连接成功")
        
        # 测试查询MCP服务器
        servers = db.query(MCPServer).all()
        print(f"📋 找到 {len(servers)} 个MCP服务器")
        
        for server in servers:
            print(f"  - {server.server_name} ({server.server_id})")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db())
    sys.exit(0 if success else 1)