-- 清理定时任务数据库 - 只保留必要的2个任务
-- 1. 更新智能体任务的task_path
UPDATE celery_periodic_task_configs 
SET task_path = 'celery_app.agent_tasks.execute_agent_periodic_task' 
WHERE id = 17;

-- 2. 删除所有无用任务，只保留ID 3和17
DELETE FROM celery_periodic_task_configs 
WHERE id NOT IN (3, 17);

-- 3. 查看清理后的结果
SELECT id, task_name, task_path, task_enabled, 
       SUBSTRING(task_extra_config, 1, 100) as config_preview 
FROM celery_periodic_task_configs 
ORDER BY id;