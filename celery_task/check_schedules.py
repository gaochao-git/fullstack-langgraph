#!/usr/bin/env python3
"""
检查定时任务调度间隔配置
"""

import sys
import os
from datetime import datetime

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from celery_app.models import get_session, PeriodicTask

def main():
    print(f"📅 定时任务调度配置检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    session = get_session()
    
    try:
        # 获取所有启用的任务
        tasks = session.query(PeriodicTask).filter_by(task_enabled=True).all()
        
        if not tasks:
            print("❌ 没有找到启用的定时任务")
            return
        
        print(f"📊 找到 {len(tasks)} 个启用的定时任务:")
        print()
        
        for task in tasks:
            print(f"🎯 任务名: {task.task_name}")
            print(f"   ID: {task.id}")
            print(f"   路径: {task.task_path}")
            
            # 显示调度配置
            if task.task_interval:
                print(f"   📍 调度方式: 间隔调度")
                print(f"   ⏱️  间隔时间: {task.task_interval} 秒 ({task.task_interval/60:.1f} 分钟)")
            else:
                print(f"   📍 调度方式: Crontab调度")
                print(f"   ⏱️  Cron表达式:")
                print(f"      分钟: {task.task_crontab_minute or '*'}")
                print(f"      小时: {task.task_crontab_hour or '*'}")
                print(f"      星期: {task.task_crontab_day_of_week or '*'}")
                print(f"      日期: {task.task_crontab_day_of_month or '*'}")
                print(f"      月份: {task.task_crontab_month_of_year or '*'}")
            
            # 显示运行统计
            print(f"   📈 运行统计:")
            print(f"      上次运行: {task.task_last_run_time or '从未运行'}")
            print(f"      运行次数: {task.task_run_count or 0}")
            
            # 解析额外配置
            if task.task_extra_config:
                try:
                    import json
                    extra_config = json.loads(task.task_extra_config)
                    task_type = extra_config.get('task_type', 'unknown')
                    
                    print(f"   🏷️  任务类型: {task_type}")
                    
                    if task_type == 'agent':
                        agent_id = extra_config.get('agent_id', 'N/A')
                        message = extra_config.get('message', 'N/A')
                        user = extra_config.get('user', 'system')
                        timeout = extra_config.get('timeout', 'N/A')
                        
                        print(f"      智能体ID: {agent_id}")
                        print(f"      消息: {message[:50]}{'...' if len(message) > 50 else ''}")
                        print(f"      用户: {user}")
                        print(f"      超时: {timeout}秒" if timeout else "      超时: 默认")
                        
                        # 分析调度冲突风险
                        if task.task_interval:
                            interval_min = task.task_interval / 60
                            timeout_min = (timeout or 300) / 60
                            
                            print(f"   ⚠️  风险分析:")
                            if interval_min < timeout_min:
                                risk_level = "🔴 高风险"
                                advice = "调度间隔小于任务超时，可能导致任务堆积"
                            elif interval_min < timeout_min * 1.5:
                                risk_level = "🟡 中风险"  
                                advice = "调度间隔接近任务超时，建议增加缓冲时间"
                            else:
                                risk_level = "🟢 低风险"
                                advice = "调度间隔合理"
                            
                            print(f"      {risk_level}: {advice}")
                            print(f"      建议调度间隔: ≥ {timeout_min * 1.5:.1f} 分钟")
                        
                except json.JSONDecodeError:
                    print(f"   ⚠️  额外配置JSON解析失败")
            
            print(f"   {'-' * 60}")
        
        # 总体建议
        print("\n💡 优化建议:")
        print("1. 确保调度间隔 > 任务最大执行时间 * 1.5")
        print("2. 监控任务执行时间，及时调整超时配置")
        print("3. 对于长时间运行的任务，考虑异步回调机制")
        print("4. 定期清理失败或僵尸任务")
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        
    finally:
        session.close()

if __name__ == '__main__':
    main()