"""
Checkpoint管理 - 支持memory和mysql两种saver
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)

async def setup_postgres_tables():
    """手动初始化PostgreSQL表结构 - 仅在需要时使用"""
    postgres_uri = os.getenv("POSTGRES_CHECKPOINT_URI")
    if not postgres_uri:
        logger.error("POSTGRES_CHECKPOINT_URI未配置")
        return False
    
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        
        with PostgresSaver.from_conn_string(postgres_uri) as saver:
            saver.setup()
            logger.info("PostgreSQL checkpoint表初始化成功")
            return True
    except Exception as e:
        # 如果初始化失败，可能是表已存在，这通常是正常的
        if "already exists" in str(e) or "relation" in str(e):
            logger.info("PostgreSQL checkpoint表已存在，跳过初始化")
            return True
        else:
            logger.warning(f"PostgreSQL checkpoint表初始化遇到问题: {e}")
            logger.info("LangGraph将在首次使用时自动处理表结构")
            return False

def create_saver():
    """创建checkpoint saver"""
    checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
    print(f"checkpointer_type: {checkpointer_type}")
    
    if checkpointer_type == "postgres":
        try:
            # 方法1: 尝试使用同步PostgreSQL saver
            try:
                from langgraph.checkpoint.postgres import PostgresSaver
                import psycopg_pool
                postgres_uri = os.getenv("POSTGRES_CHECKPOINT_URI")
                if not postgres_uri:
                    logger.warning("POSTGRES_CHECKPOINT_URI未配置，回退到内存模式")
                    raise ValueError("PostgreSQL URI not configured")
                
                logger.info(f"使用PostgreSQL连接: {postgres_uri.split('@')[1] if '@' in postgres_uri else 'localhost'}")
                
                # 创建连接池并传递给PostgresSaver
                pool = psycopg_pool.ConnectionPool(postgres_uri, kwargs={"autocommit": True})
                saver = PostgresSaver(pool)
                
                # 测试连接并初始化
                with pool.connection() as conn:
                    temp_saver = PostgresSaver(conn)
                    temp_saver.setup()
                    logger.info("PostgreSQL checkpoint表初始化成功")
                
                logger.info("使用PostgreSQL checkpoint saver (连接池)")
                return saver
                
            except ImportError:
                logger.warning("psycopg_pool不可用，尝试异步PostgreSQL saver")
                # 方法2: 回到异步saver但使用正确的初始化
                from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
                postgres_uri = os.getenv("POSTGRES_CHECKPOINT_URI")
                saver_context = AsyncPostgresSaver.from_conn_string(postgres_uri)
                logger.info("使用异步PostgreSQL checkpoint saver")
                return saver_context
                
        except Exception as e:
            logger.warning(f"PostgreSQL saver创建失败，回退到内存模式: {e}")
    
    # 默认内存saver
    from langgraph.checkpoint.memory import MemorySaver
    logger.info("使用内存checkpoint saver")
    return MemorySaver()