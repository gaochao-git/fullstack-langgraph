# 队列配置示例

## 概述

系统支持3个队列：
- `system`: 系统任务（健康检查、调度器更新等）
- `priority_high`: 高优先级智能体任务
- `priority_low`: 低优先级智能体任务（默认）

## 配置方法

在数据库表 `celery_periodic_task_configs` 的 `task_extra_config` 字段中配置队列：

### 高优先级智能体任务

```json
{
  "task_type": "agent",
  "agent_id": "urgent_diagnostic_agent",
  "message": "紧急故障诊断",
  "user": "admin",
  "timeout": 300,
  "queue": "priority_high"
}
```

### 低优先级智能体任务（默认）

```json
{
  "task_type": "agent", 
  "agent_id": "daily_report_agent",
  "message": "生成日常报告",
  "user": "system",
  "timeout": 600,
  "queue": "priority_low"
}
```

### 系统任务

系统任务自动路由到 `system` 队列，无需配置。

## Worker 启动方式

### 标准启动（推荐：单Worker处理所有队列，按优先级顺序）
```bash
python run_worker.py
```

这会启动一个Worker，按优先级顺序处理队列：`system` → `priority_high` → `priority_low`

### 扩展部署（多Worker实例）
```bash
# 启动多个Worker实例提高处理能力
python run_worker.py &  # Worker 1
python run_worker.py &  # Worker 2
python run_worker.py &  # Worker 3
```

## 队列监控

```bash
# 查看队列状态
python monitor_queues.py

# 查看任务详情
python debug_tasks.py
```

## 队列配置建议

### 高优先级队列 (priority_high)
- **适用场景**: 紧急告警、实时响应、VIP用户任务
- **超时设置**: 较短（5-15分钟）
- **并发配置**: 更多Worker进程
- **示例任务**: 故障诊断、安全告警处理

### 低优先级队列 (priority_low)  
- **适用场景**: 批量处理、定期报告、数据分析
- **超时设置**: 较长（30-60分钟）
- **并发配置**: 标准配置
- **示例任务**: 日报生成、数据清理、日常检查

### 系统队列 (system)
- **适用场景**: 系统维护、健康检查、调度器任务
- **超时设置**: 中等（10-30分钟）
- **并发配置**: 较少进程（系统任务通常不多）
- **示例任务**: Worker健康检查、调度配置更新

## 故障排查

### 队列积压
```bash
# 检查队列长度
python monitor_queues.py

# 增加对应队列的Worker数量
# 或调整任务超时时间和调度间隔
```

### 任务路由错误
- 检查 `task_extra_config` 中的 `queue` 字段
- 确认队列名称正确：`system`、`priority_high`、`priority_low`
- 无效队列名会自动降级到 `priority_low`

### Worker 无法处理特定队列
- 确认Worker启动时指定了正确的队列参数 `-Q`
- 检查Redis连接和队列创建情况