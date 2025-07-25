import os
import sys
import json
import uuid
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from celery_app.tasks import long_running_task, process_data, save_result
from celery_app.celery import app

def test_simple_task():
    """测试简单的异步任务"""
    task_id = str(uuid.uuid4())
    data = {'value': 42, 'should_fail': False}
    
    print(f"提交任务: {task_id}")
    result = long_running_task.delay(task_id, data)
    
    print(f"任务ID: {result.id}")
    print("任务已提交，可以使用以下命令查看任务状态:")
    print(f"python scripts/task_manager.py details {result.id} --show-result")

def test_chain_task():
    """测试链式任务"""
    # 创建任务链
    chain = process_data.s(10) | save_result.s()
    
    print("提交链式任务")
    result = chain()
    
    print(f"任务ID: {result.id}")
    print("任务已提交，可以使用以下命令查看任务状态:")
    print(f"python scripts/task_manager.py details {result.id} --show-result")

def test_failing_task():
    """测试失败的任务"""
    task_id = str(uuid.uuid4())
    data = {'value': 42, 'should_fail': True}
    
    print(f"提交预期会失败的任务: {task_id}")
    result = long_running_task.delay(task_id, data)
    
    print(f"任务ID: {result.id}")
    print("任务已提交，可以使用以下命令查看任务状态:")
    print(f"python scripts/task_manager.py details {result.id} --show-result")

if __name__ == '__main__':
    print("=== 测试简单的异步任务 ===")
    test_simple_task()
    
    print("\n=== 测试链式任务 ===")
    test_chain_task()
    
    print("\n=== 测试失败的任务 ===")
    test_failing_task() 