-- MySQL dump 10.13  Distrib 5.7.44, for linux-glibc2.12 (x86_64)
--
-- Host: 127.0.0.1    Database: omind
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

-- CHANGE MASTER TO MASTER_LOG_FILE='mysql-bin.000024', MASTER_LOG_POS=366252940;

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
  `create_by` varchar(100) NOT NULL DEFAULT 'system' COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `agent_id` (`agent_id`)
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COMMENT='智能体配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `agent_configs`
--

LOCK TABLES `agent_configs` WRITE;
/*!40000 ALTER TABLE `agent_configs` DISABLE KEYS */;
INSERT INTO `agent_configs` VALUES (24,'diagnostic_agent','故障诊断智能体','故障诊断','专业的系统故障诊断和问题分析智能体，能够快速定位和解决各类技术问题','Brain','[\"数据库诊断\", \"系统监控\", \"日志分析\", \"性能优化\"]','1.0.0','stopped','no','yes','{\"mcp_tools\": [{\"tools\": [\"get_zabbix_metric_data\", \"get_zabbix_metrics\"], \"server_id\": \"zabbix-mcp-server\", \"server_name\": \"Zabbix监控MCP服务器111\"}, {\"tools\": [\"get_es_data\", \"get_es_trends_data\", \"get_es_indices\"], \"server_id\": \"es-mcp-server\", \"server_name\": \"Elasticsearch工具MCP服务器\"}, {\"tools\": [\"execute_mysql_query\"], \"server_id\": \"db-mcp-server\", \"server_name\": \"数据库工具MCP服务器\"}], \"system_tools\": [\"get_sop_content\", \"get_sop_detail\", \"list_sops\", \"search_sops\", \"get_current_time\"]}','{\"top_p\": 1, \"max_tokens\": 2000, \"model_name\": \"deepseek-chat\", \"temperature\": 0.7, \"available_models\": [\"deepseek-chat\"], \"presence_penalty\": 0, \"frequency_penalty\": 0}','{\"system_prompt\": \"你是故障诊断智能体，请根据用户需求提供专业的帮助。\", \"user_prompt_template\": \"\", \"assistant_prompt_template\": \"\"}',0,0,0,NULL,'1.0',1,'system','user','2025-07-23 09:52:45','2025-08-06 21:12:44'),(25,'custom_g04l34h5','审计检查智能体','合规审计','强大的信息研究和数据分析智能体，擅长网络搜索、数据整理和深度分析','Search','[\"专业\", \"洞察\", \"严谨\"]','1.0.0','stopped','yes','no','{\"mcp_tools\": [{\"tools\": [\"get_zabbix_metric_data\", \"get_zabbix_metrics\"], \"server_id\": \"zabbix-mcp-server\", \"server_name\": \"Zabbix监控MCP服务器111\"}], \"system_tools\": [\"get_current_time\"]}','{\"top_p\": 1, \"max_tokens\": 2000, \"model_name\": \"deepseek-chat\", \"temperature\": 0.7, \"available_models\": [\"deepseek-chat\"], \"presence_penalty\": 0, \"frequency_penalty\": 0}','{\"system_prompt\": \"你是审计检查智能体，请根据用户需求提供专业的帮助。\", \"user_prompt_template\": \"\", \"assistant_prompt_template\": \"\"}',0,0,0,NULL,'1.0',1,'system','system','2025-07-23 09:52:51','2025-08-06 21:11:02'),(26,'custom_l44h87l2','安全防护智能体','安全防护',NULL,'Shield','[\"敏锐\", \"安全\", \"高效\"]','1.0.0','stopped','yes','no','{\"mcp_tools\": [], \"system_tools\": [\"get_current_time\"]}','{\"top_p\": 1, \"max_tokens\": 2000, \"model_name\": \"deepseek-chat\", \"temperature\": 0.7, \"available_models\": [\"deepseek-chat\"], \"presence_penalty\": 0, \"frequency_penalty\": 0}','{\"system_prompt\": \"你是安全防护智能体，请根据用户需求提供专业的帮助。\", \"user_prompt_template\": \"\", \"assistant_prompt_template\": \"\"}',0,0,0,NULL,'1.0',1,'system','system','2025-07-23 09:52:52','2025-08-06 21:10:55'),(35,'research_agent','研究分析智能体','资源管理',NULL,'Brain','[\"多维度\"]','1.0.0','stopped','yes','yes','{\"mcp_tools\": [], \"system_tools\": [\"get_current_time\"]}','{\"top_p\": 1, \"max_tokens\": 2000, \"model_name\": \"deepseek-chat\", \"temperature\": 0.7, \"available_models\": [\"deepseek-chat\"], \"presence_penalty\": 0, \"frequency_penalty\": 0}','{\"system_prompt\": \"你是研究分析智能体，请根据用户需求提供专业的帮助。\", \"user_prompt_template\": \"\", \"assistant_prompt_template\": \"\"}',0,0,0,NULL,'1.0',1,'system',NULL,'2025-07-31 00:14:16','2025-08-06 21:10:20'),(36,'security_agent','安全防护智能体','安全防护',NULL,'Bot','[\"聪明\"]','1.0.0','stopped','yes','yes','{\"mcp_tools\": [{\"tools\": [\"get_zabbix_metric_data\", \"get_zabbix_metrics\"], \"server_id\": \"zabbix-mcp-server\", \"server_name\": \"Zabbix监控MCP服务器111\"}, {\"tools\": [\"get_es_data\", \"get_es_trends_data\", \"get_es_indices\"], \"server_id\": \"es-mcp-server\", \"server_name\": \"Elasticsearch工具MCP服务器\"}, {\"tools\": [\"get_system_info\", \"analyze_processes\", \"check_service_status\", \"analyze_system_logs\", \"execute_system_command\"], \"server_id\": \"ssh-mcp-server\", \"server_name\": \"SSH工具MCP服务器\"}, {\"tools\": [\"execute_mysql_query\"], \"server_id\": \"db-mcp-server\", \"server_name\": \"数据库工具MCP服务器\"}], \"system_tools\": [\"get_current_time\", \"get_sop_content\", \"get_sop_detail\", \"list_sops\", \"search_sops\"]}','{\"top_p\": 1, \"max_tokens\": 2000, \"model_name\": \"deepseek-chat\", \"temperature\": 0.7, \"available_models\": [\"deepseek-chat\"], \"presence_penalty\": 0, \"frequency_penalty\": 0}','{\"system_prompt\": \"你是安全防护智能体，请根据用户需求提供专业的帮助。\", \"user_prompt_template\": \"\", \"assistant_prompt_template\": \"\"}',0,0,0,NULL,'1.0',1,'system',NULL,'2025-07-31 00:53:54','2025-08-06 21:10:06'),(37,'custom_00e75667','故事小助手','其他',NULL,'Crown','[\"幽默\", \"灵活\"]','1.0.0','stopped','yes','no','{\"mcp_tools\": [], \"system_tools\": [\"get_current_time\"]}','{\"top_p\": 1, \"max_tokens\": 2000, \"model_name\": \"deepseek-chat\", \"temperature\": 0.7, \"available_models\": [\"deepseek-chat\"], \"presence_penalty\": 0, \"frequency_penalty\": 0}','{\"system_prompt\": \"你是故事小助手，请根据用户需求提供专业的帮助。\", \"user_prompt_template\": \"\", \"assistant_prompt_template\": \"\"}',0,0,0,NULL,'1.0',1,'system',NULL,'2025-08-01 13:03:43','2025-08-06 21:10:47'),(38,'custom_9b45e60b','网络监控智能体','监控告警',NULL,'Bot','[\"安全\"]','1.0.0','stopped','yes','no','{\"mcp_tools\": [{\"tools\": [\"get_zabbix_metric_data\", \"get_zabbix_metrics\"], \"server_id\": \"zabbix-mcp-server\", \"server_name\": \"Zabbix监控MCP服务器111\"}], \"system_tools\": [\"get_current_time\"]}','{\"top_p\": 1, \"max_tokens\": 2000, \"model_name\": \"deepseek-chat\", \"temperature\": 0.7, \"available_models\": [\"deepseek-chat\"], \"presence_penalty\": 0, \"frequency_penalty\": 0}','{\"system_prompt\": \"你是网络监控智能体，请根据用户需求提供专业的帮助。\", \"user_prompt_template\": \"\", \"assistant_prompt_template\": \"\"}',0,0,0,NULL,'1.0',1,'system',NULL,'2025-08-01 13:06:11','2025-08-06 21:10:37'),(39,'custom_ebcae47f','硬盘检查职能体','日志分析',NULL,'Settings','[\"灵活\", \"严谨\"]','1.0.0','stopped','yes','no','{\"mcp_tools\": [{\"tools\": [\"get_zabbix_metric_data\", \"get_zabbix_metrics\"], \"server_id\": \"zabbix-mcp-server\", \"server_name\": \"Zabbix监控MCP服务器111\"}], \"system_tools\": [\"get_current_time\"]}','{\"top_p\": 1, \"max_tokens\": 2000, \"model_name\": \"deepseek-chat\", \"temperature\": 0.7, \"available_models\": [\"deepseek-chat\"], \"presence_penalty\": 0, \"frequency_penalty\": 0}','{\"system_prompt\": \"你是硬盘检查职能体，请根据用户需求提供专业的帮助。\", \"user_prompt_template\": \"\", \"assistant_prompt_template\": \"\"}',0,0,0,NULL,'1.0',1,'system',NULL,'2025-08-01 16:20:58','2025-08-06 21:10:29');
/*!40000 ALTER TABLE `agent_configs` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COMMENT='AI模型配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ai_model_configs`
--

LOCK TABLES `ai_model_configs` WRITE;
/*!40000 ALTER TABLE `ai_model_configs` DISABLE KEYS */;
INSERT INTO `ai_model_configs` VALUES (2,'model-3267aa5a4ded','ollama-qwen3-0.6B','ollama','qwen3:0.6b','http://localhost:11434',NULL,NULL,'active',NULL,'frontend_user','frontend_user','2025-07-24 00:58:42','2025-07-24 00:59:04'),(3,'model-ee8bef7a98d3','deepseek-chat','deepseek','deepseek-chat','https://api.deepseek.com/v1','sk-490738f8ce8f4a36bcc0bfb165270008',NULL,'active',NULL,'frontend_user','frontend_user','2025-07-24 01:04:59','2025-07-24 01:05:53');
/*!40000 ALTER TABLE `ai_model_configs` ENABLE KEYS */;
UNLOCK TABLES;

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
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `create_by` varchar(50) NOT NULL COMMENT '创建人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_key_hash` (`key_hash`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_auth_api_keys_prefix` (`key_prefix`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API密钥表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_api_keys`
--

LOCK TABLES `auth_api_keys` WRITE;
/*!40000 ALTER TABLE `auth_api_keys` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_api_keys` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=140 DEFAULT CHARSET=utf8mb4 COMMENT='登录历史记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_login_history`
--

LOCK TABLES `auth_login_history` WRITE;
/*!40000 ALTER TABLE `auth_login_history` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_login_history` ENABLE KEYS */;
UNLOCK TABLES;

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
  `sso_provider` varchar(50) NOT NULL COMMENT 'SSO提供商',
  `sso_session_id` varchar(255) DEFAULT NULL COMMENT 'SSO提供商的会话ID',
  `sso_access_token` text COMMENT 'SSO访问令牌（加密存储）',
  `sso_refresh_token` text COMMENT 'SSO刷新令牌（加密存储）',
  `sso_id_token` text COMMENT 'SSO ID令牌',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `expires_at` datetime NOT NULL COMMENT '过期时间',
  `last_accessed_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后访问时间',
  `is_active` tinyint(1) DEFAULT '1' COMMENT '是否活跃',
  `terminated_at` datetime DEFAULT NULL COMMENT '终止时间',
  `termination_reason` varchar(255) DEFAULT NULL COMMENT '终止原因',
  `ip_address` varchar(45) DEFAULT NULL COMMENT 'IP地址',
  `user_agent` text COMMENT 'User-Agent',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_session_id` (`session_id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_sso_provider` (`sso_provider`),
  KEY `idx_expires_at` (`expires_at`),
  KEY `idx_auth_sessions_active` (`is_active`,`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SSO会话管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_sessions`
--

LOCK TABLES `auth_sessions` WRITE;
/*!40000 ALTER TABLE `auth_sessions` DISABLE KEYS */;
/*!40000 ALTER TABLE `auth_sessions` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=257 DEFAULT CHARSET=utf8mb4 COMMENT='JWT令牌管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_tokens`
--

LOCK TABLES `auth_tokens` WRITE;
/*!40000 ALTER TABLE `auth_tokens` DISABLE KEYS */;
INSERT INTO `auth_tokens` VALUES (1,'user_1754284542','1kfQW23hczaBXnVScKb1rw','access','2025-08-04 13:17:02','2025-08-04 05:47:02',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 13:17:02'),(2,'user_1754284542','DZ13Qt4tbOmZL6Xip_UWvQ','refresh','2025-08-04 13:17:02','2025-08-11 05:17:02',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 13:17:02'),(3,'user_1754284542','k0Zmf4li7inrK3m65qPrXw','access','2025-08-04 13:31:34','2025-08-04 06:01:34',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 13:31:34'),(4,'user_1754284542','Ux8On7jJFBJCq5_IkNZEGA','refresh','2025-08-04 13:31:34','2025-08-11 05:31:34',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 13:31:34'),(5,'user_1754283990','aKEXpt43_mwBMYnf_5HR8g','access','2025-08-04 13:32:31','2025-08-04 06:02:31',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 13:32:31'),(6,'user_1754283990','0OE0lorn7lyvy74jScyBUQ','refresh','2025-08-04 13:32:31','2025-08-11 05:32:31',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 13:32:31'),(7,'user_1754283990','5KyoPmPoiZjt2bGWceTLPA','access','2025-08-04 13:32:52','2025-08-04 06:02:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 13:32:52'),(8,'user_1754283990','VUsxQRjDHIkVyvq5QPBlmg','refresh','2025-08-04 13:32:53','2025-08-11 05:32:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 13:32:53'),(9,'user_1754284542','BjiiHbdtb_KrpVkmS7sDQg','access','2025-08-04 14:06:24','2025-08-04 06:36:24',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:06:24'),(10,'user_1754284542','SkJqppYUUBF7H3z5im5D7w','refresh','2025-08-04 14:06:24','2025-08-11 06:06:24',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:06:24'),(11,'user_1754284542','Iv7wsxPMURAZiDM6CC6lDQ','access','2025-08-04 14:08:03','2025-08-04 06:38:03',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:08:03'),(12,'user_1754284542','3UMHtwrzv_y2_fslpoQbSQ','refresh','2025-08-04 14:08:03','2025-08-11 06:08:03',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:08:03'),(13,'user_1754283990','S2LBlTGlwK_OKxg1PA3B_Q','access','2025-08-04 14:10:23','2025-08-04 06:40:23',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:10:23'),(14,'user_1754283990','WXPBc43-FKIJQDxCU1Ke4Q','refresh','2025-08-04 14:10:23','2025-08-11 06:10:23',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:10:23'),(15,'user_1754283990','_2RxKNe60CQEHbrmIEm3Dg','access','2025-08-04 14:38:58','2025-08-04 07:08:58',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:38:58'),(16,'user_1754283990','2qrTfxSOZL2SyEZrU1s7mQ','refresh','2025-08-04 14:38:58','2025-08-11 06:38:58',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:38:58'),(17,'user_1754283990','WCy_N9Dfgk6Wx2MTLjDeqA','access','2025-08-04 14:41:59','2025-08-04 07:11:59',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:41:59'),(18,'user_1754283990','W3U-eQvuUxqxcansnOq3Kw','refresh','2025-08-04 14:41:59','2025-08-11 06:41:59',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:41:59'),(19,'user_1754283990','U0mCSs9xhhvPIhX-ioHTYQ','access','2025-08-04 14:44:39','2025-08-04 07:14:39',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:44:39'),(20,'user_1754283990','pfej4dF3Cmtd32cN5BUoVg','refresh','2025-08-04 14:44:39','2025-08-11 06:44:39',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 14:44:39'),(21,'user_1754283990','2dnNKYIx7GNKHMj5JtYjuA','access','2025-08-04 18:15:39','2025-08-04 10:45:39',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 18:15:39'),(22,'user_1754283990','Q_fAhXmIyxynijBYMpDt9Q','refresh','2025-08-04 18:15:39','2025-08-11 10:15:39',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 18:15:39'),(23,'user_1754283990','8iI--nk1phkFNAkOKZ4vnA','access','2025-08-04 20:40:20','2025-08-04 13:10:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 20:40:20'),(24,'user_1754283990','aUJbQ6UEhh38nSKptsh09A','refresh','2025-08-04 20:40:20','2025-08-11 12:40:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-04 20:40:20'),(25,'user_1754397315','-y6CmkEHhtFVA4kfb_nqZg','access','2025-08-05 20:35:24','2025-08-05 13:05:24',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 20:35:24'),(26,'user_1754397315','RlpYuEoTEUHjyq9J_GSvhA','refresh','2025-08-05 20:35:24','2025-08-12 12:35:24',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 20:35:24'),(27,'user_1754397315','UUicwwg_6JpsdQWZd1Sedw','access','2025-08-05 21:11:40','2025-08-05 13:41:40',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:11:40'),(28,'user_1754397315','1bvbnmVSeJjWqAbAjkHabw','refresh','2025-08-05 21:11:40','2025-08-12 13:11:40',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:11:40'),(29,'user_1754397315','LzkfHqZDxrLurSlYkV80Xg','access','2025-08-05 21:12:24','2025-08-05 13:42:24',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:12:24'),(30,'user_1754397315','0pVYMoTH6i8LDmgMd9D8bw','refresh','2025-08-05 21:12:24','2025-08-12 13:12:24',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:12:24'),(31,'user_1754397315','swG-ljJgUrfKlMmoHEa8og','access','2025-08-05 21:48:18','2025-08-05 14:18:17',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:48:18'),(32,'user_1754397315','ObOi4BnfSopMyby1c64HxA','refresh','2025-08-05 21:48:18','2025-08-12 13:48:17',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:48:18'),(33,'user_1754397315','9ywDKB_ACdDWYLCNm97KkQ','access','2025-08-05 21:49:06','2025-08-05 14:19:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:49:06'),(34,'user_1754397315','2bXMfV6zkU_1VFOGNc7T5A','refresh','2025-08-05 21:49:06','2025-08-12 13:49:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:49:06'),(35,'user_1754397315','aG1MrZslBGJd6IErMdqxQw','access','2025-08-05 21:49:38','2025-08-05 14:19:38',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:49:38'),(36,'user_1754397315','DwcXximJRNILjWTeQbACFg','refresh','2025-08-05 21:49:38','2025-08-12 13:49:38',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:49:38'),(37,'user_1754397315','HJz9LDQdj2SfzSvzmBu2XA','access','2025-08-05 21:51:37','2025-08-05 14:21:37',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:51:37'),(38,'user_1754397315','4SNpzurQcz3oScrlN9eA1Q','refresh','2025-08-05 21:51:37','2025-08-12 13:51:37',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:51:37'),(39,'user_1754397315','9p0t3bJi0PyZwM3sJMwpdQ','access','2025-08-05 21:55:48','2025-08-05 14:25:48',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:55:48'),(40,'user_1754397315','U8lDvy3IOX6_2cP3GWCflQ','refresh','2025-08-05 21:55:48','2025-08-12 13:55:48',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 21:55:48'),(41,'user_1754397315','UARAktnS6QAFQUyeXX90Bg','access','2025-08-05 22:02:50','2025-08-05 14:32:50',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 22:02:50'),(42,'user_1754397315','4Mr2YArUJjdvK01pxMog-Q','refresh','2025-08-05 22:02:50','2025-08-12 14:02:50',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-05 22:02:50'),(43,'user_1754397315','IMt8-wjpgNdip-hVgtTvfw','access','2025-08-06 06:45:15','2025-08-05 23:15:15',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 06:45:15'),(44,'user_1754397315','Wp0LK8sld7AnIqhdfzt6bA','refresh','2025-08-06 06:45:15','2025-08-12 22:45:15',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 06:45:15'),(45,'user_1754397315','tQqt_JTelJn2-1gPV6m_rQ','access','2025-08-06 06:45:21','2025-08-05 23:15:21',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 06:45:21'),(46,'user_1754397315','EPtQHx-F1poWpXq9rhLopA','refresh','2025-08-06 06:45:21','2025-08-12 22:45:21',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 06:45:21'),(47,'user_1754397315','9jxwNJql7AC7I9npZnzJ4w','access','2025-08-06 06:45:35','2025-08-05 23:15:35',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 06:45:35'),(48,'user_1754397315','6Omzv-NSomOuHjMLF0gbqw','refresh','2025-08-06 06:45:35','2025-08-12 22:45:35',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 06:45:35'),(49,'user_1754397315','u60rofzYE2cplc4oUt8EZg','access','2025-08-06 06:53:40','2025-08-05 23:23:40',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 06:53:40'),(50,'user_1754397315','IoirbTYi9v5NUOY2suambQ','refresh','2025-08-06 06:53:40','2025-08-12 22:53:40',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 06:53:40'),(51,'user_1754397315','nbLIVqPFM9p4goRF6F49aQ','access','2025-08-06 07:04:26','2025-08-05 23:34:26',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 07:04:26'),(52,'user_1754397315','_01Tf_PWjIpWf_VEkKBIKw','refresh','2025-08-06 07:04:26','2025-08-12 23:04:26',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 07:04:26'),(53,'user_1754397315','163FXcbEXw87_gQviDO9ow','access','2025-08-06 07:04:36','2025-08-05 23:34:36',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 07:04:36'),(54,'user_1754397315','luytnVAFN5mOKKpU-KHblw','refresh','2025-08-06 07:04:36','2025-08-12 23:04:36',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 07:04:36'),(55,'user_1754397315','HKhVDy2v6d9Q4guuJOS1Wg','access','2025-08-06 07:08:52','2025-08-05 23:38:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 07:08:52'),(56,'user_1754397315','LU-fJDvWf-L_IvtIKTIbug','refresh','2025-08-06 07:08:52','2025-08-12 23:08:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 07:08:52'),(57,'user_1754397315','4gwYMBUneH-hshJRdFxMUw','access','2025-08-06 07:51:13','2025-08-06 00:21:12',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 07:51:13'),(58,'user_1754397315','C08Rd151EVtxK5FA6LQA2Q','refresh','2025-08-06 07:51:13','2025-08-12 23:51:12',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 07:51:13'),(59,'user_1754397315','Gq8Uxey5WVrFwSYORF0GvQ','access','2025-08-06 08:06:10','2025-08-06 00:36:10',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 08:06:10'),(60,'user_1754397315','U9Pf-iMz2vTsZfGwSPrzkw','refresh','2025-08-06 08:06:10','2025-08-13 00:06:10',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 08:06:10'),(61,'user_1754397315','IeqHlxcj-bNLE0i0ypPTeQ','access','2025-08-06 08:14:02','2025-08-06 00:44:02',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 08:14:02'),(62,'user_1754397315','TbfWC94J4iUpkrA8Svmn0w','refresh','2025-08-06 08:14:02','2025-08-13 00:14:02',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 08:14:02'),(63,'user_1754397315','fe_CqzPGj_HW_MCRPWSnuw','access','2025-08-06 08:18:03','2025-08-06 00:48:03',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 08:18:03'),(64,'user_1754397315','mkPaJbiKI_9xDh-ke-j_1g','refresh','2025-08-06 08:18:03','2025-08-13 00:18:03',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 08:18:03'),(65,'user_1754397315','aDX87bAUwKlRhFKK1gTVwA','access','2025-08-06 08:48:14','2025-08-06 01:18:14',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 08:48:14'),(66,'user_1754397315','5s_mEgri6D3PR3m7USeIHg','refresh','2025-08-06 08:48:14','2025-08-13 00:48:14',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 08:48:14'),(67,'user_1754397315','wdgaF_ixm0xmPt7q1Nne8A','access','2025-08-06 09:14:52','2025-08-06 01:44:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 09:14:52'),(68,'user_1754397315','vHY6RbFRjyReKUO5udW7LA','refresh','2025-08-06 09:14:52','2025-08-13 01:14:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 09:14:52'),(69,'user_1754397315','1S969FjnfvF2Whd8dwDjQA','access','2025-08-06 09:38:03','2025-08-06 02:08:03',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 09:38:03'),(70,'user_1754397315','IViOj-bXidQqUy-PAKGHSw','refresh','2025-08-06 09:38:03','2025-08-13 01:38:03',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 09:38:03'),(71,'user_1754397315','oSykXDvfhj6MRKDjXz-bUQ','access','2025-08-06 09:38:38','2025-08-06 02:08:38',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 09:38:38'),(72,'user_1754397315','tbx4QzLZ0BPF35enXr0GHg','refresh','2025-08-06 09:38:38','2025-08-13 01:38:38',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 09:38:38'),(73,'user_1754397315','hUTWg9L1WAOBGOd4vH4Hnw','access','2025-08-06 09:39:27','2025-08-06 02:09:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 09:39:27'),(74,'user_1754397315','m1R73eR6UrkhCinRz0o1Aw','refresh','2025-08-06 09:39:27','2025-08-13 01:39:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 09:39:27'),(75,'user_1754397315','TtlvRmGOpaQGZB5rAHpQwQ','access','2025-08-06 10:08:08','2025-08-06 02:38:08',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 10:08:08'),(76,'user_1754397315','BlAULcbg_z1FlktFYd1MHA','refresh','2025-08-06 10:08:08','2025-08-13 02:08:08',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 10:08:08'),(77,'user_1754397315','X0QIqPgBnvsz7A8K-wLI9A','access','2025-08-06 10:20:21','2025-08-06 02:50:21',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 10:20:21'),(78,'user_1754397315','uKzESYPxKBZuq4_vmb2YPg','refresh','2025-08-06 10:20:21','2025-08-13 02:20:21',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 10:20:21'),(79,'user_1754397315','gn_FCV5Z1IJ2jTSf21a_WQ','access','2025-08-06 10:39:03','2025-08-06 03:09:03',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 10:39:03'),(80,'user_1754397315','cYocMUaU9_mf26Chf8dSBg','refresh','2025-08-06 10:39:03','2025-08-13 02:39:03',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 10:39:03'),(81,'user_1754397315','WCqJ6flGyyBZEmMM_8fGJw','access','2025-08-06 10:48:13','2025-08-06 03:18:13',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 10:48:13'),(82,'user_1754397315','y8FZ5XEO6tJH5e86KV2JdQ','refresh','2025-08-06 10:48:13','2025-08-13 02:48:13',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 10:48:13'),(83,'user_1754397315','mdKCCkUcPjP29SjX1a4Nvg','access','2025-08-06 11:12:05','2025-08-06 03:42:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:12:05'),(84,'user_1754397315','zsHjFfGnEJ7yKXl9sGYozA','refresh','2025-08-06 11:12:05','2025-08-13 03:12:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:12:05'),(85,'user_1754397315','bfH2gIsQuxFQCrrUIHDciQ','access','2025-08-06 11:12:33','2025-08-06 03:42:33',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:12:33'),(86,'user_1754397315','Ifd4iwUVMepwbro_2FOiWg','refresh','2025-08-06 11:12:33','2025-08-13 03:12:33',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:12:33'),(87,'user_1754397315','kTRe5TM-vUdfAm0xYQLBFQ','access','2025-08-06 11:29:52','2025-08-06 03:59:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:29:52'),(88,'user_1754397315','pYX54damS5wlK1Ii5WqX3Q','refresh','2025-08-06 11:29:52','2025-08-13 03:29:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:29:52'),(89,'user_1754397315','zhxIXo6Q8z6vtduPzgL_iw','access','2025-08-06 11:30:20','2025-08-06 04:00:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:30:20'),(90,'user_1754397315','9aj9rOKGDmFLkx69wspYww','refresh','2025-08-06 11:30:20','2025-08-13 03:30:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:30:20'),(91,'user_1754397315','P1769zfzQ7kSUK0pY_pT5Q','access','2025-08-06 11:33:49','2025-08-06 04:03:49',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:33:49'),(92,'user_1754397315','5Y8ViJzYEjCYgldphoKyrw','refresh','2025-08-06 11:33:49','2025-08-13 03:33:49',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:33:49'),(93,'user_1754397315','Kvr7ij3hcjsVI_Dv2KP9Tg','access','2025-08-06 11:35:27','2025-08-06 04:05:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:35:27'),(94,'user_1754397315','bFVS4Xp4qiIE_gAapgsGTg','refresh','2025-08-06 11:35:27','2025-08-13 03:35:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:35:27'),(95,'user_1754397315','NqzzxhkcTgfjO3mTL9PjXg','access','2025-08-06 11:35:38','2025-08-06 04:05:38',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:35:38'),(96,'user_1754397315','SgSgBfpOjcO4YHQS3g-k1g','refresh','2025-08-06 11:35:38','2025-08-13 03:35:38',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:35:38'),(97,'user_1754397315','7w3JWwgcz0S8p0Tbqrl8yQ','access','2025-08-06 11:36:02','2025-08-06 04:06:02',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:36:02'),(98,'user_1754397315','qhUWdxc7uO9mG1qUy2KgTg','refresh','2025-08-06 11:36:02','2025-08-13 03:36:02',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:36:02'),(99,'user_1754397315','UezdvyHYAatPzX68bif79w','access','2025-08-06 11:55:38','2025-08-06 04:25:38',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:55:38'),(100,'user_1754397315','fPix99cCLs80mwVhoZK44w','refresh','2025-08-06 11:55:38','2025-08-13 03:55:38',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:55:38'),(101,'user_1754397315','Nb2mYxaXrktSyEdJTXIZSA','access','2025-08-06 11:59:04','2025-08-06 04:29:04',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:59:04'),(102,'user_1754397315','auDU-tl4sn5VodyrGvjLww','refresh','2025-08-06 11:59:04','2025-08-13 03:59:04',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 11:59:04'),(103,'user_1754397315','qGhsnzIOngraUH7ZjNGGJQ','access','2025-08-06 12:03:35','2025-08-06 04:33:35',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:03:35'),(104,'user_1754397315','N5MANZ1uadybYMvhoh0Qjw','refresh','2025-08-06 12:03:35','2025-08-13 04:03:35',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:03:35'),(105,'user_1754397315','6R0R7UOdJAkF8dgTpfeP4Q','access','2025-08-06 12:10:13','2025-08-06 04:40:13',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:10:13'),(106,'user_1754397315','gL1QOobuRTuT-oTA15V_Mw','refresh','2025-08-06 12:10:13','2025-08-13 04:10:13',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:10:13'),(107,'user_1754397315','hHAD-4Pvo1yUaqYWj3RfEg','access','2025-08-06 12:16:02','2025-08-06 04:46:02',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:16:02'),(108,'user_1754397315','25JEAoOAFM6YUtWudq7fPA','refresh','2025-08-06 12:16:02','2025-08-13 04:16:02',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:16:02'),(109,'user_1754397315','ggT9vzg2-nNYGtEO9YE3_w','access','2025-08-06 12:31:29','2025-08-06 05:01:29',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:31:29'),(110,'user_1754397315','AbDZqGiGs0gFXCBnb5g8kg','refresh','2025-08-06 12:31:29','2025-08-13 04:31:29',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:31:29'),(111,'user_1754397315','4V1Sxn1ABeqD07WcDIQVzA','access','2025-08-06 12:43:05','2025-08-06 05:13:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:43:05'),(112,'user_1754397315','w9M6MvK5xpfarKSsggbEaQ','refresh','2025-08-06 12:43:06','2025-08-13 04:43:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:43:06'),(113,'user_1754397315','PcZe7qDWYLyMbZ8p4c2oHQ','access','2025-08-06 12:46:41','2025-08-06 05:16:41',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:46:41'),(114,'user_1754397315','iIqAod_epzm7k_PIipr6_g','refresh','2025-08-06 12:46:42','2025-08-13 04:46:41',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:46:42'),(115,'user_1754397315','ZHd1kk1aeyuuLJw6jKFXzA','access','2025-08-06 12:47:32','2025-08-06 05:17:32',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:47:32'),(116,'user_1754397315','ooyFD_TELQvr9dHUcUBiaw','refresh','2025-08-06 12:47:33','2025-08-13 04:47:32',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:47:33'),(117,'user_1754397315','LpBKdEDJNVaCyBaQccrL5Q','access','2025-08-06 12:54:21','2025-08-06 05:24:21',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:54:21'),(118,'user_1754397315','McUsoFX-pUhTmi4ox3RkFg','refresh','2025-08-06 12:54:21','2025-08-13 04:54:21',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:54:21'),(119,'user_1754397315','tMeKx3Fj3oJtRW9Cn4DKaA','access','2025-08-06 12:55:16','2025-08-06 05:25:16',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:55:16'),(120,'user_1754397315','rz82E-oDC6gDxzOydF0kiw','refresh','2025-08-06 12:55:16','2025-08-13 04:55:16',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 12:55:16'),(121,'user_1754397315','t8gSm_oFi5tlUtIeEeE4hg','access','2025-08-06 13:50:13','2025-08-06 06:20:13',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 13:50:13'),(122,'user_1754397315','RbCCAaZgOjBmfYZbDnlk_Q','refresh','2025-08-06 13:50:13','2025-08-13 05:50:13',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 13:50:13'),(123,'user_1754397315','11x1ZyGc2GKuLi-9_bTb-Q','access','2025-08-06 13:55:48','2025-08-06 06:25:48',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 13:55:48'),(124,'user_1754397315','Sfk6bN3z95QwZL8nDjAjBg','refresh','2025-08-06 13:55:48','2025-08-13 05:55:48',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 13:55:48'),(125,'user_1754397315','I0ac7x_e_6sYyEfTGknegQ','access','2025-08-06 13:56:44','2025-08-06 06:26:44',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 13:56:44'),(126,'user_1754397315','CbzvB-fT-paZq0snKdEqJw','refresh','2025-08-06 13:56:44','2025-08-13 05:56:44',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 13:56:44'),(127,'user_1754397315','6q7lk5OaIuAUAOS2iq27rA','access','2025-08-06 13:58:52','2025-08-06 06:28:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 13:58:52'),(128,'user_1754397315','OT6rdKTuQ-9OkpGUivim3Q','refresh','2025-08-06 13:58:52','2025-08-13 05:58:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 13:58:52'),(129,'user_1754397315','4VipnS20gIqQ1AIwWImiBA','access','2025-08-06 14:01:21','2025-08-06 06:31:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 14:01:21'),(130,'user_1754397315','rVQ0aS-iXZ1M9EI9le-imA','refresh','2025-08-06 14:01:21','2025-08-13 06:01:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 14:01:21'),(131,'user_1754397315','8pK8aq_pt2PXoaXwINsIjA','access','2025-08-06 14:10:55','2025-08-06 06:40:55',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 14:10:55'),(132,'user_1754397315','gYMknL8jrSd6YEpPG8gzQw','refresh','2025-08-06 14:10:55','2025-08-13 06:10:55',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 14:10:55'),(133,'user_1754397315','-oCeuoUE5z_suEATQjJ4Sw','access','2025-08-06 14:20:34','2025-08-06 06:50:34',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 14:20:34'),(134,'user_1754397315','NnxOLGEhzT3xpUqR-ZHgnA','refresh','2025-08-06 14:20:34','2025-08-13 06:20:34',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 14:20:34'),(135,'user_1754397315','T7hH3v8J1_JGFP0tQl-1Nw','access','2025-08-06 14:24:17','2025-08-06 06:54:17',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 14:24:17'),(136,'user_1754397315','YmIQFVsGqIwsrXhjtGeHYQ','refresh','2025-08-06 14:24:17','2025-08-13 06:24:17',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 14:24:17'),(137,'user_1754397315','FyL4v3c41Aks7fiXctbgdQ','access','2025-08-06 15:15:45','2025-08-06 07:45:45',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:15:45'),(138,'user_1754397315','lrdh9i1iBsp7rTYwNhr6VA','refresh','2025-08-06 15:15:45','2025-08-13 07:15:45',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:15:45'),(139,'user_1754397315','Sq9mCDexH5QhED6UbILdRw','access','2025-08-06 15:31:00','2025-08-06 08:01:00',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:31:00'),(140,'user_1754397315','CfwwIXYzCXK6dXpUv7L7mw','refresh','2025-08-06 15:31:00','2025-08-13 07:31:00',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:31:00'),(141,'user_1754397315','0BhuhAsQp7xnfW-p16TjAg','access','2025-08-06 15:32:27','2025-08-06 08:02:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:32:27'),(142,'user_1754397315','NNACfzq_LfUcRNsMJgp3ZQ','refresh','2025-08-06 15:32:27','2025-08-13 07:32:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:32:27'),(143,'user_1754397315','El015sJithq6MG-TTDf1YQ','access','2025-08-06 15:33:27','2025-08-06 08:03:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:33:27'),(144,'user_1754397315','3Ba_iHWirCge5IydTw-Hsw','refresh','2025-08-06 15:33:27','2025-08-13 07:33:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:33:27'),(145,'user_1754397315','0vUuWjYOSPFW7A38vlpdtg','access','2025-08-06 15:37:16','2025-08-06 08:07:16',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:37:16'),(146,'user_1754397315','AOywyaH2q61KFdvo-se7hA','refresh','2025-08-06 15:37:16','2025-08-13 07:37:16',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:37:16'),(147,'user_1754397315','PCkF6uDc6ilVMYfHBDMRjw','access','2025-08-06 15:38:50','2025-08-06 08:08:50',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:38:50'),(148,'user_1754397315','RInQ-RnLiTDh4lTO79g8_g','refresh','2025-08-06 15:38:50','2025-08-13 07:38:50',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:38:50'),(149,'user_1754397315','_PYEvLlNxcXnJyFKktXPMw','access','2025-08-06 15:40:15','2025-08-06 08:10:15',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:40:15'),(150,'user_1754397315','MB5_hLEHusIs0xJQG_MbbA','refresh','2025-08-06 15:40:15','2025-08-13 07:40:15',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:40:15'),(151,'user_1754397315','mew-Yz8R1zTsdqWKjKaY0w','access','2025-08-06 15:41:11','2025-08-06 08:11:11',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:41:11'),(152,'user_1754397315','q-gJb4ZgEHSkxzOycDh9Rg','refresh','2025-08-06 15:41:11','2025-08-13 07:41:11',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:41:11'),(153,'user_1754397315','WpDHeygrrzp15kdGPZUtUQ','access','2025-08-06 15:42:47','2025-08-06 08:12:47',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:42:47'),(154,'user_1754397315','tJUOtvYvCOFblBJoCn5-2A','refresh','2025-08-06 15:42:47','2025-08-13 07:42:47',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:42:47'),(155,'user_1754397315','3fZFQXHHMjAv_y5FRjOPUg','access','2025-08-06 15:49:08','2025-08-06 08:19:08',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:49:08'),(156,'user_1754397315','vFEbwoIOHa-js20wSo0qbQ','refresh','2025-08-06 15:49:08','2025-08-13 07:49:08',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:49:08'),(157,'user_1754397315','5AW3W9cpD5O5DVYQy6UBEA','access','2025-08-06 15:50:05','2025-08-06 08:20:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:50:05'),(158,'user_1754397315','i5i_bDay2OxuRsqG1JGuOg','refresh','2025-08-06 15:50:05','2025-08-13 07:50:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:50:05'),(159,'user_1754397315','zeP3z8H6Fh3pwjY0C6iRug','access','2025-08-06 15:50:33','2025-08-06 08:20:33',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:50:33'),(160,'user_1754397315','x4yEvt9k8lHilnZSwx4yAw','refresh','2025-08-06 15:50:33','2025-08-13 07:50:33',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:50:33'),(161,'user_1754397315','b8LLlY5-hc4US04mEmidsg','access','2025-08-06 15:51:22','2025-08-06 08:21:22',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:51:22'),(162,'user_1754397315','SDQwk-GkYUql0SzHfOZgVA','refresh','2025-08-06 15:51:22','2025-08-13 07:51:22',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:51:22'),(163,'user_1754397315','L9KQ7dm3bjJQ8F4dRE3uTA','access','2025-08-06 15:52:11','2025-08-06 08:22:11',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:52:11'),(164,'user_1754397315','p_LkJfkLGPauIauxGh5bvA','refresh','2025-08-06 15:52:11','2025-08-13 07:52:11',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 15:52:11'),(165,'user_1754397315','9eKQB2a6xsM4SS5r0hdzeg','access','2025-08-06 16:12:16','2025-08-06 08:42:16',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:12:16'),(166,'user_1754397315','azmsXOcQ8FP7twtNC1MFnw','refresh','2025-08-06 16:12:16','2025-08-13 08:12:16',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:12:16'),(167,'user_1754397315','4AcGWy4S5B8eM3h2po2JuA','access','2025-08-06 16:15:37','2025-08-06 08:45:37',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:15:37'),(168,'user_1754397315','V4FRd6V8eqKMqIdmmXNr6A','refresh','2025-08-06 16:15:37','2025-08-13 08:15:37',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:15:37'),(169,'user_1754397315','gWpCQdIH5gQGL2Ti55NzHw','access','2025-08-06 16:40:33','2025-08-06 09:10:33',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:40:33'),(170,'user_1754397315','eYl0JbbRoKl-MjCie0zsow','refresh','2025-08-06 16:40:33','2025-08-13 08:40:33',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:40:33'),(171,'user_1754397315','rCwAY9lwYdYug3hSMgZyYw','access','2025-08-06 16:41:18','2025-08-06 09:11:18',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:41:18'),(172,'user_1754397315','z919wzHluUcvVS8-8Grp-A','refresh','2025-08-06 16:41:19','2025-08-13 08:41:18',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:41:19'),(173,'user_1754397315','MqkbOknHI9lEkat00gEMLA','access','2025-08-06 16:43:00','2025-08-06 09:13:00',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:43:00'),(174,'user_1754397315','up7ljIkUTlCO8nRvz_mXuA','refresh','2025-08-06 16:43:00','2025-08-13 08:43:00',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:43:00'),(175,'user_1754397315','kjqrAhbrrNQ431JcNoTdog','access','2025-08-06 16:44:56','2025-08-06 09:14:55',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:44:56'),(176,'user_1754397315','xKZo0lExJvI16EJbcWFtbw','refresh','2025-08-06 16:44:56','2025-08-13 08:44:55',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:44:56'),(177,'user_1754397315','0w6Zro-1XYRt-vHlXp3vIg','access','2025-08-06 16:47:52','2025-08-06 09:17:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:47:52'),(178,'user_1754397315','PMYWdYSuUJ3OufLunMDvZg','refresh','2025-08-06 16:47:52','2025-08-13 08:47:52',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 16:47:52'),(179,'user_1754397315','df107GocIMbd6SaQvX-wGA','access','2025-08-06 17:09:47','2025-08-06 09:39:47',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:09:47'),(180,'user_1754397315','MTe1yQ1GEvusxTUxZEmp8w','refresh','2025-08-06 17:09:47','2025-08-13 09:09:47',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:09:47'),(181,'user_1754397315','87QfF_QaHwg2C03n8RthTQ','access','2025-08-06 17:18:58','2025-08-06 09:48:58',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:18:58'),(182,'user_1754397315','2NembhP96Ijpa3xhVJWgIg','refresh','2025-08-06 17:18:58','2025-08-13 09:18:58',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:18:58'),(183,'user_1754397315','yp8zr3ZqtEJvDhgFfY3oag','access','2025-08-06 17:19:36','2025-08-06 09:49:36',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:19:36'),(184,'user_1754397315','30O6tTsgoRXnjyAFiZCxEA','refresh','2025-08-06 17:19:36','2025-08-13 09:19:36',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:19:36'),(185,'user_1754397315','hGFNX3Lg2NW5K13NORpoWQ','access','2025-08-06 17:27:22','2025-08-06 09:57:22',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:27:22'),(186,'user_1754397315','FGrgOvN2GWG6axfTPJ65RA','refresh','2025-08-06 17:27:22','2025-08-13 09:27:22',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:27:22'),(187,'user_1754397315','fiDdbmBwNphSU7nwPiBAKg','access','2025-08-06 17:31:53','2025-08-06 10:01:53',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:31:53'),(188,'user_1754397315','le229eVT3sjX0pGjhIz7XA','refresh','2025-08-06 17:31:53','2025-08-13 09:31:53',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:31:53'),(189,'user_1754397315','woEd-ORf6Ym4uLeVmXO56w','access','2025-08-06 17:35:19','2025-08-06 10:05:19',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:35:19'),(190,'user_1754397315','PudJ2Mq-y6TbKwM6FnEkfg','refresh','2025-08-06 17:35:19','2025-08-13 09:35:19',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:35:19'),(191,'user_1754397315','EoIxEmcHZmZ1lLSm9xioMA','access','2025-08-06 17:37:15','2025-08-06 10:07:15',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:37:15'),(192,'user_1754397315','koS6v-evSmOVp-nS_TWCCQ','refresh','2025-08-06 17:37:15','2025-08-13 09:37:15',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:37:15'),(193,'user_1754397315','0pB0chuNUKel2DVXRBgb3A','access','2025-08-06 17:41:29','2025-08-06 10:11:29',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:41:29'),(194,'user_1754397315','VojxkQ8ICPmOwQYpAVfmeg','refresh','2025-08-06 17:41:29','2025-08-13 09:41:29',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:41:29'),(195,'user_1754397315','2b51sELQYwC8WSA66lEamA','access','2025-08-06 17:43:26','2025-08-06 10:13:26',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:43:26'),(196,'user_1754397315','uQPD3AWOLN2HiXU9FwbWBQ','refresh','2025-08-06 17:43:26','2025-08-13 09:43:26',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:43:26'),(197,'user_1754397315','AaFImgNNFfFDWU9ubiXElw','access','2025-08-06 17:44:26','2025-08-06 10:14:26',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:44:26'),(198,'user_1754397315','sN7yegEUdDO1t3LEYK4K-w','refresh','2025-08-06 17:44:26','2025-08-13 09:44:26',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:44:26'),(199,'user_1754397315','Pqxvh9wcJlPBJHHSGXZJqA','access','2025-08-06 17:46:48','2025-08-06 10:16:48',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:46:48'),(200,'user_1754397315','LzSqejYHVgc5rGCJrnBKTg','refresh','2025-08-06 17:46:48','2025-08-13 09:46:48',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:46:48'),(201,'user_1754397315','k_hD7RWfiPw573pYiTFZOQ','access','2025-08-06 17:47:05','2025-08-06 10:17:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:47:05'),(202,'user_1754397315','GWkJv3LdfbWMKd5F996OfQ','refresh','2025-08-06 17:47:05','2025-08-13 09:47:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:47:05'),(203,'user_1754397315','HVgP44ccu_EKvMCWyCw1Mg','access','2025-08-06 17:48:28','2025-08-06 10:18:28',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:48:28'),(204,'user_1754397315','i-GwALRAk5l6ybjNfIJoiw','refresh','2025-08-06 17:48:28','2025-08-13 09:48:28',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:48:28'),(205,'user_1754397315','afLUa5030aeIahyZyzi0fA','access','2025-08-06 17:55:44','2025-08-06 10:25:44',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:55:44'),(206,'user_1754397315','VzqahZJccWoccGn1vm9fjA','refresh','2025-08-06 17:55:44','2025-08-13 09:55:44',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:55:44'),(207,'user_1754397315','u4eSsObTVeAxjDLx2BuZTg','access','2025-08-06 17:56:54','2025-08-06 10:26:54',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:56:54'),(208,'user_1754397315','RsYnjJmpYRFdkgTezAxt6w','refresh','2025-08-06 17:56:54','2025-08-13 09:56:54',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 17:56:54'),(209,'user_1754397315','WNCbuIixYjftQ5ya3TSPBw','access','2025-08-06 19:45:29','2025-08-06 12:15:29',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 19:45:29'),(210,'user_1754397315','kkJn4L7QWdW1D0VwOzcqcA','refresh','2025-08-06 19:45:29','2025-08-13 11:45:29',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 19:45:29'),(211,'user_1754397315','U-E2lUk0ONLWW1bYbnOK0A','access','2025-08-06 20:10:20','2025-08-06 12:40:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:10:20'),(212,'user_1754397315','IJGb78AcmH8BGktcM1iQbw','refresh','2025-08-06 20:10:20','2025-08-13 12:10:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:10:20'),(213,'user_1754397315','j5wddoERjpTEnImo-_X4qw','access','2025-08-06 20:12:49','2025-08-06 12:42:49',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:12:49'),(214,'user_1754397315','5h52y92sG5RqBQSs1sgsuA','refresh','2025-08-06 20:12:49','2025-08-13 12:12:49',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:12:49'),(215,'user_1754397315','zwg_PjNj4PD80w77HGehyg','access','2025-08-06 20:31:11','2025-08-06 13:01:11',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:31:11'),(216,'user_1754397315','Vcyz3si0HxKQhfz5mXga4A','refresh','2025-08-06 20:31:11','2025-08-13 12:31:11',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:31:11'),(217,'user_1754397315','Zm-Tjk-_UfQWglCx-t9wOg','access','2025-08-06 20:31:30','2025-08-06 13:01:30',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:31:30'),(218,'user_1754397315','mcJGuohpkPXLgcATrYL6hQ','refresh','2025-08-06 20:31:31','2025-08-13 12:31:30',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:31:31'),(219,'user_1754397315','YkSwnjTxZBfsdmckeBXfEg','access','2025-08-06 20:32:05','2025-08-06 13:02:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:32:05'),(220,'user_1754397315','pzRz4hXbOddXveHbH-bfjQ','refresh','2025-08-06 20:32:05','2025-08-13 12:32:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:32:05'),(221,'user_1754397315','vaoFROK2d9qfnj7_9CZrvg','access','2025-08-06 20:34:31','2025-08-06 13:04:31',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:34:31'),(222,'user_1754397315','i4nNloderKpYDPC41iHN1A','refresh','2025-08-06 20:34:31','2025-08-13 12:34:31',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:34:31'),(223,'user_1754397315','AqT8WReU4KHnovfJf5gC6Q','access','2025-08-06 20:36:46','2025-08-06 13:06:46',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:36:46'),(224,'user_1754397315','vmFLpcimCBjxu0Js1BD_JQ','refresh','2025-08-06 20:36:46','2025-08-13 12:36:46',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:36:46'),(225,'user_1754397315','suUJHeRwkaxb3IB4ZqdxuA','access','2025-08-06 20:37:32','2025-08-06 13:07:32',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:37:32'),(226,'user_1754397315','5nslzskDBl30f8KBKam7cg','refresh','2025-08-06 20:37:32','2025-08-13 12:37:32',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:37:32'),(227,'user_1754397315','5mLvhxq-dXwYPy2PWj0H6w','access','2025-08-06 20:38:10','2025-08-06 13:08:09',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:38:10'),(228,'user_1754397315','B_V4B23vGE6puFBuwAkOsQ','refresh','2025-08-06 20:38:10','2025-08-13 12:38:09',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:38:10'),(229,'user_1754397315','aX9IILA6ZRnDt-piu0Q5vw','access','2025-08-06 20:54:10','2025-08-06 13:24:10',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:54:10'),(230,'user_1754397315','Z_ZIxqnb4Fst68yhkcB0jA','refresh','2025-08-06 20:54:10','2025-08-13 12:54:10',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:54:10'),(231,'user_1754397315','fpQ60SrUSJkvhdQwHJ4dVg','access','2025-08-06 20:57:41','2025-08-06 13:27:41',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:57:41'),(232,'user_1754397315','nSXdhM1pKqgFCatcx6sC_Q','refresh','2025-08-06 20:57:41','2025-08-13 12:57:41',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 20:57:41'),(233,'user_1754397315','Uf45SCyMkxQywEbJQXrC4A','access','2025-08-06 21:01:50','2025-08-06 13:31:50',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 21:01:50'),(234,'user_1754397315','FB8_KChh5y1d60n23IOwmA','refresh','2025-08-06 21:01:50','2025-08-13 13:01:50',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 21:01:50'),(235,'user_1754397315','MKD_R9dTg2pYZUJAbHwCKQ','access','2025-08-06 21:04:51','2025-08-06 13:34:51',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 21:04:51'),(236,'user_1754397315','aovU2yLnu7KR-SoQi-3-Eg','refresh','2025-08-06 21:04:51','2025-08-13 13:04:51',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 21:04:51'),(237,'user_1754397315','3HYodNARIs-VWvkOBDHvcQ','access','2025-08-06 21:52:58','2025-08-06 14:22:58',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 21:52:58'),(238,'user_1754397315','lF9G6v26fv_due53Gw5pdQ','refresh','2025-08-06 21:52:58','2025-08-13 13:52:58',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 21:52:58'),(239,'user_1754397315','y-OFncxKv7T9D7GJHNRq_A','access','2025-08-06 22:11:55','2025-08-06 14:41:54',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 22:11:55'),(240,'user_1754397315','HUjuIVrHVAgGZhEpWsk70w','refresh','2025-08-06 22:11:55','2025-08-13 14:11:54',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-06 22:11:55'),(241,'user_1754397315','IB3wNfhk9r0ZQAeA4egEkQ','access','2025-08-07 09:25:26','2025-08-07 01:55:26',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 09:25:26'),(242,'user_1754397315','v6ROtDFQoSaPns3D59hqyA','refresh','2025-08-07 09:25:26','2025-08-14 01:25:26',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 09:25:26'),(243,'user_1754397315','uCxX5KogVKGasOjcbgbONw','access','2025-08-07 10:45:10','2025-08-07 03:15:10',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 10:45:10'),(244,'user_1754397315','bECxGPTDlTDgOtHyJD8KHw','refresh','2025-08-07 10:45:10','2025-08-14 02:45:10',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 10:45:10'),(245,'user_1754397315','ukNRuRbAZfA9unqmYlti8Q','access','2025-08-07 11:22:27','2025-08-07 03:52:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 11:22:27'),(246,'user_1754397315','pmb7L399v4K9o5QzxSiuoQ','refresh','2025-08-07 11:22:27','2025-08-14 03:22:27',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 11:22:27'),(247,'user_1754397315','DgZTfgS-QhV6qBo41eyBXQ','access','2025-08-07 11:47:29','2025-08-07 04:17:29',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 11:47:29'),(248,'user_1754397315','xtQl3007N2wnoNvtfYEP-A','refresh','2025-08-07 11:47:29','2025-08-14 03:47:29',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 11:47:29'),(249,'user_1754397315','SfQ6GlBAt33PXFq-j49GqA','access','2025-08-07 15:23:05','2025-08-07 07:53:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 15:23:05'),(250,'user_1754397315','2WuqchF69XdfOw1ZY5xrWA','refresh','2025-08-07 15:23:05','2025-08-14 07:23:05',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-07 15:23:05'),(251,'user_1754397315','ImofpB0Kvx6BXlGNwbguIQ','access','2025-08-08 07:07:07','2025-08-07 23:37:07',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-08 07:07:07'),(252,'user_1754397315','zfAe2UNmMuSjcnQXtg6SKg','refresh','2025-08-08 07:07:07','2025-08-14 23:07:07',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-08 07:07:07'),(253,'user_1754397315','9Aaf0QA1cezlwJ9sidR5kA','access','2025-08-08 09:13:20','2025-08-08 01:43:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-08 09:13:20'),(254,'user_1754397315','Us6URMSpGAT9EtRil_PH1g','refresh','2025-08-08 09:13:20','2025-08-15 01:13:20',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-08 09:13:20'),(255,'user_1754616685','agulY6DsVEsmDeoU0UXqlQ','access','2025-08-08 09:31:34','2025-08-08 02:01:34',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-08 09:31:34'),(256,'user_1754616685','PCHw85eiuCO8Hl9dB05oEw','refresh','2025-08-08 09:31:34','2025-08-15 01:31:34',NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,'2025-08-08 09:31:34');
/*!40000 ALTER TABLE `auth_tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `auth_users`
--

DROP TABLE IF EXISTS `auth_users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `auth_users` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `user_id` varchar(64) NOT NULL COMMENT '关联RBAC用户ID',
  `password_hash` varchar(255) DEFAULT NULL COMMENT '密码哈希（JWT认证使用）',
  `mfa_secret` varchar(255) DEFAULT NULL COMMENT 'MFA密钥',
  `mfa_enabled` tinyint(1) DEFAULT '0' COMMENT '是否启用MFA',
  `last_login` datetime DEFAULT NULL COMMENT '最后登录时间',
  `last_login_ip` varchar(45) DEFAULT NULL COMMENT '最后登录IP',
  `login_attempts` int(11) DEFAULT '0' COMMENT '登录尝试次数',
  `locked_until` datetime DEFAULT NULL COMMENT '账户锁定到期时间',
  `sso_provider` varchar(50) DEFAULT NULL COMMENT 'SSO提供商标识',
  `sso_user_id` varchar(255) DEFAULT NULL COMMENT 'SSO用户ID',
  `sso_attributes` text COMMENT 'SSO属性（JSON格式）',
  `password_changed_at` datetime DEFAULT NULL COMMENT '密码最后修改时间',
  `require_password_change` tinyint(1) DEFAULT '0' COMMENT '是否需要修改密码',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_id` (`user_id`),
  KEY `idx_last_login` (`last_login`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COMMENT='用户认证信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `auth_users`
--

LOCK TABLES `auth_users` WRITE;
/*!40000 ALTER TABLE `auth_users` DISABLE KEYS */;
INSERT INTO `auth_users` VALUES (1,'user_1754282487','$2b$12$vWZl4CskGZvl79GvMkTZUu5YqL5CC7gAGI5SckDihNnSOnJ94x8pW',NULL,0,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,0,'2025-08-04 12:41:28','2025-08-04 12:41:28'),(2,'user_1754282511','$2b$12$yOTCWrfehPx/GxD3S7STZuIAhbgTFsl1tJV4RhSZRsHAIbEM6ItuK',NULL,0,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,0,'2025-08-04 12:41:52','2025-08-04 12:41:52'),(3,'user_1754283990','$2b$12$KF1pQmjHGODXv9QEUuo2xeBHUsvAdKnHOxOvqq6T/mH.LjSIsQ3Fu',NULL,0,'2025-08-04 12:40:19',NULL,1,NULL,NULL,NULL,NULL,NULL,0,'2025-08-04 13:06:31','2025-08-05 07:37:54'),(4,'user_1754284138','$2b$12$HrBUICZ2gfpPWLdOgvqEXucB985evhPGuBql9cSrhZUP879.xifim',NULL,0,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,0,'2025-08-04 13:08:59','2025-08-04 13:08:59'),(5,'user_1754284542','$2b$12$eqnlEHWawrKHnaKt6nLhDu.b7DQ5CKH..kq6SH5SBGrPLkEdf44Aq',NULL,0,'2025-08-04 06:08:03',NULL,0,NULL,NULL,NULL,NULL,NULL,0,'2025-08-04 13:15:43','2025-08-04 14:08:03'),(6,'user_1754397315','$2b$12$JSSfeM.NrUCfoiUf4e/5sexhtDCs5YoqZ6TGez3QuZJkZ/fypG8Bm',NULL,0,'2025-08-08 01:13:19',NULL,0,NULL,NULL,NULL,NULL,NULL,0,'2025-08-05 20:35:16','2025-08-08 09:13:19'),(7,'user_1754616685','$2b$12$/PzgNiBCxIpW0RBtmfKhnO1/q/0Pqfpi4YtfZGbXIC5DE1lR38Rwe',NULL,0,'2025-08-08 01:31:34',NULL,0,NULL,NULL,NULL,NULL,NULL,0,'2025-08-08 09:31:26','2025-08-08 09:31:34');
/*!40000 ALTER TABLE `auth_users` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COMMENT='定时任务配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `celery_periodic_task_configs`
--

LOCK TABLES `celery_periodic_task_configs` WRITE;
/*!40000 ALTER TABLE `celery_periodic_task_configs` DISABLE KEYS */;
INSERT INTO `celery_periodic_task_configs` VALUES (3,'agent_health_check','celery_app.agent_tasks.periodic_agent_health_check',1800,NULL,NULL,NULL,NULL,NULL,'[]','{}',1,NULL,0,'2025-07-26 05:57:57','2025-07-26 13:42:25','system','system','每5分钟检查所有智能体的健康状态',NULL),(29,'故事小助手','celery_app.agent_tasks.execute_agent_periodic_task',60,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,'2025-07-27 22:17:43',144,'2025-07-27 06:06:54','2025-07-27 22:18:06',NULL,'system',NULL,'{\"task_type\":\"agent\",\"agent_id\":\"604a64b2-46ca-4f9a-9510-e3eac4716d4b\",\"agent_url\":\"http://192.168.1.10:8000/\",\"message\":\"讲个小狗和嫦娥的故事\",\"user\":\"zhangsan123\",\"task_timeout\":300,\"max_retries\":3}'),(30,'故障诊断定时测试2','celery_app.agent_tasks.execute_agent_periodic_task',60,NULL,NULL,NULL,NULL,NULL,NULL,NULL,1,NULL,0,'2025-07-30 19:34:08','2025-07-30 19:34:08',NULL,NULL,NULL,'{\"task_type\":\"agent\",\"agent_id\":\"diagnostic_agent\",\"agent_url\":\"http://172.20.10.2:8000/\",\"message\":\"你好大黄狗\",\"user\":\"zhangsan123\",\"task_timeout\":300,\"max_retries\":3}');
/*!40000 ALTER TABLE `celery_periodic_task_configs` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=961 DEFAULT CHARSET=utf8mb4 COMMENT='定时任务执行记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `celery_periodic_task_execution_logs`
--

LOCK TABLES `celery_periodic_task_execution_logs` WRITE;
/*!40000 ALTER TABLE `celery_periodic_task_execution_logs` DISABLE KEYS */;
/*!40000 ALTER TABLE `celery_periodic_task_execution_logs` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=1326 DEFAULT CHARSET=utf8mb4 COMMENT='异步任务记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `celery_task_records`
--

LOCK TABLES `celery_task_records` WRITE;
/*!40000 ALTER TABLE `celery_task_records` DISABLE KEYS */;
/*!40000 ALTER TABLE `celery_task_records` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=2813 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `celery_taskmeta`
--

LOCK TABLES `celery_taskmeta` WRITE;
/*!40000 ALTER TABLE `celery_taskmeta` DISABLE KEYS */;
/*!40000 ALTER TABLE `celery_taskmeta` ENABLE KEYS */;
UNLOCK TABLES;

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
-- Dumping data for table `celery_tasksetmeta`
--

LOCK TABLES `celery_tasksetmeta` WRITE;
/*!40000 ALTER TABLE `celery_tasksetmeta` DISABLE KEYS */;
/*!40000 ALTER TABLE `celery_tasksetmeta` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COMMENT='MCP配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mcp_configs`
--

LOCK TABLES `mcp_configs` WRITE;
/*!40000 ALTER TABLE `mcp_configs` DISABLE KEYS */;
INSERT INTO `mcp_configs` VALUES (7,'6563db1c-836c-47a2-977e-feebbd1c1688','db001','dba','[{\"server\": \"db_query_mcp_server\", \"prefix\": \"/gateway/db_query\"}]','[{\"name\": \"db_query_mcp_server\", \"description\": \"获取数据库数据\", \"allowedTools\": [\"list_databases\", \"list_tables\"]}]','[{\"responseBody\": \"{{.Response.Body}}\", \"headers\": {\"Content-Type\": \"application/json\"}, \"name\": \"list_databases\", \"method\": \"POST\", \"endpoint\": \"http1\"}, {\"responseBody\": \"{{.Response.Body}}\", \"headers\": {\"Content-Type\": \"application/json\"}, \"name\": \"list_tables\", \"method\": \"POST\", \"endpoint\": \"http2\"}]','[]','[]',0,'frontend_user','frontend_user','2025-08-01 10:09:53','2025-08-02 12:00:51'),(8,'ab31d49a-7595-47cb-8ecd-88f1ddce40a8','debug-config','default','[{\"server\": \"debug-server\", \"prefix\": \"/gateway/debug\"}]','[{\"name\": \"debug-server\", \"description\": \"测试服务器\", \"allowedTools\": [\"tool1\", \"tool2\"]}]','[{\"name\": \"tool1\", \"method\": \"POST\", \"endpoint\": \"http://localhost:8000/api/v1/test1\"}, {\"name\": \"tool2\", \"method\": \"GET\", \"endpoint\": \"http://localhost:8000/api/v1/test2\"}]','[]','[]',1,'debug_user',NULL,'2025-08-01 10:14:06','2025-08-01 10:14:48'),(9,'03dc3e7c-d2d2-4c57-a74f-385073eb6cbd','systemhaha','default','[{\"server\": \"zabbix_mcp_proxy\", \"prefix\": \"/gateway/zabbix_mcp_proxy\"}, {\"server\": \"es_mcp_proxy\", \"prefix\": \"/gateway/es_mcp_proxy\"}]','[]','[{\"name\": \"systeminfo\", \"method\": \"POST\", \"endpoint\": \"http://172.20.10.2:8000/api/v1/mcp/tools/system_info\", \"requestBody\": \"\", \"responseBody\": \"{{.Response.Body}}\", \"headers\": {\"Content-Type\": \"application/json\"}}, {\"responseBody\": \"{{.Response.Body}}\", \"headers\": {\"Content-Type\": \"application/json\"}, \"name\": \"execute_ssh_command\", \"method\": \"POST\", \"endpoint\": \"http://172.20.10.2:8000/api/v1/mcp/tools/execute_command\"}, {\"name\": \"get_zabbix_metric_data\", \"description\": \"获取指定主机的特定监控指标历史数据\", \"method\": \"POST\", \"endpoint\": \"http://localhost:3005/call_tool\", \"requestBody\": \"{\\\"name\\\": \\\"get_zabbix_metric_data\\\", \\\"arguments\\\": {\\\"ip\\\": \\\"{{.Args.ip}}\\\", \\\"metric_key\\\": \\\"{{.Args.metric_key}}\\\", \\\"start_time\\\": \\\"{{.Args.start_time}}\\\", \\\"end_time\\\": \\\"{{.Args.end_time}}\\\"}}\", \"responseBody\": \"{{.Response.Body}}\", \"headers\": {\"Content-Type\": \"application/json\"}, \"inputSchema\": {\"type\": \"object\", \"properties\": {\"ip\": {\"type\": \"string\", \"default\": \"127.0.0.1\"}, \"metric_key\": {\"type\": \"string\", \"default\": \"system.cpu.util\"}, \"start_time\": {\"type\": \"string\", \"default\": \"\"}, \"end_time\": {\"type\": \"string\", \"default\": \"\"}}}}, {\"name\": \"get_zabbix_metrics\", \"description\": \"获取指定主机的所有可用监控指标\", \"method\": \"POST\", \"endpoint\": \"http://localhost:3005/call_tool\", \"requestBody\": \"{\\\"name\\\": \\\"get_zabbix_metrics\\\", \\\"arguments\\\": {\\\"hostname\\\": \\\"{{.Args.hostname}}\\\"}}\", \"responseBody\": \"{{.Response.Body}}\", \"headers\": {\"Content-Type\": \"application/json\"}, \"inputSchema\": {\"type\": \"object\", \"properties\": {\"hostname\": {\"type\": \"string\", \"default\": \"127.0.0.1\"}}}}]','[]','[{\"type\": \"streamable-http\", \"name\": \"zabbix_mcp_proxy\", \"url\": \"http://localhost:3003/mcp\", \"preinstalled\": false}, {\"type\": \"streamable-http\", \"name\": \"es_mcp_proxy\", \"url\": \"http://localhost:3003/mcp\"}]',0,'test_user','frontend_user','2025-08-01 10:41:52','2025-08-02 17:31:03');
/*!40000 ALTER TABLE `mcp_configs` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COMMENT='MCP服务器配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `mcp_servers`
--

LOCK TABLES `mcp_servers` WRITE;
/*!40000 ALTER TABLE `mcp_servers` DISABLE KEYS */;
INSERT INTO `mcp_servers` VALUES (1,'es-mcp-server','Zabbix监控MCP服务器111','http://172.20.10.2:3004/mcp','streamable-http','提供Zabbix监控数据获取和分析工具','on','disconnected','none',NULL,NULL,5,'[{\"name\": \"get_es_data\", \"description\": \"\\u6267\\u884c\\u81ea\\u5b9a\\u4e49Elasticsearch\\u67e5\\u8be2\\u3002\\u652f\\u6301\\u6307\\u5b9a\\u7d22\\u5f15\\u540d\\u3001\\u65f6\\u95f4\\u8303\\u56f4\\u548c\\u67e5\\u8be2\\u4f53\\u3002\\n\\nArgs:\\n    index_name: \\u7d22\\u5f15\\u540d\\u79f0\\n    start_time: \\u5f00\\u59cb\\u65f6\\u95f4\\uff0c\\u683c\\u5f0f\\uff1a\\u5e74-\\u6708-\\u65e5 \\u65f6:\\u5206:\\u79d2\\n    end_time: \\u7ed3\\u675f\\u65f6\\u95f4\\uff0c\\u683c\\u5f0f\\uff1a\\u5e74-\\u6708-\\u65e5 \\u65f6:\\u5206:\\u79d2\\n    query_body: \\u81ea\\u5b9a\\u4e49\\u67e5\\u8be2\\u4f53\\uff0c\\u5982\\u679c\\u4e3a\\u7a7a\\u5219\\u751f\\u6210\\u9ed8\\u8ba4\\u67e5\\u8be2\\n\\nReturns:\\n    \\u5305\\u542b\\u67e5\\u8be2\\u7ed3\\u679c\\u7684JSON\\u5b57\\u7b26\\u4e32\", \"globalEnabled\": true, \"category\": \"unknown\", \"parameters\": {\"properties\": {\"index_name\": {\"title\": \"Index Name\", \"type\": \"string\"}, \"start_time\": {\"title\": \"Start Time\", \"type\": \"string\"}, \"end_time\": {\"title\": \"End Time\", \"type\": \"string\"}, \"query_body\": {\"anyOf\": [{\"additionalProperties\": true, \"type\": \"object\"}, {\"type\": \"null\"}], \"default\": null, \"title\": \"Query Body\"}}, \"required\": [\"index_name\", \"start_time\", \"end_time\"], \"type\": \"object\"}}, {\"name\": \"get_es_trends_data\", \"description\": \"\\u83b7\\u53d6ES\\u8d8b\\u52bf\\u6570\\u636e\\u3002\\u7528\\u4e8e\\u5206\\u6790\\u6307\\u5b9a\\u65f6\\u95f4\\u8303\\u56f4\\u5185\\u6570\\u636e\\u7684\\u8d8b\\u52bf\\u53d8\\u5316\\u3002\\n\\nArgs:\\n    index_name: \\u7d22\\u5f15\\u540d\\u79f0\\n    start_time: \\u5f00\\u59cb\\u65f6\\u95f4\\uff0c\\u683c\\u5f0f\\uff1a\\u5e74-\\u6708-\\u65e5 \\u65f6:\\u5206:\\u79d2\\n    end_time: \\u7ed3\\u675f\\u65f6\\u95f4\\uff0c\\u683c\\u5f0f\\uff1a\\u5e74-\\u6708-\\u65e5 \\u65f6:\\u5206:\\u79d2\\n    field: \\u7528\\u4e8e\\u7edf\\u8ba1\\u8d8b\\u52bf\\u7684\\u5b57\\u6bb5\\n    interval: \\u65f6\\u95f4\\u95f4\\u9694\\uff0c\\u5982: 1m, 5m, 1h, 1d\\n\\nReturns:\\n    \\u5305\\u542b\\u8d8b\\u52bf\\u6570\\u636e\\u7684JSON\\u5b57\\u7b26\\u4e32\", \"globalEnabled\": true, \"category\": \"unknown\", \"parameters\": {\"properties\": {\"index_name\": {\"title\": \"Index Name\", \"type\": \"string\"}, \"start_time\": {\"title\": \"Start Time\", \"type\": \"string\"}, \"end_time\": {\"title\": \"End Time\", \"type\": \"string\"}, \"field\": {\"title\": \"Field\", \"type\": \"string\"}, \"interval\": {\"default\": \"1h\", \"title\": \"Interval\", \"type\": \"string\"}}, \"required\": [\"index_name\", \"start_time\", \"end_time\", \"field\"], \"type\": \"object\"}}, {\"name\": \"get_es_indices\", \"description\": \"\\u83b7\\u53d6Elasticsearch\\u6240\\u6709\\u7d22\\u5f15\\u5217\\u8868\\u3002\\u7528\\u4e8e\\u67e5\\u770b\\u53ef\\u7528\\u7684\\u7d22\\u5f15\\u3002\\n\\nReturns:\\n    \\u5305\\u542b\\u7d22\\u5f15\\u5217\\u8868\\u7684JSON\\u5b57\\u7b26\\u4e32\", \"globalEnabled\": true, \"category\": \"unknown\", \"parameters\": {\"properties\": {}, \"type\": \"object\"}}]','{}','default_team','admin','system','2025-07-23 00:55:21','2025-08-06 22:03:38'),(2,'db-mcp-server','SSH工具MCP服务器','http://172.20.10.2:3002/sse','sse','提供SSH远程系统管理和诊断工具','on','disconnected','none',NULL,NULL,5,'[{\"name\": \"execute_mysql_query\", \"description\": \"\\u6267\\u884c\\u8bca\\u65adSQL\\u67e5\\u8be2\\u3002\\u7528\\u4e8e\\u6267\\u884c\\u81ea\\u5b9a\\u4e49\\u7684\\u6570\\u636e\\u5e93\\u8bca\\u65ad\\u67e5\\u8be2\\u3002\\n\\nArgs:\\n    connection_name: MySQL\\u8fde\\u63a5\\u540d\\u79f0\\n    query: SQL\\u67e5\\u8be2\\u8bed\\u53e5\\n    limit: \\u7ed3\\u679c\\u9650\\u5236\\u6570\\u91cf\\n\\nReturns:\\n    \\u5305\\u542b\\u67e5\\u8be2\\u7ed3\\u679c\\u7684JSON\\u5b57\\u7b26\\u4e32\", \"globalEnabled\": true, \"category\": \"unknown\", \"parameters\": {\"properties\": {\"connection_name\": {\"default\": \"default\", \"title\": \"Connection Name\", \"type\": \"string\"}, \"query\": {\"default\": \"\", \"title\": \"Query\", \"type\": \"string\"}, \"limit\": {\"default\": 100, \"title\": \"Limit\", \"type\": \"integer\"}}, \"type\": \"object\"}}]','{}','default_team','admin','system','2025-07-23 00:54:42','2025-08-06 22:03:52'),(3,'zabbix-mcp-server','Zabbix监控MCP服务器111','http://172.20.10.2:3004/mcp','streamable-http','提供Zabbix监控数据获取和分析工具','on','disconnected','none',NULL,NULL,5,'[]','{}','default_team','admin','system','2025-07-23 00:55:38','2025-08-06 22:03:24'),(4,'ssh-mcp-server','Elasticsearch工具MCP服务器','http://172.20.10.2:3003/mcp','streamable-http','提供Elasticsearch查询和分析工具','on','disconnected','none',NULL,NULL,5,'[]','{}','default_team','admin','system','2025-07-23 00:54:55','2025-08-06 22:03:44');
/*!40000 ALTER TABLE `mcp_servers` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=46 DEFAULT CHARSET=utf8 COMMENT='菜单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rbac_menus`
--

LOCK TABLES `rbac_menus` WRITE;
/*!40000 ALTER TABLE `rbac_menus` DISABLE KEYS */;
INSERT INTO `rbac_menus` VALUES (4,4,'系统管理','Setting',1,'/system','/system/ai/agents','',1,0,'2025-08-04 14:46:17','2025-08-08 09:10:42','admin','admin',20),(7,1,'首页','Home',-1,'/','','HomePage',1,0,'2025-08-04 14:54:00','2025-08-06 15:39:39','admin','admin',0),(9,5,'用户服务','Info',1,'/service','/service/agents','',1,0,'2025-08-04 15:04:06','2025-08-08 09:10:42','admin','admin',1),(10,6,'智能体广场','lucide:crown',5,'/service/agents','','AgentMarketplace',1,0,'2025-08-04 15:04:21','2025-08-08 09:08:18','admin','admin',10),(11,7,'知识中心','Book',5,'/service/knowledge','','KnowledgeManagement',1,0,'2025-08-04 15:54:57','2025-08-08 09:08:18','admin','admin',100),(30,8,'智能体管理','Bot',21,'/system/ai/agents','','AgentManagement',1,0,'2025-08-04 18:32:59','2025-08-08 09:08:18','admin','admin',10),(32,10,'MCP管理','lucide:server',21,'/system/ai/mcp','','MCPManagement',1,0,'2025-08-04 18:33:03','2025-08-08 09:08:18','admin','admin',2),(33,11,'用户权限管理','User',4,'/system/userPermission','/system/permission/users','',1,0,'2025-08-04 18:39:57','2025-08-08 09:10:42','admin','admin',1),(35,12,'用户管理','lucide:user',11,'/system/userPermission/users','','UserManagement',1,0,'2025-08-04 18:42:31','2025-08-08 09:08:18','admin','admin',10),(36,13,'角色管理','lucide:package',11,'/system/permission/roles','','RoleManagement',1,0,'2025-08-04 18:43:39','2025-08-08 09:08:18','admin','admin',3),(37,14,'菜单管理','Menu',11,'/system/userPermission/menu','','MenuManagement',1,0,'2025-08-04 18:44:22','2025-08-08 09:08:18','admin','admin',5),(38,15,'权限管理','lucide:star',11,'/system/userPermission/permission','','PermissionManagement',1,0,'2025-08-04 18:45:21','2025-08-08 09:08:18','admin','admin',4),(40,16,'任务管理','Clock',21,'/system/ai/tasks','','TasksManagement',1,0,'2025-08-04 18:50:34','2025-08-08 09:08:18','admin','admin',40),(41,17,'模型管理','lucide:brain',21,'/system/ai/models','','ModelsManagement',1,0,'2025-08-04 18:51:47','2025-08-08 09:08:18','admin','admin',1),(43,19,'知识管理','Book',4,'/system/kb','/system/kb/sop','',1,0,'2025-08-04 19:04:30','2025-08-08 09:10:42','admin','admin',5),(44,20,'SOP管理','lucide:book',19,'/system/kb/sop','','SOPList',1,0,'2025-08-04 19:05:37','2025-08-08 09:08:18','admin','admin',10),(45,21,'AI管理','Robot',4,'/system/ai','/system/ai/agents','',1,0,'2025-08-05 07:51:58','2025-08-08 09:10:42','admin','admin',2);
/*!40000 ALTER TABLE `rbac_menus` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=881 DEFAULT CHARSET=utf8 COMMENT='api权限表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rbac_permissions`
--

LOCK TABLES `rbac_permissions` WRITE;
/*!40000 ALTER TABLE `rbac_permissions` DISABLE KEYS */;
INSERT INTO `rbac_permissions` VALUES (760,1,'用户登录 (POST)','/api/v1/auth/login','POST','off',NULL,0,'2025-08-05 13:26:26','2025-08-05 13:26:26','api_scanner','api_scanner'),(761,2,'用户注册 (POST)','/api/v1/auth/register','POST','off',NULL,0,'2025-08-05 13:26:26','2025-08-05 13:26:26','api_scanner','api_scanner'),(762,3,'刷新访问令牌 (POST)','/api/v1/auth/refresh','POST','off',NULL,0,'2025-08-05 13:26:26','2025-08-05 13:26:26','api_scanner','api_scanner'),(763,4,'用户登出 (POST)','/api/v1/auth/logout','POST','off',NULL,0,'2025-08-05 13:26:26','2025-08-05 13:26:26','api_scanner','api_scanner'),(764,5,'获取当前用户信息 (GET)','/api/v1/auth/me','GET','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(765,6,'获取当前用户权限 (GET)','/api/v1/auth/me/permissions','GET','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(766,7,'验证令牌 (POST)','/api/v1/auth/verify','POST','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(767,8,'获取SSO提供商列表 (GET)','/api/v1/auth/sso/providers','GET','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(768,9,'获取SSO登录URL (GET)','/api/v1/auth/sso/url','GET','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(769,10,'SSO回调处理 (POST)','/api/v1/auth/sso/callback','POST','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(770,11,'修改密码 (POST)','/api/v1/auth/change-password','POST','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(771,12,'忘记密码 (POST)','/api/v1/auth/forgot-password','POST','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(772,13,'重置密码 (POST)','/api/v1/auth/reset-password','POST','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(773,14,'启用MFA (POST)','/api/v1/auth/mfa/enable','POST','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(774,15,'验证MFA设置 (POST)','/api/v1/auth/mfa/verify','POST','off',NULL,0,'2025-08-05 13:26:27','2025-08-05 13:26:27','api_scanner','api_scanner'),(775,16,'禁用MFA (POST)','/api/v1/auth/mfa/disable','POST','off',NULL,0,'2025-08-05 13:26:28','2025-08-05 13:26:28','api_scanner','api_scanner'),(776,17,'创建API密钥 (POST)','/api/v1/auth/api-keys','POST','off',NULL,0,'2025-08-05 13:26:28','2025-08-05 13:26:28','api_scanner','api_scanner'),(777,18,'获取API密钥列表 (GET)','/api/v1/auth/api-keys','GET','off',NULL,0,'2025-08-05 13:26:28','2025-08-05 13:26:28','api_scanner','api_scanner'),(778,19,'撤销API密钥 (DELETE)','/api/v1/auth/api-keys/{key_id}','DELETE','off',NULL,0,'2025-08-05 13:26:28','2025-08-05 13:26:28','api_scanner','api_scanner'),(779,20,'获取活跃会话 (GET)','/api/v1/auth/sessions','GET','off',NULL,0,'2025-08-05 13:26:28','2025-08-05 13:26:28','api_scanner','api_scanner'),(780,21,'终止会话 (POST)','/api/v1/auth/sessions/terminate','POST','off',NULL,0,'2025-08-05 13:26:28','2025-08-05 13:26:28','api_scanner','api_scanner'),(781,22,'检查权限 (POST)','/api/v1/auth/permissions/check','POST','off',NULL,0,'2025-08-05 13:26:28','2025-08-05 13:26:28','api_scanner','api_scanner'),(782,23,'获取菜单列表 (GET)','/api/v1/auth/admin/menus','GET','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(783,24,'获取父菜单选项 (GET)','/api/v1/auth/admin/menus/parent-options','GET','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(784,25,'创建菜单 (POST)','/api/v1/auth/admin/menus','POST','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(785,26,'获取菜单详情 (GET)','/api/v1/auth/admin/menus/{menu_id}','GET','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(786,27,'更新菜单 (PUT)','/api/v1/auth/admin/menus/{menu_id}','PUT','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(787,28,'删除菜单 (DELETE)','/api/v1/auth/admin/menus/{menu_id}','DELETE','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(788,29,'获取当前用户菜单 (GET)','/api/v1/auth/me/menus','GET','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(789,30,'更新菜单排序 (PUT)','/api/v1/auth/admin/menus/{menu_id}/sort','PUT','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(790,31,'初始化管理员账户 (POST)','/api/v1/auth/init/admin','POST','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(791,32,'POST /api/v1/agents','/api/v1/agents','POST','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(792,33,'GET /api/v1/agents','/api/v1/agents','GET','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(793,34,'GET /api/v1/agents/{agent_id}','/api/v1/agents/{agent_id}','GET','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(794,35,'PUT /api/v1/agents/{agent_id}','/api/v1/agents/{agent_id}','PUT','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(795,36,'DELETE /api/v1/agents/{agent_id}','/api/v1/agents/{agent_id}','DELETE','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(796,37,'PUT /api/v1/agents/{agent_id}/mcp-config','/api/v1/agents/{agent_id}/mcp-config','PUT','off',NULL,0,'2025-08-05 13:26:29','2025-08-05 13:26:29','api_scanner','api_scanner'),(797,38,'PUT /api/v1/agents/{agent_id}/status','/api/v1/agents/{agent_id}/status','PUT','off',NULL,0,'2025-08-05 13:26:30','2025-08-05 13:26:30','api_scanner','api_scanner'),(798,39,'PUT /api/v1/agents/{agent_id}/statistics','/api/v1/agents/{agent_id}/statistics','PUT','off',NULL,0,'2025-08-05 13:26:30','2025-08-05 13:26:30','api_scanner','api_scanner'),(799,40,'GET /api/v1/agents/meta/statistics','/api/v1/agents/meta/statistics','GET','off',NULL,0,'2025-08-05 13:26:30','2025-08-05 13:26:30','api_scanner','api_scanner'),(800,41,'GET /api/v1/agents/search','/api/v1/agents/search','GET','off',NULL,0,'2025-08-05 13:26:30','2025-08-05 13:26:30','api_scanner','api_scanner'),(801,42,'POST /api/chat/threads','/api/chat/threads','POST','off',NULL,0,'2025-08-05 13:26:30','2025-08-05 13:26:30','api_scanner','api_scanner'),(802,43,'POST /api/chat/threads/{thread_id}/history','/api/chat/threads/{thread_id}/history','POST','off',NULL,0,'2025-08-05 13:26:30','2025-08-05 13:26:30','api_scanner','api_scanner'),(803,44,'POST /api/chat/threads/{thread_id}/runs/stream','/api/chat/threads/{thread_id}/runs/stream','POST','off',NULL,0,'2025-08-05 13:26:30','2025-08-05 13:26:30','api_scanner','api_scanner'),(804,45,'GET /api/chat/users/{user_name}/threads','/api/chat/users/{user_name}/threads','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(805,46,'POST /api/v1/sops','/api/v1/sops','POST','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(806,47,'GET /api/v1/sops/{sop_id}','/api/v1/sops/{sop_id}','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(807,48,'GET /api/v1/sops','/api/v1/sops','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(808,49,'PUT /api/v1/sops/{sop_id}','/api/v1/sops/{sop_id}','PUT','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(809,50,'DELETE /api/v1/sops/{sop_id}','/api/v1/sops/{sop_id}','DELETE','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(810,51,'GET /api/v1/sops/meta/categories','/api/v1/sops/meta/categories','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(811,52,'GET /api/v1/sops/meta/teams','/api/v1/sops/meta/teams','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(812,53,'GET /api/v1/sops/meta/severity','/api/v1/sops/meta/severity','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(813,54,'GET /api/v1/sops/meta/statistics','/api/v1/sops/meta/statistics','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(814,55,'POST /api/v1/mcp/servers','/api/v1/mcp/servers','POST','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(815,56,'GET /api/v1/mcp/servers/{server_id}','/api/v1/mcp/servers/{server_id}','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(816,57,'GET /api/v1/mcp/servers','/api/v1/mcp/servers','GET','off',NULL,0,'2025-08-05 13:26:31','2025-08-05 13:26:31','api_scanner','api_scanner'),(817,58,'PUT /api/v1/mcp/servers/{server_id}','/api/v1/mcp/servers/{server_id}','PUT','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(818,59,'DELETE /api/v1/mcp/servers/{server_id}','/api/v1/mcp/servers/{server_id}','DELETE','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(819,60,'PATCH /api/v1/mcp/servers/{server_id}/status','/api/v1/mcp/servers/{server_id}/status','PATCH','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(820,61,'PATCH /api/v1/mcp/servers/{server_id}/enable','/api/v1/mcp/servers/{server_id}/enable','PATCH','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(821,62,'GET /api/v1/mcp/servers/meta/teams','/api/v1/mcp/servers/meta/teams','GET','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(822,63,'GET /api/v1/mcp/servers/meta/statistics','/api/v1/mcp/servers/meta/statistics','GET','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(823,64,'POST /api/v1/mcp/test','/api/v1/mcp/test','POST','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(824,65,'POST /api/v1/mcp/tools/system_info','/api/v1/mcp/tools/system_info','POST','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(825,66,'POST /api/v1/mcp/tools/execute_command','/api/v1/mcp/tools/execute_command','POST','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(826,67,'GET /api/v1/mcp/tools/list_files','/api/v1/mcp/tools/list_files','GET','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(827,68,'GET /api/v1/mcp/gateway/configs/real','/api/v1/mcp/gateway/configs/real','GET','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(828,69,'GET /api/v1/mcp/gateway/configs/all','/api/v1/mcp/gateway/configs/all','GET','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(829,70,'POST /api/v1/mcp/gateway/configs','/api/v1/mcp/gateway/configs','POST','off',NULL,0,'2025-08-05 13:26:32','2025-08-05 13:26:32','api_scanner','api_scanner'),(830,71,'GET /api/v1/mcp/gateway/configs','/api/v1/mcp/gateway/configs','GET','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(831,72,'GET /api/v1/mcp/gateway/configs/{config_id}','/api/v1/mcp/gateway/configs/{config_id}','GET','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(832,73,'PUT /api/v1/mcp/gateway/configs/{config_id}','/api/v1/mcp/gateway/configs/{config_id}','PUT','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(833,74,'DELETE /api/v1/mcp/gateway/configs/{config_id}','/api/v1/mcp/gateway/configs/{config_id}','DELETE','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(834,75,'POST /api/v1/ai-models','/api/v1/ai-models','POST','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(835,76,'GET /api/v1/ai-models/{model_id}','/api/v1/ai-models/{model_id}','GET','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(836,77,'GET /api/v1/ai-models','/api/v1/ai-models','GET','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(837,78,'PUT /api/v1/ai-models/{model_id}','/api/v1/ai-models/{model_id}','PUT','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(838,79,'DELETE /api/v1/ai-models/{model_id}','/api/v1/ai-models/{model_id}','DELETE','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(839,80,'POST /api/v1/ai-models/test-connection','/api/v1/ai-models/test-connection','POST','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(840,81,'POST /api/v1/ai-models/discover-ollama','/api/v1/ai-models/discover-ollama','POST','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(841,82,'PATCH /api/v1/ai-models/{model_id}/status','/api/v1/ai-models/{model_id}/status','PATCH','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(842,83,'GET /api/v1/ai-models/meta/providers','/api/v1/ai-models/meta/providers','GET','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(843,84,'GET /api/v1/ai-models/meta/types','/api/v1/ai-models/meta/types','GET','off',NULL,0,'2025-08-05 13:26:33','2025-08-05 13:26:33','api_scanner','api_scanner'),(844,85,'GET /api/v1/ai-models/meta/statistics','/api/v1/ai-models/meta/statistics','GET','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(845,86,'GET /api/v1/scheduled-tasks/records','/api/v1/scheduled-tasks/records','GET','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(846,87,'GET /api/v1/scheduled-tasks/meta/statistics','/api/v1/scheduled-tasks/meta/statistics','GET','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(847,88,'GET /api/v1/scheduled-tasks','/api/v1/scheduled-tasks','GET','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(848,89,'POST /api/v1/scheduled-tasks','/api/v1/scheduled-tasks','POST','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(849,90,'GET /api/v1/scheduled-tasks/records/{record_id}','/api/v1/scheduled-tasks/records/{record_id}','GET','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(850,91,'GET /api/v1/scheduled-tasks/{task_id}/logs','/api/v1/scheduled-tasks/{task_id}/logs','GET','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(851,92,'POST /api/v1/scheduled-tasks/{task_id}/enable','/api/v1/scheduled-tasks/{task_id}/enable','POST','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(852,93,'POST /api/v1/scheduled-tasks/{task_id}/disable','/api/v1/scheduled-tasks/{task_id}/disable','POST','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(853,94,'POST /api/v1/scheduled-tasks/{task_id}/trigger','/api/v1/scheduled-tasks/{task_id}/trigger','POST','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(854,95,'GET /api/v1/scheduled-tasks/{task_id}','/api/v1/scheduled-tasks/{task_id}','GET','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(855,96,'PUT /api/v1/scheduled-tasks/{task_id}','/api/v1/scheduled-tasks/{task_id}','PUT','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(856,97,'DELETE /api/v1/scheduled-tasks/{task_id}','/api/v1/scheduled-tasks/{task_id}','DELETE','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(857,98,'POST /api/v1/rbac/users','/api/v1/rbac/users','POST','off',NULL,0,'2025-08-05 13:26:34','2025-08-05 13:26:34','api_scanner','api_scanner'),(858,99,'GET /api/v1/rbac/users/{user_id}','/api/v1/rbac/users/{user_id}','GET','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(859,100,'GET /api/v1/rbac/users','/api/v1/rbac/users','GET','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(860,101,'PUT /api/v1/rbac/users/{user_id}','/api/v1/rbac/users/{user_id}','PUT','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(861,102,'DELETE /api/v1/rbac/users/{user_id}','/api/v1/rbac/users/{user_id}','DELETE','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(862,103,'POST /api/v1/rbac/roles','/api/v1/rbac/roles','POST','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(863,104,'GET /api/v1/rbac/roles/{role_id}','/api/v1/rbac/roles/{role_id}','GET','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(864,105,'GET /api/v1/rbac/roles','/api/v1/rbac/roles','GET','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(865,106,'PUT /api/v1/rbac/roles/{role_id}','/api/v1/rbac/roles/{role_id}','PUT','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(866,107,'DELETE /api/v1/rbac/roles/{role_id}','/api/v1/rbac/roles/{role_id}','DELETE','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(867,108,'POST /api/v1/rbac/permissions','/api/v1/rbac/permissions','POST','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(868,109,'GET /api/v1/rbac/permissions/{permission_id}','/api/v1/rbac/permissions/{permission_id}','GET','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(869,110,'GET /api/v1/rbac/permissions','/api/v1/rbac/permissions','GET','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(870,111,'PUT /api/v1/rbac/permissions/{permission_id}','/api/v1/rbac/permissions/{permission_id}','PUT','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(871,112,'DELETE /api/v1/rbac/permissions/{permission_id}','/api/v1/rbac/permissions/{permission_id}','DELETE','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(872,113,'POST /api/v1/rbac/menus','/api/v1/rbac/menus','POST','off',NULL,0,'2025-08-05 13:26:35','2025-08-05 13:26:35','api_scanner','api_scanner'),(873,114,'GET /api/v1/rbac/menus/{menu_id}','/api/v1/rbac/menus/{menu_id}','GET','off',NULL,0,'2025-08-05 13:26:36','2025-08-05 13:26:36','api_scanner','api_scanner'),(874,115,'GET /api/v1/rbac/menus','/api/v1/rbac/menus','GET','off',NULL,0,'2025-08-05 13:26:36','2025-08-05 13:26:36','api_scanner','api_scanner'),(875,116,'PUT /api/v1/rbac/menus/{menu_id}','/api/v1/rbac/menus/{menu_id}','PUT','off',NULL,0,'2025-08-05 13:26:36','2025-08-05 13:26:36','api_scanner','api_scanner'),(876,117,'DELETE /api/v1/rbac/menus/{menu_id}','/api/v1/rbac/menus/{menu_id}','DELETE','off',NULL,0,'2025-08-05 13:26:36','2025-08-05 13:26:36','api_scanner','api_scanner'),(878,118,'xxxx','xxx','GET','off',NULL,1,'2025-08-05 14:11:06','2025-08-05 14:11:11','system','system'),(879,119,'GET /api/v1/rbac/roles/{role_id}/permissions','/api/v1/rbac/roles/{role_id}/permissions','GET','off',NULL,0,'2025-08-05 14:34:08','2025-08-05 14:34:08','api_scanner','api_scanner'),(880,120,'GET /api/v1/rbac/roles/{role_id}/debug','/api/v1/rbac/roles/{role_id}/debug','GET','off',NULL,0,'2025-08-05 15:12:16','2025-08-05 15:12:16','api_scanner','api_scanner');
/*!40000 ALTER TABLE `rbac_permissions` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8 COMMENT='角色表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rbac_roles`
--

LOCK TABLES `rbac_roles` WRITE;
/*!40000 ALTER TABLE `rbac_roles` DISABLE KEYS */;
INSERT INTO `rbac_roles` VALUES (1,1,'超级管理员','系统最高权限管理员，拥有所有系统功能的完全控制权，包括系统配置、用户管理、数据管理等全部权限',0,'2025-08-03 20:21:45','2025-08-05 14:44:33','system','system'),(2,2,'安全管理员','负责系统安全管理，包括用户权限管理、安全策略配置、访问控制、安全事件监控和响应',0,'2025-08-03 20:21:45','2025-08-03 20:21:45','system','system'),(3,3,'审计人员','负责系统审计监督，拥有所有操作日志的只读权限，进行合规检查、异常行为分析和审计报告生成',0,'2025-08-03 20:21:45','2025-08-03 20:21:45','system','system'),(4,4,'普通用户','标准业务用户，拥有业务功能的正常操作权限，可以进行日常业务操作和数据查看',0,'2025-08-03 20:21:45','2025-08-03 20:21:45','system','system'),(5,5,'匿名用户','未登录或访客用户，只能访问公开信息和基础功能，具有最小化的系统访问权限',0,'2025-08-03 20:21:45','2025-08-03 20:21:45','system','system');
/*!40000 ALTER TABLE `rbac_roles` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=2037 DEFAULT CHARSET=utf8 COMMENT='角色-权限关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rbac_roles_permissions`
--

LOCK TABLES `rbac_roles_permissions` WRITE;
/*!40000 ALTER TABLE `rbac_roles_permissions` DISABLE KEYS */;
INSERT INTO `rbac_roles_permissions` VALUES (15,2,2001,2001,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(16,2,2002,2002,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(17,2,2003,2003,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(18,2,3001,3001,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(19,2,5001,5001,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(20,2,5002,5002,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(21,2,5003,5003,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(22,3,3001,3001,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(23,3,3002,3002,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(24,3,3003,3003,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(25,3,5001,5001,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(26,3,5002,5002,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(27,3,5003,5003,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(28,4,4001,4001,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(29,4,4002,4002,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(30,4,4003,4003,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(31,4,5001,5001,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(32,4,5002,5002,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(33,4,5003,5003,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(34,5,5001,5001,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(35,5,5002,5002,1,0,'2025-08-03 20:22:43','2025-08-03 20:22:43','system','system'),(1900,1,1,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1901,1,2,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1902,1,3,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1903,1,4,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1904,1,5,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1905,1,6,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1906,1,7,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1907,1,8,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1908,1,9,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1909,1,10,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1910,1,11,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1911,1,12,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1912,1,13,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1913,1,14,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1914,1,15,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1915,1,16,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1916,1,17,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1917,1,18,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1918,1,19,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1919,1,20,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1920,1,21,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1921,1,22,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1922,1,23,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1923,1,24,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1924,1,25,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1925,1,26,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1926,1,27,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1927,1,28,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1928,1,29,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1929,1,30,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1930,1,31,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1931,1,32,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1932,1,33,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1933,1,34,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1934,1,35,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1935,1,36,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1936,1,37,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1937,1,38,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1938,1,39,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1939,1,40,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1940,1,41,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1941,1,42,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1942,1,43,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1943,1,44,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1944,1,45,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1945,1,46,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1946,1,47,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1947,1,48,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1948,1,49,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1949,1,50,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1950,1,51,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1951,1,52,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1952,1,53,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1953,1,54,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1954,1,55,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1955,1,56,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1956,1,57,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1957,1,58,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1958,1,59,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1959,1,60,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1960,1,61,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1961,1,62,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1962,1,63,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1963,1,64,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1964,1,65,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1965,1,66,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1966,1,67,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1967,1,68,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1968,1,69,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1969,1,70,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1970,1,71,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1971,1,72,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1972,1,73,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1973,1,74,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1974,1,75,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1975,1,76,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1976,1,77,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1977,1,78,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1978,1,79,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1979,1,80,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1980,1,81,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1981,1,82,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1982,1,83,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1983,1,84,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1984,1,85,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1985,1,86,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1986,1,87,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1987,1,88,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1988,1,89,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1989,1,90,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1990,1,91,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1991,1,92,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1992,1,93,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1993,1,94,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1994,1,95,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1995,1,96,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1996,1,97,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1997,1,98,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1998,1,99,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(1999,1,100,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2000,1,101,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2001,1,102,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2002,1,103,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2003,1,104,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2004,1,105,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2005,1,106,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2006,1,107,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2007,1,108,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2008,1,109,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2009,1,110,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2010,1,111,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2011,1,112,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2012,1,113,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2013,1,114,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2014,1,115,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2015,1,116,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2016,1,117,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2017,1,118,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2018,1,119,-1,2,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2019,1,-1,1,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2020,1,-1,4,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2021,1,-1,5,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2022,1,-1,6,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2023,1,-1,7,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2024,1,-1,8,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2025,1,-1,10,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2026,1,-1,11,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2027,1,-1,12,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2028,1,-1,13,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2029,1,-1,14,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2030,1,-1,15,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2031,1,-1,16,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2032,1,-1,17,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2033,1,-1,18,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2034,1,-1,19,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2035,1,-1,20,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system'),(2036,1,-1,21,1,0,'2025-08-05 14:44:34','2025-08-05 14:44:34','system','system');
/*!40000 ALTER TABLE `rbac_roles_permissions` ENABLE KEYS */;
UNLOCK TABLES;

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
  `user_source` tinyint(1) NOT NULL DEFAULT '3' COMMENT '用户来源,1-->cas,2-->jwt',
  `is_active` tinyint(1) NOT NULL DEFAULT '1' COMMENT '用户是否活跃,1活跃,0冻结',
  `is_deleted` tinyint(4) NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `create_by` varchar(50) NOT NULL DEFAULT '' COMMENT '创建人',
  `update_by` varchar(50) NOT NULL DEFAULT '' COMMENT '更新人',
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  UNIQUE KEY `user_name` (`user_name`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8 COMMENT='用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rbac_users`
--

LOCK TABLES `rbac_users` WRITE;
/*!40000 ALTER TABLE `rbac_users` DISABLE KEYS */;
INSERT INTO `rbac_users` VALUES (7,'user_1754397315','gaochao','高超','默认部门','普通用户','123474213@qq.com','1888888888888',3,1,0,'2025-08-05 20:35:16','2025-08-06 12:47:18','system','system'),(8,'user_1754616685','zhangsan','张三','默认部门','普通用户','123474214@qq.com','',3,1,0,'2025-08-08 09:31:26','2025-08-08 09:31:26','system','system');
/*!40000 ALTER TABLE `rbac_users` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8 COMMENT='用户-角色关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `rbac_users_roles`
--

LOCK TABLES `rbac_users_roles` WRITE;
/*!40000 ALTER TABLE `rbac_users_roles` DISABLE KEYS */;
INSERT INTO `rbac_users_roles` VALUES (29,'user_1754397315',1,0,'2025-08-06 12:47:18','2025-08-06 12:47:18','system','system'),(30,'user_1754397315',2,0,'2025-08-06 12:47:18','2025-08-06 12:47:18','system','system');
/*!40000 ALTER TABLE `rbac_users_roles` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COMMENT='SOP标准操作程序模板表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `sop_prompt_templates`
--

LOCK TABLES `sop_prompt_templates` WRITE;
/*!40000 ALTER TABLE `sop_prompt_templates` DISABLE KEYS */;
INSERT INTO `sop_prompt_templates` VALUES (4,'SOP-DB-001','MySQL数据库响应耗时升高诊断','database','诊断MySQL数据库响应时间过长的标准操作程序','high','[{\"args\": \"SHOW VARIABLES WHERE Variable_name IN (long_query_time, slow_query_log);\", \"step\": 1, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"获取慢查询日志配置和阈值设置\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"根据用户描述的响应耗时和慢查询阈值，确定分析范围，如果用户告诉了范围用用户的，否则用报警时间前后5分钟\", \"step\": 2, \"tool\": \"llm\", \"timeout\": null, \"on_failure\": null, \"description\": \"确定分析范围\", \"retry_count\": null, \"ai_generated\": true, \"requires_approval\": false}, {\"args\": \"如果响应耗时小于慢查询阈值则跳过慢日志分析直接执行第5步，如果大于阈值则继续第4步\", \"step\": 3, \"tool\": \"llm\", \"timeout\": null, \"on_failure\": null, \"description\": \"大模型判断是否需要分析慢查询日志\", \"retry_count\": null, \"ai_generated\": true, \"requires_approval\": false}, {\"args\": \"index: mysql-slow-*, start_time: 动态生成, end_time: 动态生成, query: 动态生成,获取一条数据看看有哪些字段然后生成\", \"step\": 4, \"tool\": \"get_es_data\", \"timeout\": null, \"on_failure\": null, \"description\": \"从ES中查询指定时间范围的慢查询日志，分析是写慢查询还是读慢查询，查看扫描行数和锁等待情况\", \"retry_count\": null, \"ai_generated\": true, \"requires_approval\": false}, {\"args\": \"metric: [system.cpu.util[,user], disk.io.util[vda]], start_time: 动态生成, end_time: 动态生成\", \"step\": 5, \"tool\": \"get_zabbix_metric_data\", \"timeout\": null, \"on_failure\": null, \"description\": \"获取指定时间范围内的磁盘IO使用率和CPU使用率，检查是否存在瓶颈或异常波动\", \"retry_count\": null, \"ai_generated\": true, \"requires_approval\": false}, {\"args\": \"top -b -n1 | head -12; iotop -b -n1 | head -10\", \"step\": 6, \"tool\": \"execute_system_command\", \"timeout\": null, \"on_failure\": null, \"description\": \"如果CPU或者磁盘IO有瓶颈且当前仍然存在瓶颈，则排查CPU和IO占用前5名进程\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"查看对应的会话id是否继续在执行慢查询，如果继续执行则kill\", \"step\": 7, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"故障自愈\", \"retry_count\": null, \"ai_generated\": true, \"requires_approval\": false}]','[\"execute_mysql_query\", \"get_es_data\", \"get_zabbix_metric_data\", \"execute_system_command\", \"llm\"]','建议优化识别到的慢查询SQL，为高频查询字段添加索引，重构复杂查询，联系DBA进行查询优化','ops-team','admin','admin','2025-07-22 05:34:23','2025-07-24 06:43:44'),(5,'SOP-DB-002','MySQL连接数过多诊断11333','database','诊断MySQL连接数过多等问题','high','[{\"args\": \"SHOW STATUS LIKE Threads_connected;\", \"step\": 1, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"查看当前活跃连接数量\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"SHOW VARIABLES LIKE max_connections;\", \"step\": 2, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"确认最大连接数限制\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"SELECT USER, HOST, COUNT(*) FROM information_schema.PROCESSLIST GROUP BY USER, HOST;\", \"step\": 3, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"分析连接来源分布\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"SELECT COMMAND, COUNT(*) FROM information_schema.PROCESSLIST GROUP BY COMMAND;\", \"step\": 4, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"分析连接状态分布\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"SELECT ID, USER, HOST, TIME, STATE FROM information_schema.PROCESSLIST WHERE TIME > 300;\", \"step\": 5, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"查找长时间等待的连接\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}]','[\"execute_mysql_query\"]','建议优化应用连接池配置，增加最大连接数限制，优化长时间运行的查询，实施连接超时策略','ops-team','admin','system','2025-07-22 05:34:23','2025-08-01 23:03:54'),(6,'SOP-DB-003','MySQL活跃会话数过多诊断111333333','database','诊断MySQL活跃会话数过多导致的性能问题.....','high','[{\"args\": \"SELECT COUNT(*) as active_sessions FROM information_schema.PROCESSLIST WHERE COMMAND != Sleep;\", \"step\": 1, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"统计当前活跃会话数量\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO FROM information_schema.PROCESSLIST WHERE COMMAND != Sleep ORDER BY TIME DESC;\", \"step\": 2, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"查看所有活跃会话的详细状态\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"SELECT ID, USER, HOST, TIME, STATE, INFO FROM information_schema.PROCESSLIST WHERE TIME > 60 AND COMMAND != Sleep;\", \"step\": 3, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"识别运行时间超过60秒的会话\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"SELECT STATE, COUNT(*) as session_count FROM information_schema.PROCESSLIST GROUP BY STATE ORDER BY session_count DESC;\", \"step\": 4, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"分析会话状态分布情况\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"SELECT USER, COUNT(*) as session_count FROM information_schema.PROCESSLIST GROUP BY USER ORDER BY session_count DESC;\", \"step\": 5, \"tool\": \"execute_mysql_query\", \"timeout\": null, \"on_failure\": null, \"description\": \"按用户统计会话数量\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}]','[\"execute_mysql_query\"]','建议优化长时间运行的查询，调整应用连接池配置，终止异常的长时间会话，优化数据库连接管理策略','ops-team','admin','system','2025-07-22 05:34:24','2025-08-01 23:03:00'),(7,'SOP-SYS-101','磁盘空间不足诊断','system','诊断服务器磁盘空间不足的标准操作程序1111','critical','[{\"args\": \"df -h\", \"step\": 1, \"tool\": \"execute_system_command\", \"timeout\": null, \"on_failure\": null, \"description\": \"检查磁盘使用情况\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": true}, {\"args\": \"du -sh --exclude=/proc --exclude=/sys /* | sort -rh | head -10\", \"step\": 2, \"tool\": \"execute_system_command\", \"timeout\": null, \"on_failure\": null, \"description\": \"找出大文件和目录\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": true}, {\"args\": \"find /var/log -size +100M -exec ls -lh {} \\\\;\", \"step\": 3, \"tool\": \"execute_system_command\", \"timeout\": null, \"on_failure\": null, \"description\": \"检查日志文件大小\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"du -sh /tmp /var/tmp\", \"step\": 4, \"tool\": \"execute_system_command\", \"timeout\": null, \"on_failure\": null, \"description\": \"分析临时文件占用\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"find /var/log -name *.log.* -mtime +7 -ls\", \"step\": 5, \"tool\": \"execute_system_command\", \"timeout\": null, \"on_failure\": null, \"description\": \"检查可清理的日志文件\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"报告必须包含以下几部分信息：基本信息(时间、对象、问题描述、sop编号)、根因分析(是否确定根因、确定依据)、修复建议、预防措施\", \"step\": 6, \"tool\": \"llm\", \"timeout\": null, \"on_failure\": null, \"description\": \"生成排查报告\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}]','[\"execute_system_command\", \"get_current_time\"]','建议清理/tmp和/var/tmp中的临时文件，归档或删除旧的日志文件，联系系统管理员扩展磁盘空间，实施日志轮转策略','ops-team','admin','system','2025-07-22 05:34:24','2025-08-01 23:04:23'),(8,'SOP-SYS-102','系统负载过高诊断','system','诊断Linux系统负载平均值过高的标准操作程序','high','[{\"args\": \"uptime && cat /proc/loadavg\", \"step\": 1, \"tool\": \"get_system_info\", \"timeout\": null, \"on_failure\": null, \"description\": \"检查当前负载\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"top -bn1 | head -20\", \"step\": 2, \"tool\": \"analyze_processes\", \"timeout\": null, \"on_failure\": null, \"description\": \"查看CPU使用率\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"iostat -x 1 5\", \"step\": 3, \"tool\": \"execute_system_command\", \"timeout\": null, \"on_failure\": null, \"description\": \"检查IO等待\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"ps aux --sort=-%cpu | head -10\", \"step\": 4, \"tool\": \"analyze_processes\", \"timeout\": null, \"on_failure\": null, \"description\": \"查找高CPU进程\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}, {\"args\": \"ps aux --sort=-%mem | head -10\", \"step\": 5, \"tool\": \"analyze_processes\", \"timeout\": null, \"on_failure\": null, \"description\": \"查找高内存进程\", \"retry_count\": null, \"ai_generated\": false, \"requires_approval\": false}]','[\"get_system_info\", \"analyze_processes\", \"execute_system_command\"]','建议优化高CPU使用率的进程，优化高内存使用的进程，检查IO瓶颈并优化磁盘性能，联系系统管理员进行资源调优','ops-team','admin','admin','2025-07-22 05:34:24','2025-07-22 05:34:24');
/*!40000 ALTER TABLE `sop_prompt_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tenant_info`
--

DROP TABLE IF EXISTS `tenant_info`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tenant_info` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(100) NOT NULL COMMENT '租户唯一标识',
  `tenant_name` varchar(200) NOT NULL COMMENT '租户名称',
  `tenant_status` varchar(20) DEFAULT 'active' COMMENT '租户状态',
  `tenant_description` varchar(500) DEFAULT NULL COMMENT '租户描述',
  `contact_email_address` varchar(200) DEFAULT NULL COMMENT '联系邮箱',
  `create_by` varchar(100) NOT NULL COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_delete` tinyint(4) DEFAULT '0' COMMENT '软删除标记:0未删除,1已删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `tenant_id` (`tenant_id`),
  KEY `idx_tenant_status` (`tenant_status`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COMMENT='租户管理表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tenant_info`
--

LOCK TABLES `tenant_info` WRITE;
/*!40000 ALTER TABLE `tenant_info` DISABLE KEYS */;
INSERT INTO `tenant_info` VALUES (1,'default','默认租户','active','系统默认租户，用于向下兼容',NULL,'system',NULL,'2025-08-02 18:10:27','2025-08-02 18:10:27',0);
/*!40000 ALTER TABLE `tenant_info` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tenant_user`
--

DROP TABLE IF EXISTS `tenant_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `tenant_user` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `tenant_id` varchar(100) NOT NULL COMMENT '租户ID',
  `user_id` varchar(100) NOT NULL COMMENT '用户ID',
  `create_by` varchar(100) NOT NULL COMMENT '创建人用户名',
  `update_by` varchar(100) DEFAULT NULL COMMENT '最后更新人用户名',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  `is_delete` tinyint(4) DEFAULT '0' COMMENT '软删除标记:0未删除,1已删除',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uniq_tenant_user` (`tenant_id`,`user_id`),
  KEY `idx_tenant_id` (`tenant_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='租户用户关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tenant_user`
--

LOCK TABLES `tenant_user` WRITE;
/*!40000 ALTER TABLE `tenant_user` DISABLE KEYS */;
/*!40000 ALTER TABLE `tenant_user` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB AUTO_INCREMENT=903 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_threads`
--

LOCK TABLES `user_threads` WRITE;
/*!40000 ALTER TABLE `user_threads` DISABLE KEYS */;
INSERT INTO `user_threads` VALUES (901,'zhangsan123','23436a45-72e7-4125-b96b-831731a901aa','2025-07-24 15:26:01，...',NULL,0,0,NULL,'2025-08-07 10:26:15','2025-08-07 10:26:15'),(902,'zhangsan123','f1443da0-683d-4e57-a8bb-f6be79bad45d','nihao',NULL,0,0,NULL,'2025-08-07 10:45:40','2025-08-07 10:45:40');
/*!40000 ALTER TABLE `user_threads` ENABLE KEYS */;
UNLOCK TABLES;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-08-08  9:40:36
