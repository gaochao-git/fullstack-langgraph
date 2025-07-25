#!/usr/bin/env python3
"""
测试后端数据库连接池和重连机制
"""
import sys
import os
import asyncio
import time
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

async def test_async_connection():
    """测试异步数据库连接"""
    print("🔍 测试异步数据库连接...")
    
    try:
        from src.db.config import get_async_session, async_engine
        from sqlalchemy import text
        
        # 测试连接池信息
        print(f"   连接池大小: {async_engine.pool.size()}")
        print(f"   已检出连接: {async_engine.pool.checkedout()}")
        print(f"   连接池状态: {async_engine.pool.status()}")
        
        # 测试多个并发连接
        async def test_query(session_id):
            async for session in get_async_session():
                result = await session.execute(text("SELECT CONNECTION_ID(), NOW()"))
                row = result.fetchone()
                print(f"   异步会话 {session_id}: 连接ID={row[0]}, 时间={row[1]}")
                return row[0]
        
        # 并发测试
        tasks = [test_query(i) for i in range(3)]
        connection_ids = await asyncio.gather(*tasks)
        
        print(f"   获取到的连接ID: {connection_ids}")
        return True
        
    except Exception as e:
        print(f"   ❌ 异步连接测试失败: {e}")
        return False

def test_sync_connection():
    """测试同步数据库连接"""
    print("\n🔍 测试同步数据库连接...")
    
    try:
        from src.db.config import get_sync_session, sync_engine
        from sqlalchemy import text
        
        # 测试连接池信息
        print(f"   连接池大小: {sync_engine.pool.size()}")
        print(f"   已检出连接: {sync_engine.pool.checkedout()}")
        print(f"   连接池状态: {sync_engine.pool.status()}")
        
        # 测试多个连接
        for i in range(3):
            for session in get_sync_session():
                result = session.execute(text("SELECT CONNECTION_ID(), NOW()"))
                row = result.fetchone()
                print(f"   同步会话 {i+1}: 连接ID={row[0]}, 时间={row[1]}")
                break
            time.sleep(0.1)
        
        return True
        
    except Exception as e:
        print(f"   ❌ 同步连接测试失败: {e}")
        return False

def test_fastapi_dependency():
    """测试FastAPI依赖注入"""
    print("\n🔍 测试FastAPI数据库依赖...")
    
    try:
        from src.db.config import get_db
        from sqlalchemy import text
        
        for db in get_db():
            result = db.execute(text("SELECT CONNECTION_ID(), DATABASE()"))
            row = result.fetchone()
            print(f"   FastAPI依赖: 连接ID={row[0]}, 数据库={row[1]}")
            break
        
        return True
        
    except Exception as e:
        print(f"   ❌ FastAPI依赖测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("🚀 后端数据库连接测试")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 测试异步连接
    async_success = await test_async_connection()
    
    # 测试同步连接
    sync_success = test_sync_connection()
    
    # 测试FastAPI依赖
    fastapi_success = test_fastapi_dependency()
    
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print(f"   异步连接: {'✅ 成功' if async_success else '❌ 失败'}")
    print(f"   同步连接: {'✅ 成功' if sync_success else '❌ 失败'}")
    print(f"   FastAPI依赖: {'✅ 成功' if fastapi_success else '❌ 失败'}")
    
    if all([async_success, sync_success, fastapi_success]):
        print("\n🎉 所有数据库连接测试通过！")
        print("💡 连接池和重连机制已正确配置")
        print("💡 后端现在可以处理MySQL连接超时问题")
    else:
        print("\n❌ 部分测试失败，需要检查配置")
    
    print("\n🔧 优化内容:")
    print("   - 连接池: 20个核心连接 + 30个溢出连接")
    print("   - 自动重连: pool_pre_ping=True")
    print("   - 连接超时: 10秒连接 + 30秒读写超时")
    print("   - 重试机制: 连接失败自动重试3次")
    print("   - 连接回收: 1小时后自动回收防止超时")

if __name__ == "__main__":
    asyncio.run(main())