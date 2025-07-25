import os
import sys
import argparse
import json
from tabulate import tabulate

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from celery_app.models import get_session, Task

def list_tasks(args):
    """列出所有任务"""
    session = get_session()
    
    try:
        if args.status:
            tasks = session.query(Task).filter_by(task_status=args.status.upper()).all()
        else:
            tasks = session.query(Task).all()
        
        headers = ["ID", "任务ID", "名称", "状态", "创建时间", "开始时间", "完成时间", "重试次数"]
        rows = []
        
        for task in tasks:
            rows.append([
                task.id,
                task.task_id,
                task.task_name,
                task.task_status,
                task.create_time.strftime("%Y-%m-%d %H:%M:%S"),
                task.task_start_time.strftime("%Y-%m-%d %H:%M:%S") if task.task_start_time else "-",
                task.task_complete_time.strftime("%Y-%m-%d %H:%M:%S") if task.task_complete_time else "-",
                task.task_retry_count
            ])
        
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    finally:
        session.close()

def show_task_details(args):
    """显示任务详情"""
    session = get_session()
    
    try:
        task = session.query(Task).filter_by(task_id=args.task_id).first()
        
        if not task:
            print(f"找不到任务ID为 {args.task_id} 的任务")
            return
        
        print(f"任务ID: {task.task_id}")
        print(f"任务名称: {task.task_name}")
        print(f"状态: {task.task_status}")
        print(f"创建时间: {task.create_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"开始时间: {task.task_start_time.strftime('%Y-%m-%d %H:%M:%S') if task.task_start_time else '-'}")
        print(f"完成时间: {task.task_complete_time.strftime('%Y-%m-%d %H:%M:%S') if task.task_complete_time else '-'}")
        print(f"重试次数: {task.task_retry_count}")
        
        if task.task_args:
            print(f"参数: {task.task_args}")
        
        if task.task_kwargs:
            print(f"关键字参数: {task.task_kwargs}")
        
        if args.show_result and task.task_result:
            try:
                result = json.loads(task.task_result)
                print("\n结果:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            except:
                print(f"\n结果: {task.task_result}")
        
        if task.task_traceback:
            print("\n错误追踪:")
            print(task.task_traceback)
    finally:
        session.close()

def main():
    parser = argparse.ArgumentParser(description='Celery 任务管理工具')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # 列出任务
    list_parser = subparsers.add_parser('list', help='列出任务')
    list_parser.add_argument('--status', help='按状态筛选 (PENDING, STARTED, SUCCESS, FAILURE)')
    
    # 任务详情
    details_parser = subparsers.add_parser('details', help='显示任务详情')
    details_parser.add_argument('task_id', help='任务ID')
    details_parser.add_argument('--show-result', action='store_true', help='显示任务结果')
    
    args = parser.parse_args()
    
    if args.command == 'list':
        list_tasks(args)
    elif args.command == 'details':
        show_task_details(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main() 