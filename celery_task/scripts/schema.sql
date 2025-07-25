-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS celery_tasks CHARACTER SET utf8mb4;

USE celery_tasks;

-- 异步任务记录表
CREATE TABLE IF NOT EXISTS `celery_task_records` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_id` varchar(255) NOT NULL COMMENT 'Celery任务ID',
  `task_name` varchar(255) NOT NULL COMMENT '任务名称',
  `task_status` varchar(50) DEFAULT 'PENDING' COMMENT '任务状态',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(100) DEFAULT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `task_start_time` datetime DEFAULT NULL COMMENT '开始执行时间',
  `task_complete_time` datetime DEFAULT NULL COMMENT '完成时间',
  `task_result` text DEFAULT NULL COMMENT '任务结果',
  `task_traceback` text DEFAULT NULL COMMENT '错误追踪信息',
  `task_retry_count` int(11) DEFAULT 0 COMMENT '重试次数',
  `task_args` text DEFAULT NULL COMMENT '任务参数',
  `task_kwargs` text DEFAULT NULL COMMENT '任务关键字参数',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `idx_task_status` (`task_status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='异步任务记录表';

-- 定时任务执行记录表
CREATE TABLE IF NOT EXISTS `celery_periodic_task_execution_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_name` varchar(255) NOT NULL COMMENT '任务名称',
  `task_schedule_time` datetime NOT NULL COMMENT '计划执行时间',
  `task_execute_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '实际执行时间',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(100) DEFAULT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `task_status` varchar(50) DEFAULT 'SUCCESS' COMMENT '执行状态',
  `task_result` text DEFAULT NULL COMMENT '执行结果',
  PRIMARY KEY (`id`),
  KEY `idx_task_name` (`task_name`),
  KEY `idx_task_schedule_time` (`task_schedule_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务执行记录表';

-- 定时任务配置表
CREATE TABLE IF NOT EXISTS `celery_periodic_task_configs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_name` varchar(255) NOT NULL COMMENT '任务名称',
  `task_path` varchar(255) NOT NULL COMMENT '任务路径',
  `task_interval` int(11) DEFAULT NULL COMMENT '间隔秒数',
  `task_crontab_minute` varchar(64) DEFAULT NULL COMMENT 'Crontab分钟',
  `task_crontab_hour` varchar(64) DEFAULT NULL COMMENT 'Crontab小时',
  `task_crontab_day_of_week` varchar(64) DEFAULT NULL COMMENT 'Crontab星期',
  `task_crontab_day_of_month` varchar(64) DEFAULT NULL COMMENT 'Crontab日期',
  `task_crontab_month_of_year` varchar(64) DEFAULT NULL COMMENT 'Crontab月份',
  `task_args` text DEFAULT NULL COMMENT 'JSON格式的参数',
  `task_kwargs` text DEFAULT NULL COMMENT 'JSON格式的关键字参数',
  `task_enabled` tinyint(1) DEFAULT 1 COMMENT '是否启用',
  `task_last_run_time` datetime DEFAULT NULL COMMENT '上次运行时间',
  `task_run_count` int(11) DEFAULT 0 COMMENT '总运行次数',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(100) DEFAULT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `task_description` text DEFAULT NULL COMMENT '任务描述',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_name` (`task_name`),
  KEY `idx_task_enabled` (`task_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务配置表'; 