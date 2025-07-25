#!/usr/bin/env python3
"""
数据迁移脚本：从PostgreSQL迁移到MySQL
将非checkpoint开头的表数据从PostgreSQL迁移到MySQL
"""

import asyncio
import asyncpg
import aiomysql
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 数据库连接配置
PG_CONFIG = {
    'host': '82.156.146.51',
    'port': 5432,
    'user': 'gaochao',
    'password': 'fffjjj',
    'database': 'langgraph_memory'
}

MYSQL_CONFIG = {
    'host': '82.156.146.51',
    'port': 3306,
    'user': 'gaochao',
    'password': 'fffjjj',
    'db': 'omind',
    'charset': 'utf8mb4'
}

# 需要迁移的表映射 (PostgreSQL表名 -> MySQL表名)
TABLES_TO_MIGRATE = {
    'sop_prompt_templates': 'sop_prompt_templates',
    'mcp_servers': 'mcp_servers', 
    'agent_configs': 'agent_configs',
    'ai_model_configs': 'ai_model_configs',
    'users': 'users',
    'user_threads': 'user_threads'
}

class DataMigrator:
    def __init__(self):
        self.pg_conn = None
        self.mysql_conn = None
        
    async def connect_databases(self):
        """连接到PostgreSQL和MySQL数据库"""
        try:
            # 连接PostgreSQL
            self.pg_conn = await asyncpg.connect(**PG_CONFIG)
            logger.info("✅ PostgreSQL连接成功")
            
            # 连接MySQL
            self.mysql_conn = await aiomysql.connect(**MYSQL_CONFIG)
            logger.info("✅ MySQL连接成功")
            
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            raise
    
    async def close_connections(self):
        """关闭数据库连接"""
        if self.pg_conn:
            await self.pg_conn.close()
        if self.mysql_conn:
            await self.mysql_conn.ensure_closed()
        logger.info("🔒 数据库连接已关闭")
    
    async def check_table_exists(self, table_name: str, db_type: str = 'mysql') -> bool:
        """检查表是否存在"""
        try:
            if db_type == 'postgresql':
                query = """
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
                """
                result = await self.pg_conn.fetchval(query, table_name)
            else:  # MySQL
                cursor = await self.mysql_conn.cursor()
                query = "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s AND table_name = %s"
                await cursor.execute(query, (MYSQL_CONFIG['db'], table_name))
                result = await cursor.fetchone()
                result = result[0] if result else 0
                await cursor.close()
            
            return result > 0
        except Exception as e:
            logger.error(f"检查表 {table_name} 是否存在时出错: {e}")
            return False
    
    async def get_table_data(self, table_name: str) -> List[Dict[str, Any]]:
        """从PostgreSQL获取表数据"""
        try:
            # 先检查表是否存在
            if not await self.check_table_exists(table_name, 'postgresql'):
                logger.warning(f"⚠️  PostgreSQL中表 {table_name} 不存在，跳过")
                return []
            
            # 获取表数据
            query = f"SELECT * FROM {table_name}"
            rows = await self.pg_conn.fetch(query)
            
            # 转换为字典列表
            data = []
            for row in rows:
                row_dict = dict(row)
                # 处理特殊数据类型
                for key, value in row_dict.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    elif value is None:
                        row_dict[key] = None
                    # JSON字段保持原样，MySQL会自动处理
                data.append(row_dict)
            
            logger.info(f"📊 从 {table_name} 获取了 {len(data)} 行数据")
            return data
            
        except Exception as e:
            logger.error(f"❌ 获取表 {table_name} 数据失败: {e}")
            return []
    
    async def clear_mysql_table(self, table_name: str):
        """清空MySQL表数据"""
        try:
            cursor = await self.mysql_conn.cursor()
            await cursor.execute(f"DELETE FROM {table_name}")
            await self.mysql_conn.commit()
            await cursor.close()
            logger.info(f"🗑️  清空MySQL表 {table_name}")
        except Exception as e:
            logger.error(f"❌ 清空表 {table_name} 失败: {e}")
    
    async def insert_mysql_data(self, table_name: str, data: List[Dict[str, Any]]):
        """将数据插入MySQL表"""
        if not data:
            logger.info(f"📝 表 {table_name} 无数据需要插入")
            return
        
        try:
            cursor = await self.mysql_conn.cursor()
            
            # 构建插入SQL
            first_row = data[0]
            columns = list(first_row.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join([f"`{col}`" for col in columns])
            
            sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            
            # 准备数据
            values_list = []
            for row in data:
                values = []
                for col in columns:
                    value = row[col]
                    # 处理JSON字段
                    if isinstance(value, (dict, list)):
                        value = json.dumps(value, ensure_ascii=False)
                    values.append(value)
                values_list.append(values)
            
            # 批量插入
            await cursor.executemany(sql, values_list)
            await self.mysql_conn.commit()
            await cursor.close()
            
            logger.info(f"✅ 成功插入 {len(data)} 行数据到表 {table_name}")
            
        except Exception as e:
            logger.error(f"❌ 插入数据到表 {table_name} 失败: {e}")
            logger.error(f"错误SQL: {sql}")
            if data:
                logger.error(f"示例数据: {data[0]}")
    
    async def migrate_table(self, pg_table: str, mysql_table: str):
        """迁移单个表"""
        logger.info(f"🚀 开始迁移表: {pg_table} -> {mysql_table}")
        
        # 检查MySQL表是否存在
        if not await self.check_table_exists(mysql_table, 'mysql'):
            logger.error(f"❌ MySQL表 {mysql_table} 不存在，请先创建表结构")
            return
        
        # 获取PostgreSQL数据
        data = await self.get_table_data(pg_table)
        
        if data:
            # 清空MySQL表
            await self.clear_mysql_table(mysql_table)
            
            # 插入数据
            await self.insert_mysql_data(mysql_table, data)
        
        logger.info(f"✅ 表 {pg_table} 迁移完成")
    
    async def migrate_all_tables(self):
        """迁移所有表"""
        logger.info("🚀 开始数据迁移...")
        
        for pg_table, mysql_table in TABLES_TO_MIGRATE.items():
            try:
                await self.migrate_table(pg_table, mysql_table)
            except Exception as e:
                logger.error(f"❌ 迁移表 {pg_table} 时出错: {e}")
                continue
        
        logger.info("🎉 数据迁移完成！")
    
    async def verify_migration(self):
        """验证迁移结果"""
        logger.info("🔍 验证迁移结果...")
        
        for pg_table, mysql_table in TABLES_TO_MIGRATE.items():
            try:
                # 获取PostgreSQL行数
                if await self.check_table_exists(pg_table, 'postgresql'):
                    pg_count = await self.pg_conn.fetchval(f"SELECT COUNT(*) FROM {pg_table}")
                else:
                    pg_count = 0
                
                # 获取MySQL行数
                if await self.check_table_exists(mysql_table, 'mysql'):
                    cursor = await self.mysql_conn.cursor()
                    await cursor.execute(f"SELECT COUNT(*) FROM {mysql_table}")
                    mysql_count = (await cursor.fetchone())[0]
                    await cursor.close()
                else:
                    mysql_count = 0
                
                status = "✅" if pg_count == mysql_count else "❌"
                logger.info(f"{status} {pg_table}: PostgreSQL({pg_count}) -> MySQL({mysql_count})")
                
            except Exception as e:
                logger.error(f"❌ 验证表 {pg_table} 时出错: {e}")

async def main():
    """主函数"""
    migrator = DataMigrator()
    
    try:
        # 连接数据库
        await migrator.connect_databases()
        
        # 执行迁移
        await migrator.migrate_all_tables()
        
        # 验证结果
        await migrator.verify_migration()
        
    except Exception as e:
        logger.error(f"❌ 迁移过程中出错: {e}")
    finally:
        # 关闭连接
        await migrator.close_connections()

if __name__ == "__main__":
    asyncio.run(main())