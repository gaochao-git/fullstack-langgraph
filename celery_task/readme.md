# Celery 智能体任务调度系统

基于 Celery 的智能体定时任务调度系统，支持动态配置、多队列优先级处理。

## 核心功能

- **动态任务发现**: 数据库配置变更30秒内自动生效，无需重启
- **多队列优先级**: system > priority_high > priority_low > celery
- **智能体集成**: 自动调用智能体API，支持超时控制和错误处理
- **任务监控**: 完整的执行状态跟踪和结果记录

## 快速启动

### 1. 启动 Worker
```bash
python run_worker.py
```

### 2. 启动 Beat 调度器
```bash
python run_beat.py
```

## 运行机制

### 任务调度流程
```
数据库配置 → DatabaseScheduler → Celery Beat → Redis队列 → Worker执行
```

### 智能体任务执行链
```
1. Beat扫描数据库任务配置 (PeriodicTask表)
2. 解析task_extra_config获取智能体参数
3. 发送任务到指定优先级队列
4. Worker执行execute_agent_periodic_task
5. 调用call_agent_task发送API请求
6. 记录执行结果到数据库
```

## 配置说明

### 数据库任务配置 (PeriodicTask表)
```json
{
  "task_type": "agent",
  "agent_id": "智能体ID", 
  "message": "发送消息",
  "user": "用户名",
  "queue": "priority_low",
  "timeout": 300
}
```

### 队列优先级
- `system`: 系统维护任务
- `priority_high`: 高优先级智能体任务  
- `priority_low`: 普通智能体任务(默认)
- `celery`: 兜底队列

## 主要文件

- `config.py`: Celery配置(Redis、MySQL、队列)
- `scheduler.py`: 动态数据库调度器
- `agent_tasks.py`: 智能体任务执行逻辑
- `run_worker.py`: Worker启动脚本
- `run_beat.py`: Beat启动脚本

## 环境要求

- Python 3.8+
- Redis (消息队列)
- MySQL (结果存储)
- Celery 5.3+
