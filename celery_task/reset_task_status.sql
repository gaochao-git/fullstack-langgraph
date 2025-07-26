-- 重置任务状态SQL
-- 1. 重置所有智能体定时任务的运行状态
UPDATE celery_periodic_task_configs 
SET 
    task_last_run_time = NULL,
    task_run_count = 0,
    update_time = NOW(),
    update_by = 'system'
WHERE task_path = 'celery_app.agent_tasks.execute_agent_periodic_task';

-- 2. 清理旧的执行日志（可选）
DELETE FROM celery_task_records 
WHERE task_name LIKE 'execute_agent_%' OR task_name LIKE 'call_agent_%';

-- 3. 查看重置后的任务状态
SELECT 
    id,
    task_name,
    task_enabled,
    task_last_run_time,
    task_run_count,
    SUBSTRING(task_extra_config, 1, 50) as config_preview
FROM celery_periodic_task_configs 
WHERE task_path = 'celery_app.agent_tasks.execute_agent_periodic_task'
ORDER BY id;