-- MySQL dump 10.13  Distrib 5.7.44, for linux-glibc2.12 (x86_64)
--
-- Host: 127.0.0.1    Database: omind_prd
-- ------------------------------------------------------
-- Server version	5.7.44-log

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Position to start replication or point-in-time recovery from
--

-- CHANGE MASTER TO MASTER_LOG_FILE='mysql-bin.000026', MASTER_LOG_POS=484545444;

--
-- Table structure for table `agent_configs`
--

DROP TABLE IF EXISTS `agent_configs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent_configs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
  `agent_id` varchar(100) NOT NULL COMMENT '智能体唯一标识符',
  `agent_name` varchar(200) NOT NULL COMMENT '智能体显示名称',
  `agent_type` varchar(32) NOT NULL DEFAULT '办公' COMMENT '智能体分类',
  `agent_description` text COMMENT '智能体功能描述',
  `agent_icon` varchar(50) DEFAULT 'Bot' COMMENT '智能体图标',
  `agent_capabilities` json DEFAULT NULL COMMENT '智能体能力列表，JSON数组格式',
  `agent_version` varchar(20) NOT NULL DEFAULT '1.0.0' COMMENT '智能体版本号',
  `agent_status` varchar(20) NOT NULL DEFAULT 'stopped' COMMENT '运行状态（running/stopped/error）',
  `agent_enabled` varchar(10) NOT NULL DEFAULT 'yes' COMMENT '是否启用（yes/no）',
  `is_builtin` varchar(10) NOT NULL DEFAULT 'no' COMMENT '是否为内置智能体（yes/no）',
  `tools_info` json DEFAULT NULL COMMENT '工具配置信息，包含系统工具和MCP工具',
  `llm_info` json DEFAULT NULL COMMENT '大语言模型配置信息',
  `prompt_info` json DEFAULT NULL COMMENT '提示词配置信息',
  `total_runs` int(11) NOT NULL DEFAULT '0' COMMENT '总运行次数统计',
  `success_rate` float NOT NULL DEFAULT '0' COMMENT '成功率（0.0-1.0）',
  `avg_response_time` float NOT NULL DEFAULT '0' COMMENT '平均响应时间（毫秒）',
  `last_used` datetime DEFAULT NULL COMMENT '最后使用时间',
  `config_version` varchar(20) NOT NULL DEFAULT '1.0' COMMENT '配置版本号',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否处于活跃状态',
  `agent_owner` varchar(100) NOT NULL DEFAULT 'system' COMMENT '智能体所有者用户名',
  `visibility_type` varchar(100) NOT NULL DEFAULT 'public' COMMENT '可见权限级别:private,team,department,public',
  `visibility_additional_users` text COMMENT '指定某些人可以看',
  `favorite_users` text COMMENT '主动收藏该智能体的人员列表',
  `create_by` varchar(100) NOT NULL DEFAULT 'system' COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_id` (`agent_id`),
  KEY `idx_agent_owner` (`agent_owner`),
  KEY `idx_visibility_type` (`visibility_type`),
  KEY `idx_create_by` (`create_by`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8mb4 COMMENT='智能体配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_document_session`
--

DROP TABLE IF EXISTS `agent_document_session`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent_document_session` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
  `thread_id` varchar(36) NOT NULL COMMENT '会话线程ID',
  `file_id` varchar(36) NOT NULL COMMENT '文件ID',
  `agent_id` varchar(36) NOT NULL COMMENT '智能体ID',
  `create_by` varchar(100) NOT NULL DEFAULT 'system' COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_session_thread_file` (`thread_id`,`file_id`),
  KEY `idx_session_thread` (`thread_id`),
  KEY `idx_session_file` (`file_id`),
  KEY `idx_session_agent` (`agent_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='智能体会话文档关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_document_upload`
--

DROP TABLE IF EXISTS `agent_document_upload`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent_document_upload` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
  `file_id` varchar(36) NOT NULL COMMENT '文件唯一标识符',
  `file_name` varchar(255) NOT NULL COMMENT '原始文件名',
  `file_size` bigint(20) NOT NULL COMMENT '文件大小(字节)',
  `file_type` varchar(10) NOT NULL COMMENT '文件扩展名',
  `file_path` varchar(500) NOT NULL COMMENT '文件存储路径',
  `process_status` tinyint(4) NOT NULL DEFAULT '0' COMMENT '处理状态:0->uploaded,1->processing,2->ready,3->failed',
  `error_message` text COMMENT '错误信息',
  `doc_content` mediumtext COMMENT '提取的文档内容',
  `doc_chunks` mediumtext COMMENT '文档分块内容',
  `doc_metadata` text COMMENT '文档元数据(字符数、分块数等)',
  `upload_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
  `process_start_time` datetime DEFAULT NULL COMMENT '处理开始时间',
  `process_end_time` datetime DEFAULT NULL COMMENT '处理结束时间',
  `create_by` varchar(100) NOT NULL DEFAULT '' COMMENT '创建人用户名',
  `update_by` varchar(100) NOT NULL DEFAULT '' COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_file_id` (`file_id`),
  KEY `idx_doc_file_id` (`file_id`),
  KEY `idx_doc_create_by` (`create_by`),
  KEY `idx_doc_status` (`process_status`),
  KEY `idx_doc_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能体文档上传表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `agent_permission`
--

DROP TABLE IF EXISTS `agent_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `agent_permission` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
  `agent_id` varchar(100) NOT NULL COMMENT '智能体id',
  `agent_key` varchar(64) DEFAULT NULL COMMENT '分配的密钥',
  `user_name` varchar(64) DEFAULT NULL COMMENT '分配的用户名',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否处于活跃状态',
  `mark_comment` varchar(100) NOT NULL DEFAULT '' COMMENT '工单号',
  `create_by` varchar(100) NOT NULL DEFAULT 'system' COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_key` (`agent_key`),
  UNIQUE KEY `agent_id_user` (`agent_id`,`user_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `ai_model_configs`
--

DROP TABLE IF EXISTS `ai_model_configs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `ai_model_configs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
  `model_id` varchar(100) NOT NULL COMMENT '模型唯一标识符',
  `model_name` varchar(200) NOT NULL COMMENT '模型显示名称',
  `model_provider` varchar(50) NOT NULL COMMENT '模型提供商（openai、deepseek、ollama等）',
  `model_type` varchar(100) NOT NULL COMMENT '模型类型标识',
  `endpoint_url` varchar(500) NOT NULL COMMENT '模型API端点URL',
  `api_key_value` text COMMENT 'API密钥值',
  `model_description` text COMMENT '模型功能描述',
  `model_status` varchar(20) NOT NULL DEFAULT 'inactive' COMMENT '模型状态（active/inactive/error）',
  `config_data` text COMMENT '模型配置数据，JSON格式存储参数设置',
  `create_by` varchar(100) NOT NULL COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `model_id` (`model_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI模型配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_api_keys`
--

DROP TABLE IF EXISTS `auth_api_keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_api_keys` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(64) NOT NULL COMMENT '所属用户ID',
  `key_name` varchar(100) NOT NULL COMMENT '密钥名称',
  `key_prefix` varchar(20) NOT NULL COMMENT '密钥前缀（用于识别）',
  `key_hash` varchar(255) NOT NULL COMMENT '密钥哈希',
  `scopes` text COMMENT '权限范围（JSON数组）',
  `allowed_ips` text COMMENT '允许的IP列表（JSON数组）',
  `issued_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '签发时间',
  `expires_at` datetime DEFAULT NULL COMMENT '过期时间（null表示永不过期）',
  `last_used_at` datetime DEFAULT NULL COMMENT '最后使用时间',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否激活',
  `revoked_at` datetime DEFAULT NULL COMMENT '撤销时间',
  `revoke_reason` varchar(255) DEFAULT NULL COMMENT '撤销原因',
  `mark_comment` varchar(64) NOT NULL DEFAULT '' COMMENT '工单号',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `create_by` varchar(50) NOT NULL COMMENT '创建人',
  `update_by` varchar(50) NOT NULL DEFAULT '' COMMENT '更新人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_key_hash` (`key_hash`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_auth_api_keys_prefix` (`key_prefix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API密钥表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_login_history`
--

DROP TABLE IF EXISTS `auth_login_history`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_login_history` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(64) DEFAULT NULL COMMENT '用户ID（失败时可能为空）',
  `username` varchar(100) DEFAULT NULL COMMENT '尝试登录的用户名',
  `login_type` varchar(20) NOT NULL COMMENT '登录类型：jwt/sso/register',
  `login_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '登录时间',
  `success` tinyint(1) NOT NULL COMMENT '是否成功',
  `failure_reason` varchar(255) DEFAULT NULL COMMENT '失败原因',
  `ip_address` varchar(45) DEFAULT NULL COMMENT 'IP地址',
  `user_agent` text COMMENT 'User-Agent',
  `device_fingerprint` varchar(255) DEFAULT NULL COMMENT '设备指纹',
  `sso_provider` varchar(50) DEFAULT NULL COMMENT 'SSO提供商',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_login_time` (`login_time`),
  KEY `idx_success` (`success`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='登录历史记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_sessions`
--

DROP TABLE IF EXISTS `auth_sessions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_sessions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `session_id` varchar(255) NOT NULL COMMENT '会话ID',
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `sso_provider` varchar(50) NOT NULL COMMENT 'SSO提供商(cas/oauth2等)',
  `sso_session_id` varchar(255) DEFAULT NULL COMMENT 'SSO提供商的会话ID(如CAS ticket)',
  `created_at` datetime NOT NULL COMMENT '创建时间',
  `expires_at` datetime NOT NULL COMMENT '过期时间',
  `last_accessed_at` datetime NOT NULL COMMENT '最后访问时间',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否活跃',
  `terminated_at` datetime DEFAULT NULL COMMENT '终止时间',
  `termination_reason` varchar(255) DEFAULT NULL COMMENT '终止原因',
  `ip_address` varchar(45) DEFAULT NULL COMMENT 'IP地址',
  `user_agent` text COMMENT 'User-Agent',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_session_id` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_sso_provider` (`sso_provider`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SSO会话管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `auth_tokens`
--

DROP TABLE IF EXISTS `auth_tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_tokens` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(64) NOT NULL COMMENT '用户ID',
  `token_jti` varchar(255) NOT NULL COMMENT 'JWT的jti标识',
  `token_type` varchar(20) NOT NULL COMMENT '令牌类型：access/refresh',
  `issued_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '签发时间',
  `expires_at` datetime NOT NULL COMMENT '过期时间',
  `last_used_at` datetime DEFAULT NULL COMMENT '最后使用时间',
  `revoked` tinyint(1) DEFAULT '0' COMMENT '是否已撤销',
  `revoked_at` datetime DEFAULT NULL COMMENT '撤销时间',
  `revoke_reason` varchar(255) DEFAULT NULL COMMENT '撤销原因',
  `device_id` varchar(255) DEFAULT NULL COMMENT '设备标识',
  `device_name` varchar(255) DEFAULT NULL COMMENT '设备名称',
  `ip_address` varchar(45) DEFAULT NULL COMMENT 'IP地址',
  `user_agent` text COMMENT 'User-Agent',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_token_jti` (`token_jti`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_revoked` (`revoked`),
  KEY `idx_auth_tokens_user_device` (`user_id`,`device_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='JWT令牌管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_periodic_task_configs`
--

DROP TABLE IF EXISTS `celery_periodic_task_configs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_periodic_task_configs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_name` varchar(255) NOT NULL COMMENT '任务名称',
  `task_path` varchar(255) NOT NULL COMMENT '任务路径',
  `task_interval` int(11) DEFAULT NULL COMMENT '间隔秒数',
  `task_crontab_minute` varchar(64) DEFAULT NULL COMMENT 'Crontab分钟',
  `task_crontab_hour` varchar(64) DEFAULT NULL COMMENT 'Crontab小时',
  `task_crontab_day_of_week` varchar(64) DEFAULT NULL COMMENT 'Crontab星期',
  `task_crontab_day_of_month` varchar(64) DEFAULT NULL COMMENT 'Crontab日期',
  `task_crontab_month_of_year` varchar(64) DEFAULT NULL COMMENT 'Crontab月份',
  `task_args` text COMMENT 'JSON格式的参数',
  `task_kwargs` text COMMENT 'JSON格式的关键字参数',
  `task_enabled` tinyint(1) DEFAULT '1' COMMENT '是否启用',
  `task_last_run_time` datetime DEFAULT NULL COMMENT '上次运行时间',
  `task_run_count` int(11) DEFAULT '0' COMMENT '总运行次数',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(100) DEFAULT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `task_description` text COMMENT '任务描述',
  `task_extra_config` text,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_name` (`task_name`),
  KEY `idx_task_enabled` (`task_enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_periodic_task_execution_logs`
--

DROP TABLE IF EXISTS `celery_periodic_task_execution_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_periodic_task_execution_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `task_name` varchar(255) NOT NULL COMMENT '任务名称',
  `task_schedule_time` datetime NOT NULL COMMENT '计划执行时间',
  `task_execute_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '实际执行时间',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(100) DEFAULT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `task_status` varchar(50) DEFAULT 'SUCCESS' COMMENT '执行状态',
  `task_result` text COMMENT '执行结果',
  PRIMARY KEY (`id`),
  KEY `idx_task_name` (`task_name`),
  KEY `idx_task_schedule_time` (`task_schedule_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='定时任务执行记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_task_records`
--

DROP TABLE IF EXISTS `celery_task_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_task_records` (
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
  `task_result` text COMMENT '任务结果',
  `task_traceback` text COMMENT '错误追踪信息',
  `task_retry_count` int(11) DEFAULT '0' COMMENT '重试次数',
  `task_args` text COMMENT '任务参数',
  `task_kwargs` text COMMENT '任务关键字参数',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `idx_task_status` (`task_status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='异步任务记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_taskmeta`
--

DROP TABLE IF EXISTS `celery_taskmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_taskmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `task_id` varchar(155) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `result` blob,
  `date_done` datetime DEFAULT NULL,
  `traceback` text,
  `name` varchar(155) DEFAULT NULL,
  `args` blob,
  `kwargs` blob,
  `worker` varchar(155) DEFAULT NULL,
  `retries` int(11) DEFAULT NULL,
  `queue` varchar(155) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `celery_tasksetmeta`
--

DROP TABLE IF EXISTS `celery_tasksetmeta`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `celery_tasksetmeta` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `taskset_id` varchar(155) DEFAULT NULL,
  `result` blob,
  `date_done` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `taskset_id` (`taskset_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kb_categories`
--

DROP TABLE IF EXISTS `kb_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kb_categories` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `kb_id` varchar(36) NOT NULL COMMENT '知识库ID',
  `category_name` varchar(100) NOT NULL COMMENT '分类名称',
  `parent_id` bigint(20) DEFAULT NULL COMMENT '父分类ID',
  `sort_order` int(11) DEFAULT '0' COMMENT '排序权重',
  `category_description` text COMMENT '分类描述',
  `create_by` varchar(100) NOT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_kb_category` (`kb_id`,`parent_id`),
  KEY `idx_sort_order` (`kb_id`,`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='知识库分类表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kb_document_folders`
--

DROP TABLE IF EXISTS `kb_document_folders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kb_document_folders` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `kb_id` varchar(36) NOT NULL COMMENT '知识库ID',
  `file_id` varchar(36) NOT NULL COMMENT '文件ID',
  `folder_id` varchar(36) DEFAULT NULL COMMENT '目录ID，NULL表示根目录',
  `display_name` varchar(255) DEFAULT NULL COMMENT '在此目录中的显示名',
  `sort_order` int(11) DEFAULT '0' COMMENT '排序权重',
  `is_pinned` tinyint(1) DEFAULT '0' COMMENT '是否置顶',
  `create_by` varchar(100) NOT NULL COMMENT '操作人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_kb_file_folder` (`kb_id`,`file_id`,`folder_id`),
  KEY `idx_folder_sort` (`folder_id`,`sort_order`),
  KEY `idx_kb_folder` (`kb_id`,`folder_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='文档目录关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kb_documents`
--

DROP TABLE IF EXISTS `kb_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kb_documents` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `kb_id` varchar(36) NOT NULL COMMENT '知识库ID',
  `file_id` varchar(36) NOT NULL COMMENT '文件ID',
  `doc_title` varchar(500) DEFAULT NULL COMMENT '文档标题(可重命名)',
  `doc_category` varchar(100) DEFAULT NULL COMMENT '文档分类',
  `doc_priority` int(11) DEFAULT '0' COMMENT '权重',
  `doc_status` tinyint(4) DEFAULT '1' COMMENT '在此知识库中的状态: 1-正常, 0-禁用',
  `create_by` varchar(100) NOT NULL COMMENT '添加人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_kb_file` (`kb_id`,`file_id`),
  KEY `idx_kb_status` (`kb_id`,`doc_status`),
  KEY `idx_category` (`kb_id`,`doc_category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='知识库文档关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kb_folders`
--

DROP TABLE IF EXISTS `kb_folders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kb_folders` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `folder_id` varchar(36) NOT NULL COMMENT '目录唯一标识',
  `kb_id` varchar(36) NOT NULL COMMENT '所属知识库ID',
  `parent_folder_id` varchar(36) DEFAULT NULL COMMENT '父目录ID，NULL表示根目录',
  `folder_name` varchar(255) NOT NULL COMMENT '目录名称',
  `folder_description` text COMMENT '目录描述',
  `folder_type` varchar(50) DEFAULT 'folder' COMMENT '目录类型',
  `sort_order` int(11) DEFAULT '0' COMMENT '排序权重',
  `inherit_permissions` tinyint(1) DEFAULT '1' COMMENT '是否继承权限',
  `custom_permissions` text COMMENT '自定义权限(JSON格式)',
  `create_by` varchar(100) NOT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `folder_id` (`folder_id`),
  KEY `idx_kb_id` (`kb_id`),
  KEY `idx_parent_folder` (`parent_folder_id`),
  KEY `idx_sort_order` (`kb_id`,`parent_folder_id`,`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='知识库目录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `kb_permissions`
--

DROP TABLE IF EXISTS `kb_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `kb_permissions` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `kb_id` varchar(36) NOT NULL COMMENT '知识库ID',
  `user_id` varchar(100) NOT NULL COMMENT '用户ID',
  `permission_type` varchar(20) NOT NULL COMMENT '权限类型: read, write, admin',
  `granted_by` varchar(100) DEFAULT NULL COMMENT '授权人',
  `granted_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
  `expire_time` datetime DEFAULT NULL COMMENT '过期时间，NULL表示永不过期',
  `create_by` varchar(100) NOT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_kb_user` (`kb_id`,`user_id`),
  KEY `idx_user_permission` (`user_id`,`permission_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='知识库权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `knowledge_bases`
--

DROP TABLE IF EXISTS `knowledge_bases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `knowledge_bases` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `kb_id` varchar(36) NOT NULL COMMENT '知识库唯一标识',
  `kb_name` varchar(255) NOT NULL COMMENT '知识库名称',
  `kb_description` text COMMENT '知识库描述',
  `kb_type` varchar(50) DEFAULT 'general' COMMENT '知识库类型: general, technical, faq, training',
  `kb_status` tinyint(4) DEFAULT '1' COMMENT '状态: 1-启用, 0-禁用',
  `visibility` varchar(20) DEFAULT 'private' COMMENT '可见性: private, internal, public',
  `owner_id` varchar(100) NOT NULL COMMENT '所有者用户名',
  `department` varchar(100) DEFAULT NULL COMMENT '部门',
  `tags` text COMMENT '标签(JSON格式)',
  `settings` text COMMENT '设置(JSON格式，搜索配置、权限设置等)',
  `doc_count` int(11) DEFAULT '0' COMMENT '文档数量',
  `total_chunks` int(11) DEFAULT '0' COMMENT '总分块数',
  `create_by` varchar(100) NOT NULL COMMENT '创建人',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `kb_id` (`kb_id`),
  KEY `idx_owner` (`owner_id`),
  KEY `idx_status` (`kb_status`),
  KEY `idx_type` (`kb_type`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COMMENT='知识库表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mcp_configs`
--

DROP TABLE IF EXISTS `mcp_configs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mcp_configs` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `config_id` varchar(100) NOT NULL COMMENT '配置id',
  `name` varchar(50) NOT NULL COMMENT '配置名称',
  `tenant` varchar(50) NOT NULL COMMENT '租户名称',
  `routers` text COMMENT '路由配置',
  `servers` text COMMENT 'server配置',
  `tools` text COMMENT '工具配置',
  `prompts` text COMMENT '提示词配置',
  `mcp_servers` text COMMENT 'mcpserver配置',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
  `create_by` varchar(100) NOT NULL COMMENT '创建者',
  `update_by` varchar(100) DEFAULT NULL COMMENT '更新者',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_config_id` (`config_id`),
  UNIQUE KEY `uniq_tenant_name` (`tenant`,`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MCP配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `mcp_servers`
--

DROP TABLE IF EXISTS `mcp_servers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `mcp_servers` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
  `server_id` varchar(100) NOT NULL COMMENT 'MCP服务器唯一标识符',
  `server_name` varchar(200) NOT NULL COMMENT 'MCP服务器显示名称',
  `server_uri` varchar(500) NOT NULL COMMENT 'MCP服务器连接URI',
  `transport_type` varchar(50) NOT NULL DEFAULT 'streamable-http' COMMENT 'transport类型',
  `server_description` text COMMENT 'MCP服务器功能描述',
  `is_enabled` varchar(10) NOT NULL DEFAULT 'on' COMMENT '是否启用（on/off）',
  `connection_status` varchar(20) NOT NULL DEFAULT 'disconnected' COMMENT '连接状态（connected/disconnected/error）',
  `auth_type` varchar(20) DEFAULT '' COMMENT '认证类型（bearer、api_key等）',
  `auth_token` text COMMENT '认证令牌或密钥',
  `api_key_header` varchar(100) DEFAULT NULL COMMENT 'API密钥请求头名称',
  `read_timeout_seconds` int(11) NOT NULL DEFAULT '5' COMMENT '读取超时时间（秒）',
  `server_tools` text COMMENT '服务器提供的工具列表，JSON格式',
  `server_config` text COMMENT '服务器配置信息，JSON格式',
  `team_name` varchar(100) NOT NULL COMMENT '负责团队名称',
  `create_by` varchar(100) NOT NULL COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `server_id` (`server_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MCP服务器配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rbac_menus`
--

DROP TABLE IF EXISTS `rbac_menus`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rbac_menus` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `menu_id` int(11) NOT NULL DEFAULT '-1' COMMENT '菜单id',
  `menu_name` varchar(50) NOT NULL DEFAULT '' COMMENT '菜单名称',
  `menu_icon` varchar(50) NOT NULL DEFAULT '' COMMENT '图标',
  `parent_id` int(11) NOT NULL DEFAULT '-1' COMMENT '父级菜单id',
  `route_path` varchar(200) NOT NULL DEFAULT '' COMMENT '前端路由路径',
  `redirect_path` varchar(200) NOT NULL DEFAULT '' COMMENT '重定向路径',
  `menu_component` varchar(100) NOT NULL DEFAULT '' COMMENT '组件名称',
  `show_menu` tinyint(1) NOT NULL DEFAULT '0' COMMENT '是否展示,0展示,1隐藏',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(50) NOT NULL DEFAULT '' COMMENT '创建人',
  `update_by` varchar(50) NOT NULL DEFAULT '' COMMENT '更新人',
  `sort_order` int(11) DEFAULT '0',
  PRIMARY KEY (`id`),
  UNIQUE KEY `menu_id` (`menu_id`)
) ENGINE=InnoDB AUTO_INCREMENT=49 DEFAULT CHARSET=utf8 COMMENT='菜单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rbac_permissions`
--

DROP TABLE IF EXISTS `rbac_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rbac_permissions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `permission_id` int(11) NOT NULL DEFAULT '-1' COMMENT '权限id',
  `permission_description` varchar(200) NOT NULL DEFAULT '' COMMENT '权限描述',
  `permission_name` varchar(100) NOT NULL DEFAULT '' COMMENT '权限名称',
  `http_method` varchar(10) DEFAULT '*' COMMENT 'HTTP方法: GET,POST,PUT,DELETE,*',
  `release_disable` varchar(10) NOT NULL DEFAULT 'off' COMMENT '发版时是否禁用API接口',
  `permission_allow_client` text COMMENT '允许访问对应地址的客户端白名单',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(50) NOT NULL DEFAULT '' COMMENT '创建人',
  `update_by` varchar(50) NOT NULL DEFAULT '' COMMENT '更新人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `permission_id` (`permission_id`),
  UNIQUE KEY `uniq_name_method` (`permission_name`,`http_method`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=964 DEFAULT CHARSET=utf8 COMMENT='api权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rbac_roles`
--

DROP TABLE IF EXISTS `rbac_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rbac_roles` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `role_id` int(11) NOT NULL DEFAULT '-1' COMMENT '角色id',
  `role_name` varchar(50) NOT NULL DEFAULT '' COMMENT '角色名称',
  `description` varchar(200) NOT NULL DEFAULT '' COMMENT '角色描述',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(50) NOT NULL DEFAULT '' COMMENT '创建人',
  `update_by` varchar(50) NOT NULL DEFAULT '' COMMENT '更新人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `role_id` (`role_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8 COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rbac_roles_permissions`
--

DROP TABLE IF EXISTS `rbac_roles_permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rbac_roles_permissions` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `role_id` int(11) NOT NULL DEFAULT '-1' COMMENT '角色id',
  `back_permission_id` int(11) NOT NULL DEFAULT '-1' COMMENT '后端权限id',
  `front_permission_id` int(11) NOT NULL DEFAULT '-1' COMMENT '前端权限id',
  `permission_type` int(11) NOT NULL DEFAULT '-1' COMMENT '权限类型1->api接口权限,2前端菜单权限',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(50) NOT NULL DEFAULT '' COMMENT '创建人',
  `update_by` varchar(50) NOT NULL DEFAULT '' COMMENT '更新人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `role_back_front_id` (`role_id`,`back_permission_id`,`front_permission_id`)
) ENGINE=InnoDB AUTO_INCREMENT=3556 DEFAULT CHARSET=utf8 COMMENT='角色-权限关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rbac_users`
--

DROP TABLE IF EXISTS `rbac_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rbac_users` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `user_id` varchar(64) NOT NULL DEFAULT '' COMMENT '用户id',
  `user_name` varchar(50) NOT NULL DEFAULT '' COMMENT '用户名',
  `display_name` varchar(50) NOT NULL DEFAULT '' COMMENT '别名',
  `department_name` varchar(50) NOT NULL DEFAULT '' COMMENT '部门名称',
  `group_name` varchar(50) NOT NULL DEFAULT '' COMMENT '小组名称',
  `email` varchar(100) NOT NULL DEFAULT '' COMMENT '邮箱',
  `mobile` varchar(20) NOT NULL DEFAULT '' COMMENT '手机号',
  `user_source` tinyint(1) NOT NULL DEFAULT '3' COMMENT '用户来源,1-->sso,2-->local',
  `locked_until` datetime DEFAULT NULL COMMENT '账户锁定到期时间',
  `login_attempts` int(11) DEFAULT '0' COMMENT '登录失败次数',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  `mfa_enabled` tinyint(1) DEFAULT '0' COMMENT '是否启用MFA',
  `mfa_secret` varchar(255) DEFAULT NULL COMMENT 'MFA密钥',
  `password_hash` varchar(255) DEFAULT NULL COMMENT '密码哈希（本地认证用）',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '用户是否活跃,1活跃,0冻结',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(50) NOT NULL DEFAULT '' COMMENT '创建人',
  `update_by` varchar(50) NOT NULL DEFAULT '' COMMENT '更新人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `user_name` (`user_name`)
) ENGINE=InnoDB AUTO_INCREMENT=33 DEFAULT CHARSET=utf8 COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `rbac_users_roles`
--

DROP TABLE IF EXISTS `rbac_users_roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `rbac_users_roles` (
  `id` bigint(20) unsigned NOT NULL AUTO_INCREMENT COMMENT '主键id',
  `user_id` varchar(64) NOT NULL DEFAULT '' COMMENT '用户id',
  `role_id` int(11) NOT NULL DEFAULT '-1' COMMENT '角色id',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(50) NOT NULL DEFAULT '' COMMENT '创建人',
  `update_by` varchar(50) NOT NULL DEFAULT '' COMMENT '更新人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`,`role_id`)
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8 COMMENT='用户-角色关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sop_problem_rule`
--

DROP TABLE IF EXISTS `sop_problem_rule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sop_problem_rule` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `rule_name` varchar(200) NOT NULL COMMENT '映射规则名称',
  `sop_id` varchar(100) NOT NULL COMMENT '关联的SOP ID',
  `rules_info` text NOT NULL COMMENT '匹配规则JSON',
  `is_enabled` tinyint(1) NOT NULL DEFAULT '1' COMMENT '是否启用',
  `created_by` varchar(100) NOT NULL COMMENT '创建人',
  `updated_by` varchar(100) DEFAULT NULL COMMENT '更新人',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_rule_name` (`rule_name`),
  KEY `idx_sop_id` (`sop_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SOP问题映射表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `sop_prompt_templates`
--

DROP TABLE IF EXISTS `sop_prompt_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `sop_prompt_templates` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '主键ID，自增',
  `sop_id` varchar(100) NOT NULL COMMENT 'SOP唯一标识符，如SOP-DB-001',
  `sop_title` varchar(500) NOT NULL COMMENT 'SOP标题名称',
  `sop_category` varchar(100) NOT NULL COMMENT 'SOP分类（如database、system、network等）',
  `sop_description` text COMMENT 'SOP详细描述',
  `sop_severity` varchar(20) NOT NULL COMMENT 'SOP严重等级（high、medium、low）',
  `sop_steps` json NOT NULL COMMENT 'SOP执行步骤，JSON格式存储步骤列表',
  `tools_required` json DEFAULT NULL COMMENT '所需工具列表，JSON格式存储工具名称数组',
  `sop_recommendations` text COMMENT 'SOP建议和最佳实践',
  `team_name` varchar(100) NOT NULL COMMENT '负责团队名称',
  `create_by` varchar(100) NOT NULL COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `sop_id` (`sop_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SOP标准操作程序模板表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user_threads`
--

DROP TABLE IF EXISTS `user_threads`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `user_threads` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_name` varchar(100) NOT NULL,
  `thread_id` varchar(255) NOT NULL,
  `thread_title` varchar(500) DEFAULT NULL,
  `agent_id` varchar(100) DEFAULT NULL,
  `is_archived` tinyint(1) NOT NULL,
  `message_count` int(11) NOT NULL,
  `last_message_time` datetime DEFAULT NULL,
  `create_at` datetime NOT NULL,
  `update_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_user_threads_id` (`id`),
  KEY `ix_user_threads_user_name` (`user_name`),
  KEY `ix_user_threads_thread_id` (`thread_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-09-01 10:45:06
