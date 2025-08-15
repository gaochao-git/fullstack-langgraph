# Celery 智能体任务调度系统

基于 Celery 的智能体定时任务调度系统，支持动态配置、多队列优先级处理。

## 核心功能

- **动态任务发现**: 数据库配置变更30秒内自动生效，无需重启
- **多队列优先级**: system > priority_high > priority_low > celery
- **智能体集成**: 自动调用智能体API，支持超时控制和错误处理
- **任务监控**: 完整的执行状态跟踪和结果记录

## 快速启动

### 方式一：使用 Supervisor (推荐)
```bash
# 0. 安装依赖 (首次使用)
pip install -r requirements.txt

# 1. 启动 supervisord 守护进程
supervisord -c supervisord.conf

# 2. 查看进程状态
supervisorctl -c supervisord.conf status

# 3. 启动所有服务
supervisorctl -c supervisord.conf start all
```

### 方式二：手动启动
```bash
# 启动 Worker
python run_worker.py

# 启动 Beat 调度器  
python run_beat.py
```

## 服务管理

### Supervisor 常用命令
```bash
# 启动守护进程
supervisord -c supervisord.conf

# 查看进程状态
supervisorctl -c supervisord.conf status

# 启动/停止进程
supervisorctl -c supervisord.conf start all
supervisorctl -c supervisord.conf start celery-beat
supervisorctl -c supervisord.conf start celery-worker
supervisorctl -c supervisord.conf stop all

# 重启进程
supervisorctl -c supervisord.conf restart all
supervisorctl -c supervisord.conf restart celery-beat

# 查看日志
supervisorctl -c supervisord.conf tail -f celery-beat
supervisorctl -c supervisord.conf tail -f celery-worker

# 关闭 supervisord
supervisorctl -c supervisord.conf shutdown
```

### 日志文件位置

#### Celery应用日志（统一管理）
- 位置: `logs/celery_YYYYMMDD.log`
- 格式: 时间戳 - 模块名 - 级别 - [文件:行号] - 消息
- 轮转: 单文件最大50MB，保留30个历史文件
- 级别: 通过环境变量 `CELERY_LOG_LEVEL` 设置（默认INFO）

#### Supervisor进程管理日志
- Beat 进程日志: `logs/supervisor_beat.log`
- Worker 进程日志: `logs/supervisor_worker.log`
- Supervisor 主日志: `/tmp/supervisord.log`

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
- `logger.py`: 统一日志配置模块
- `scheduler.py`: 动态数据库调度器
- `agent_tasks.py`: 智能体任务执行逻辑
- `tasks.py`: 通用任务和信号处理
- `models.py`: 数据库模型定义
- `conf/celery_beat.conf`: Supervisor Beat配置
- `conf/celery_worker.conf`: Supervisor Worker配置

## 环境要求

- Python 3.12+
- Redis (消息队列)
- MySQL (结果存储)
- Celery 5.3+
