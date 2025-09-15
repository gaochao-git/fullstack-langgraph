#!/usr/bin/env python3
"""
创建敏感数据扫描任务相关表的迁移脚本
"""

import sys
import os
from pathlib import Path

# 添加backend目录到Python路径
backend_path = str(Path(__file__).parent.parent)
sys.path.insert(0, backend_path)

from sqlalchemy import create_engine
from src.shared.db.config import SYNC_DATABASE_URL, Base
from src.apps.sensitive_scan.models import ScanTask, ScanFile

def create_tables():
    """创建扫描任务相关的表"""
    print(f"数据库连接: {SYNC_DATABASE_URL}")
    
    # 创建引擎
    engine = create_engine(SYNC_DATABASE_URL, echo=True)
    
    # 创建表
    print("开始创建表...")
    Base.metadata.create_all(bind=engine, tables=[
        ScanTask.__table__,
        ScanFile.__table__
    ])
    
    print("表创建完成！")
    
    # 验证表是否创建成功
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("\n当前数据库中的表:")
    for table in tables:
        print(f"  - {table}")
    
    if "scan_tasks" in tables and "scan_files" in tables:
        print("\n✅ 扫描任务表创建成功！")
    else:
        print("\n❌ 扫描任务表创建失败！")


if __name__ == "__main__":
    create_tables()