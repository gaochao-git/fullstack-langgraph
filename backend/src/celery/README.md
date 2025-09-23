# Celery集成说明

## 概述

Celery已经集成到backend项目中，用于处理异步任务和定时任务。

## 目录结构

```
backend/src/celery/
├── __init__.py          # Celery应用初始化
├── celery.py            # Celery主配置
├── config.py            # Celery配置文件
├── logger.py            # 日志配置
├── models.py            # 数据库模型
├── scheduler.py         # 自定义数据库调度器
├── tasks.py             # 系统任务定义
└── agent_tasks.py       # 智能体相关任务
```

## 配置说明

### 环境变量

- `CELERY_BROKER_URL`: Redis连接URL（默认使用项目配置的Redis）
- `CELERY_DATABASE_NAME`: Celery数据库名称（默认: celery_tasks）

### 队列配置

系统使用4个队列，按优先级排序：

1. `system`: 系统任务队列（最高优先级）
2. `priority_high`: 高优先级任务队列
3. `priority_low`: 低优先级任务队列
4. `celery`: 默认队列

## 使用方法

### 1. 启动Celery服务

```bash
# 进入backend目录
cd backend

# 启动所有服务（Worker + Beat）
./celery_manage.sh start

# 单独启动Worker
./celery_manage.sh start worker

# 单独启动Beat
./celery_manage.sh start beat
```

### 2. 管理Celery服务

```bash
# 查看服务状态
./celery_manage.sh status

# 停止服务
./celery_manage.sh stop

# 重启服务
./celery_manage.sh restart

# 查看日志
./celery_manage.sh logs worker
./celery_manage.sh logs beat

# 清理队列
./celery_manage.sh purge

# 检查活动任务
./celery_manage.sh inspect active
```

### 3. 在业务模块中定义任务

在各业务模块中创建`tasks.py`文件：

```python
from src.celery.celery import app
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

@app.task(name='module_name.task_name')
def my_async_task(param1, param2):
    """异步任务示例"""
    logger.info(f"执行任务: {param1}, {param2}")
    # 任务逻辑
    return "任务结果"
```

### 4. 调用异步任务

```python
from src.apps.your_module.tasks import my_async_task

# 异步执行
result = my_async_task.delay(param1="value1", param2="value2")

# 获取任务ID
task_id = result.id

# 检查任务状态
if result.ready():
    # 获取结果
    task_result = result.get()
```

### 5. 定时任务配置

定时任务通过数据库动态配置，存储在`celery_periodic_task_configs`表中。

#### 通过API管理定时任务

```python
# 创建定时任务示例
POST /api/v1/scheduled-tasks
{
    "task_name": "清理过期会话",
    "task_path": "src.apps.auth.tasks.cleanup_expired_sessions_task",
    "task_type": "system",
    "task_enabled": true,
    "task_crontab_minute": "0",
    "task_crontab_hour": "*/2",
    "task_extra_config": {
        "queue": "system"
    }
}
```

## 已集成的任务

### 1. 认证模块任务 (`src.apps.auth.tasks`)

- `auth.cleanup_expired_sessions`: 清理过期会话
- `auth.cleanup_old_sessions`: 清理旧会话记录
- `auth.session_statistics`: 生成会话统计

### 2. 定时任务模块 (`src.apps.scheduled_task.tasks`)

- `scheduled_task.test_task`: 测试任务
- `scheduled_task.cleanup_old_logs`: 清理旧日志

### 3. 智能体任务 (`src.apps.agent.tasks`)

- `execute_agent_periodic_task`: 执行智能体定时任务
- `periodic_agent_health_check`: 智能体健康检查

## 监控和调试

### 查看任务执行日志

```bash
# 实时查看Worker日志
./celery_manage.sh logs worker

# 查看最近100行日志
./celery_manage.sh logs worker 100
```

### 检查任务状态

```bash
# 查看活动任务
./celery_manage.sh inspect active

# 查看计划任务
./celery_manage.sh inspect scheduled

# 查看统计信息
./celery_manage.sh inspect stats
```

## 注意事项

1. **数据库配置**: Celery使用独立的数据库存储任务结果和定时任务配置
2. **异步函数处理**: 对于异步函数，使用`asyncio.run()`在Celery任务中运行
3. **任务命名**: 建议使用`module_name.task_name`格式命名任务
4. **错误处理**: 任务中的异常会被Celery捕获并记录
5. **任务超时**: 可以在任务装饰器中设置`time_limit`参数

## 故障排除

### Worker无法启动

1. 检查Redis连接是否正常
2. 检查虚拟环境是否激活
3. 查看启动日志：`cat logs/celery/worker_startup.log`

### 定时任务不执行

1. 确保Beat服务正在运行
2. 检查数据库中的任务配置是否正确
3. 查看Beat日志：`./celery_manage.sh logs beat`

### 任务执行失败

1. 查看Worker日志获取错误信息
2. 检查任务参数是否正确
3. 确认相关服务（如数据库、API）是否可访问