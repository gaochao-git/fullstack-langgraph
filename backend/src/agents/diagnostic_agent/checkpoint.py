"""
Checkpoint管理 - 支持memory和mysql两种saver
"""

import os
import logging
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

logger = logging.getLogger(__name__)


def get_postgres_checkpointer():
    """
    Initialize PostgreSQL checkpointer with proper setup
    """
    import psycopg
    from psycopg_pool import ConnectionPool
    from langgraph.checkpoint.postgres import PostgresSaver
    
    connection_string = "postgresql://postgres:fffjjj@82.156.146.51:5432/langgraph_memory"
    
    # Step 1: Setup database schema with autocommit connection
    conn = psycopg.connect(connection_string, autocommit=True)
    try:
        checkpointer_setup = PostgresSaver(conn=conn)
        checkpointer_setup.setup()
        logger.info("PostgreSQL checkpoint表初始化成功")
    finally:
        conn.close()
    
    # Step 2: Create connection pool for production use
    pool = ConnectionPool(conninfo=connection_string, max_size=20)
    checkpointer = PostgresSaver(conn=pool)
    
    logger.info("使用PostgreSQL checkpoint saver")
    return checkpointer

def get_memory_checkpointer():
    """
    Initialize in-memory checkpointer
    """
    from langgraph.checkpoint.memory import MemorySaver
    logger.info("使用内存checkpoint saver")
    return MemorySaver()

def create_saver():
    """创建checkpoint saver"""
    checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
    print(f"checkpointer_type: {checkpointer_type}")
    
    if checkpointer_type == "postgres":
        try:
            return get_postgres_checkpointer()
        except Exception as e:
            print(f"PostgreSQL saver创建失败，回退到内存模式: {e}")
            logger.warning(f"PostgreSQL saver创建失败，回退到内存模式: {e}")
    
    # 默认内存saver
    return get_memory_checkpointer()