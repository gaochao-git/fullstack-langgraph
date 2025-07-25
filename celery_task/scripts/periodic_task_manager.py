import os
import sys
import json
import argparse
from datetime import datetime
from tabulate import tabulate

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from celery_app.models import get_session, PeriodicTask

def list_tasks(args):
    """列出所有定时任务"""
    session = get_session()
    
    try:
        tasks = session.query(PeriodicTask).all()
        
        headers = ["ID", "名称", "任务", "间隔(秒)", "Crontab", "启用", "上次运行", "运行次数"]
        rows = []
        
        for task in tasks:
            crontab_expr = ""
            if task.task_crontab_minute is not None:
                crontab_expr = f"{task.task_crontab_minute} {task.task_crontab_hour} {task.task_crontab_day_of_month} {task.task_crontab_month_of_year} {task.task_crontab_day_of_week}"
            
            rows.append([
                task.id,
                task.task_name,
                task.task_path,
                task.task_interval,
                crontab_expr if crontab_expr else "-",
                "是" if task.task_enabled else "否",
                task.task_last_run_time.strftime("%Y-%m-%d %H:%M:%S") if task.task_last_run_time else "-",
                task.task_run_count
            ])
        
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    finally:
        session.close()

def add_task(args):
    """添加定时任务"""
    session = get_session()
    
    try:
        # 检查任务名称是否已存在
        existing = session.query(PeriodicTask).filter_by(task_name=args.name).first()
        if existing:
            print(f"错误: 任务名称 '{args.name}' 已存在")
            return
        
        # 准备参数
        args_list = []
        kwargs_dict = {}
        
        if args.args:
            args_list = args.args.split(',')
        
        if args.kwargs:
            for kv in args.kwargs.split(','):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    kwargs_dict[k.strip()] = v.strip()
        
        # 创建任务
        task = PeriodicTask(
            task_name=args.name,
            task_path=args.task,
            task_enabled=True,
            task_description=args.description,
            create_by=args.user or 'admin',  # 添加创建人
            update_by=args.user or 'admin'   # 添加更新人
        )
        
        # 设置间隔或Crontab
        if args.interval:
            task.task_interval = args.interval
        else:
            task.task_crontab_minute = args.minute
            task.task_crontab_hour = args.hour
            task.task_crontab_day_of_week = args.day_of_week
            task.task_crontab_day_of_month = args.day_of_month
            task.task_crontab_month_of_year = args.month_of_year
        
        # 设置参数
        task.task_args = json.dumps(args_list)
        task.task_kwargs = json.dumps(kwargs_dict)
        
        session.add(task)
        session.commit()
        
        print(f"成功添加定时任务: {args.name}")
    except Exception as e:
        session.rollback()
        print(f"添加任务失败: {str(e)}")
    finally:
        session.close()

def update_task(args):
    """更新定时任务"""
    session = get_session()
    
    try:
        task = session.query(PeriodicTask).filter_by(id=args.id).first()
        
        if not task:
            print(f"错误: 找不到ID为 {args.id} 的任务")
            return
        
        # 更新任务属性
        if args.name:
            task.task_name = args.name
        
        if args.task:
            task.task_path = args.task
        
        if args.description:
            task.task_description = args.description
        
        if args.enabled is not None:
            task.task_enabled = args.enabled.lower() == 'true'
        
        # 更新更新人
        task.update_by = args.user or 'admin'
        
        # 更新间隔或Crontab
        if args.interval:
            task.task_interval = args.interval
            # 清除Crontab设置
            task.task_crontab_minute = None
            task.task_crontab_hour = None
            task.task_crontab_day_of_week = None
            task.task_crontab_day_of_month = None
            task.task_crontab_month_of_year = None
        elif any([args.minute, args.hour, args.day_of_week, args.day_of_month, args.month_of_year]):
            # 清除间隔设置
            task.task_interval = None
            
            # 更新Crontab设置
            if args.minute:
                task.task_crontab_minute = args.minute
            
            if args.hour:
                task.task_crontab_hour = args.hour
            
            if args.day_of_week:
                task.task_crontab_day_of_week = args.day_of_week
            
            if args.day_of_month:
                task.task_crontab_day_of_month = args.day_of_month
            
            if args.month_of_year:
                task.task_crontab_month_of_year = args.month_of_year
        
        # 更新参数
        if args.args:
            args_list = args.args.split(',')
            task.task_args = json.dumps(args_list)
        
        if args.kwargs:
            kwargs_dict = {}
            for kv in args.kwargs.split(','):
                if '=' in kv:
                    k, v = kv.split('=', 1)
                    kwargs_dict[k.strip()] = v.strip()
            task.task_kwargs = json.dumps(kwargs_dict)
        
        session.commit()
        
        print(f"成功更新任务: {task.task_name}")
    except Exception as e:
        session.rollback()
        print(f"更新任务失败: {str(e)}")
    finally:
        session.close()

def delete_task(args):
    """删除定时任务"""
    session = get_session()
    
    try:
        task = session.query(PeriodicTask).filter_by(id=args.id).first()
        
        if not task:
            print(f"错误: 找不到ID为 {args.id} 的任务")
            return
        
        task_name = task.task_name
        session.delete(task)
        session.commit()
        
        print(f"成功删除任务: {task_name}")
    except Exception as e:
        session.rollback()
        print(f"删除任务失败: {str(e)}")
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(description='Celery 定时任务管理工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 列出任务
    list_parser = subparsers.add_parser('list', help='列出所有定时任务')
    
    # 添加任务
    add_parser = subparsers.add_parser('add', help='添加定时任务')
    add_parser.add_argument('--name', required=True, help='任务名称')
    add_parser.add_argument('--task', required=True, help='任务路径 (例如: celery_app.tasks.periodic_task)')
    add_parser.add_argument('--interval', type=int, help='间隔秒数')
    add_parser.add_argument('--minute', help='Crontab分钟 (0-59, *, */5 等)')
    add_parser.add_argument('--hour', help='Crontab小时 (0-23, *)')
    add_parser.add_argument('--day-of-week', help='Crontab星期 (0-6 或 mon,tue,wed,thu,fri,sat,sun)')
    add_parser.add_argument('--day-of-month', help='Crontab日期 (1-31, *)')
    add_parser.add_argument('--month-of-year', help='Crontab月份 (1-12, *)')
    add_parser.add_argument('--args', help='参数列表 (逗号分隔)')
    add_parser.add_argument('--kwargs', help='关键字参数 (格式: key1=value1,key2=value2)')
    add_parser.add_argument('--description', help='任务描述')
    add_parser.add_argument('--user', help='操作用户')
    
    # 更新任务
    update_parser = subparsers.add_parser('update', help='更新定时任务')
    update_parser.add_argument('id', type=int, help='任务ID')
    update_parser.add_argument('--name', help='任务名称')
    update_parser.add_argument('--task', help='任务路径')
    update_parser.add_argument('--interval', type=int, help='间隔秒数')
    update_parser.add_argument('--minute', help='Crontab分钟')
    update_parser.add_argument('--hour', help='Crontab小时')
    update_parser.add_argument('--day-of-week', help='Crontab星期')
    update_parser.add_argument('--day-of-month', help='Crontab日期')
    update_parser.add_argument('--month-of-year', help='Crontab月份')
    update_parser.add_argument('--args', help='参数列表 (逗号分隔)')
    update_parser.add_argument('--kwargs', help='关键字参数 (格式: key1=value1,key2=value2)')
    update_parser.add_argument('--enabled', help='是否启用 (true/false)')
    update_parser.add_argument('--description', help='任务描述')
    update_parser.add_argument('--user', help='操作用户')
    
    # 删除任务
    delete_parser = subparsers.add_parser('delete', help='删除定时任务')
    delete_parser.add_argument('id', type=int, help='任务ID')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_tasks(args)
    elif args.command == 'add':
        add_task(args)
    elif args.command == 'update':
        update_task(args)
    elif args.command == 'delete':
        delete_task(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 