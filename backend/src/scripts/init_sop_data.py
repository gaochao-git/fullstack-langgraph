"""Initialize SOP database with sample data."""
import asyncio
import json
from datetime import datetime

from ..database.config import async_engine, AsyncSessionLocal
from ..database.models import Base, SOPTemplate


async def create_tables():
    """Create database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created")


async def insert_sample_data():
    """Insert sample SOP data."""
    sample_sops = [
        {
            "sop_id": "SOP-DB-001",
            "sop_title": "MySQL数据库响应耗时升高诊断",
            "sop_category": "database",
            "sop_description": "诊断MySQL数据库响应时间过长的标准操作程序",
            "sop_severity": "high",
            "sop_steps": [
                {
                    "step": 1,
                    "description": "获取慢查询日志配置和阈值设置",
                    "ai_generated": False,
                    "tool": "execute_mysql_query",
                    "args": "SHOW VARIABLES WHERE Variable_name IN ('long_query_time', 'slow_query_log');",
                    "requires_approval": False
                },
                {
                    "step": 2,
                    "description": "确定分析范围",
                    "ai_generated": True,
                    "tool": "llm",
                    "args": "根据用户描述的响应耗时和慢查询阈值，确定分析范围，如果用户告诉了范围用用户的，否则用报警时间前后5分钟",
                    "requires_approval": False
                },
                {
                    "step": 3,
                    "description": "大模型判断是否需要分析慢查询日志",
                    "ai_generated": True,
                    "tool": "llm",
                    "args": "如果响应耗时小于慢查询阈值则跳过慢日志分析直接执行第5步，如果大于阈值则继续第4步",
                    "requires_approval": False
                },
                {
                    "step": 4,
                    "description": "从ES中查询指定时间范围的慢查询日志，分析是写慢查询还是读慢查询，查看扫描行数和锁等待情况",
                    "ai_generated": True,
                    "tool": "get_es_data",
                    "args": "index: mysql-slow-*, start_time: 动态生成, end_time: 动态生成, query: 动态生成",
                    "requires_approval": False
                },
                {
                    "step": 5,
                    "description": "获取指定时间范围内的磁盘IO使用率和CPU使用率，检查是否存在瓶颈或异常波动",
                    "ai_generated": True,
                    "tool": "get_zabbix_metric_data",
                    "args": "metric: [system.cpu.util[,user], disk.io.util[vda]], start_time: 动态生成, end_time: 动态生成",
                    "requires_approval": False
                },
                {
                    "step": 6,
                    "description": "如果CPU或者磁盘IO有瓶颈且当前仍然存在瓶颈，则排查CPU和IO占用前5名进程",
                    "ai_generated": False,
                    "tool": "execute_system_command",
                    "args": "top -b -n1 | head -12; iotop -b -n1 | head -10",
                    "requires_approval": False
                }
            ],
            "tools_required": [
                "execute_mysql_query",
                "get_es_data", 
                "get_es_indices",
                "get_es_trends_data",
                "get_zabbix_metric_data",
                "get_zabbix_metrics",
                "execute_system_command"
            ],
            "sop_recommendations": "建议优化识别到的慢查询SQL，为高频查询字段添加索引，重构复杂查询，联系DBA进行查询优化",
            "team_name": "ops-team",
            "create_by": "admin",
            "update_by": "admin"
        },
        {
            "sop_id": "SOP-SYS-101",
            "sop_title": "磁盘空间不足处理",
            "sop_category": "system",
            "sop_description": "处理磁盘空间不足的标准操作程序",
            "sop_severity": "medium",
            "sop_steps": [
                {
                    "step": 1,
                    "description": "检查磁盘使用情况",
                    "ai_generated": False,
                    "tool": "execute_system_command",
                    "args": "df -h",
                    "requires_approval": False
                },
                {
                    "step": 2,
                    "description": "查找大文件",
                    "ai_generated": False,
                    "tool": "execute_system_command", 
                    "args": "find /var/log -type f -size +100M -exec ls -lh {} \\;",
                    "requires_approval": False
                },
                {
                    "step": 3,
                    "description": "清理日志文件",
                    "ai_generated": False,
                    "tool": "execute_system_command",
                    "args": "find /var/log -name '*.log' -mtime +7 -delete",
                    "requires_approval": True
                }
            ],
            "tools_required": ["execute_system_command"],
            "sop_recommendations": "定期清理日志文件，配置日志轮转，监控磁盘使用率",
            "team_name": "ops-team",
            "create_by": "admin",
            "update_by": "admin"
        }
    ]
    
    async with AsyncSessionLocal() as session:
        try:
            for sop_data in sample_sops:
                # Check if SOP already exists
                existing = await session.get(SOPTemplate, sop_data["sop_id"])
                if existing:
                    print(f"⚠️  SOP {sop_data['sop_id']} already exists, skipping")
                    continue
                
                sop = SOPTemplate(
                    sop_id=sop_data["sop_id"],
                    sop_title=sop_data["sop_title"],
                    sop_category=sop_data["sop_category"],
                    sop_description=sop_data["sop_description"],
                    sop_severity=sop_data["sop_severity"],
                    sop_steps=sop_data["sop_steps"],
                    tools_required=sop_data["tools_required"],
                    sop_recommendations=sop_data["sop_recommendations"],
                    team_name=sop_data["team_name"],
                    create_by=sop_data["create_by"],
                    update_by=sop_data["update_by"],
                    create_time=datetime.utcnow(),
                    update_time=datetime.utcnow()
                )
                
                session.add(sop)
                print(f"✅ Added SOP: {sop_data['sop_id']}")
            
            await session.commit()
            print("✅ Sample data inserted successfully")
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Error inserting sample data: {e}")
            raise


async def main():
    """Main initialization function."""
    print("🚀 Initializing SOP database...")
    
    try:
        await create_tables()
        await insert_sample_data()
        print("🎉 SOP database initialization completed!")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False
    
    return True


if __name__ == "__main__":
    asyncio.run(main())