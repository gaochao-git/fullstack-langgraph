#!/usr/bin/env python3
"""
Celery Beat 启动脚本
直接运行: python run_beat.py
"""
import os
import sys
import logging

# ==================== 配置区域 ====================
# 可以根据需要修改以下配置

LOG_LEVEL = 'INFO'                # 日志级别: DEBUG, INFO, WARNING, ERROR
ENABLE_HEALTH_CHECK = True        # 是否启用启动前健康检查

# ================================================

# 配置日志
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_imports():
    """测试关键模块导入"""
    logger.info("测试模块导入...")
    
    try:
        import celery
        logger.info(f"✅ Celery 版本: {celery.__version__}")
    except ImportError as e:
        logger.error(f"❌ Celery 导入失败: {e}")
        return False
    
    try:
        import redis
        logger.info(f"✅ Redis 模块版本: {redis.__version__}")
    except ImportError as e:
        logger.error(f"❌ Redis 导入失败: {e}")
        return False
    
    try:
        import pymysql
        logger.info(f"✅ PyMySQL 版本: {pymysql.__version__}")
    except ImportError as e:
        logger.error(f"❌ PyMySQL 导入失败: {e}")
        return False
    
    return True

def test_database():
    """测试数据库连接"""
    logger.info("测试数据库连接...")
    
    try:
        import pymysql
        config = {
            'host': '82.156.146.51',
            'port': 3306,
            'user': 'gaochao',
            'password': 'fffjjj',
            'database': 'celery_tasks',
            'charset': 'utf8mb4'
        }
        
        connection = pymysql.connect(**config)
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM celery_periodic_task_configs WHERE task_enabled = 1")
        count = cursor.fetchone()[0]
        logger.info(f"✅ 数据库连接成功，找到 {count} 个启用的任务")
        cursor.close()
        connection.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库连接失败: {e}")
        return False

def test_redis():
    """测试 Redis 连接"""
    logger.info("测试 Redis 连接...")
    
    try:
        import redis
        r = redis.Redis(host='82.156.146.51', port=6379, db=0, password='fffjjj')
        r.ping()
        logger.info("✅ Redis 连接成功")
        return True
        
    except Exception as e:
        logger.error(f"❌ Redis 连接失败: {e}")
        return False

def start_beat_safe():
    """安全启动 Celery Beat"""
    logger.info("准备启动 Celery Beat...")
    
    # 添加当前目录到路径
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    try:
        # 延迟导入 celery app
        from celery_app.celery import app
        logger.info("✅ Celery 应用导入成功")
        
        # 启动参数
        argv = [
            'beat',
            f'--loglevel={LOG_LEVEL}',
        ]
        
        logger.info("启动 Celery Beat...")
        logger.info("=" * 50)
        
        # 启动 Beat
        app.start(argv)
        
    except Exception as e:
        logger.error(f"❌ Celery Beat 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    logger.info("🚀 Celery Beat 启动器 (含动态调度器)")
    logger.info("=" * 50)
    
    if ENABLE_HEALTH_CHECK:
        # 运行前置检查
        checks = [
            ("模块导入", test_imports),
            ("数据库连接", test_database), 
            ("Redis连接", test_redis),
        ]
        
        all_passed = True
        for check_name, check_func in checks:
            logger.info(f"检查: {check_name}")
            if not check_func():
                all_passed = False
                logger.error(f"❌ {check_name} 检查失败")
            else:
                logger.info(f"✅ {check_name} 检查通过")
            logger.info("-" * 30)
        
        if all_passed:
            logger.info("🎉 所有检查通过，启动 Celery Beat...")
            start_beat_safe()
        else:
            logger.error("❌ 检查失败，请修复问题后重试")
            logger.info("提示: 可以设置 ENABLE_HEALTH_CHECK = False 跳过检查")
            sys.exit(1)
    else:
        logger.info("跳过健康检查，直接启动 Celery Beat...")
        start_beat_safe()