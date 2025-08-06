-- MySQL表结构SQL脚本
-- 基于backend/src/db/models.py生成
-- 包含四个主要业务表：SOP模板、MCP服务器、智能体配置、AI模型配置

-- 1. SOP模板表 (Standard Operating Procedure Templates)
-- 用于存储标准操作程序模板
CREATE TABLE `sop_prompt_templates` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    `sop_id` VARCHAR(100) NOT NULL UNIQUE COMMENT 'SOP唯一标识符，如SOP-DB-001',
    `sop_title` VARCHAR(500) NOT NULL COMMENT 'SOP标题名称',
    `sop_category` VARCHAR(100) NOT NULL COMMENT 'SOP分类（如database、system、network等）',
    `sop_description` TEXT COMMENT 'SOP详细描述',
    `sop_severity` VARCHAR(20) NOT NULL COMMENT 'SOP严重等级（high、medium、low）',
    `sop_steps` JSON NOT NULL COMMENT 'SOP执行步骤，JSON格式存储步骤列表',
    `tools_required` JSON COMMENT '所需工具列表，JSON格式存储工具名称数组',
    `sop_recommendations` TEXT COMMENT 'SOP建议和最佳实践',
    `team_name` VARCHAR(100) NOT NULL COMMENT '负责团队名称',
    `create_by` VARCHAR(100) NOT NULL COMMENT '创建人用户名',
    `update_by` VARCHAR(100) COMMENT '最后更新人用户名',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SOP标准操作程序模板表';

-- 2. MCP服务器配置表 (Model Context Protocol Servers)
-- 用于存储MCP服务器的配置信息
CREATE TABLE `mcp_servers` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    `server_id` VARCHAR(100) NOT NULL UNIQUE COMMENT 'MCP服务器唯一标识符',
    `server_name` VARCHAR(200) NOT NULL COMMENT 'MCP服务器显示名称',
    `server_uri` VARCHAR(500) NOT NULL COMMENT 'MCP服务器连接URI',
    `server_description` TEXT COMMENT 'MCP服务器功能描述',
    `is_enabled` VARCHAR(10) NOT NULL DEFAULT 'on' COMMENT '是否启用（on/off）',
    `connection_status` VARCHAR(20) NOT NULL DEFAULT 'disconnected' COMMENT '连接状态（connected/disconnected/error）',
    `auth_type` VARCHAR(20) DEFAULT '' COMMENT '认证类型（bearer、api_key等）',
    `auth_token` TEXT COMMENT '认证令牌或密钥',
    `api_key_header` VARCHAR(100) COMMENT 'API密钥请求头名称',
    `read_timeout_seconds` INT NOT NULL DEFAULT 5 COMMENT '读取超时时间（秒）',
    `server_tools` TEXT COMMENT '服务器提供的工具列表，JSON格式',
    `server_config` TEXT COMMENT '服务器配置信息，JSON格式',
    `team_name` VARCHAR(100) NOT NULL COMMENT '负责团队名称',
    `create_by` VARCHAR(100) NOT NULL COMMENT '创建人用户名',
    `update_by` VARCHAR(100) COMMENT '最后更新人用户名',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='MCP服务器配置表';

-- 3. 智能体配置表 (Agent Configurations)
-- 用于存储智能体的完整配置信息
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
) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COMMENT='智能体配置表'

-- 4. AI模型配置表 (AI Model Configurations)  
-- 用于存储AI模型的配置信息
CREATE TABLE `ai_model_configs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    `model_id` VARCHAR(100) NOT NULL UNIQUE COMMENT '模型唯一标识符',
    `model_name` VARCHAR(200) NOT NULL COMMENT '模型显示名称',
    `model_provider` VARCHAR(50) NOT NULL COMMENT '模型提供商（openai、deepseek、ollama等）',
    `model_type` VARCHAR(100) NOT NULL COMMENT '模型类型标识',
    `endpoint_url` VARCHAR(500) NOT NULL COMMENT '模型API端点URL',
    `api_key_value` TEXT COMMENT 'API密钥值',
    `model_description` TEXT COMMENT '模型功能描述',
    `model_status` VARCHAR(20) NOT NULL DEFAULT 'inactive' COMMENT '模型状态（active/inactive/error）',
    `config_data` TEXT COMMENT '模型配置数据，JSON格式存储参数设置',
    `create_by` VARCHAR(100) NOT NULL COMMENT '创建人用户名',
    `update_by` VARCHAR(100) COMMENT '最后更新人用户名',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='AI模型配置表';

-- 5. 用户表 (Users)
-- 用于存储用户基本信息
CREATE TABLE `users` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    `user_name` VARCHAR(100) NOT NULL UNIQUE COMMENT '用户名，全局唯一',
    `display_name` VARCHAR(200) COMMENT '用户显示名称',
    `email` VARCHAR(255) COMMENT '用户邮箱地址',
    `user_type` VARCHAR(20) NOT NULL DEFAULT 'regular' COMMENT '用户类型（admin/regular/guest）',
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否处于活跃状态',
    `last_login` DATETIME COMMENT '最后登录时间',
    `avatar_url` VARCHAR(500) COMMENT '用户头像URL',
    `preferences` JSON COMMENT '用户偏好设置，JSON格式',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户基本信息表';

-- 6. 用户线程关联表 (User Threads)
-- 用于存储用户与对话线程的关联关系
CREATE TABLE `user_threads` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID，自增',
    `user_name` VARCHAR(100) NOT NULL COMMENT '用户名，关联users表',
    `thread_id` VARCHAR(255) NOT NULL COMMENT '线程ID，对应LangGraph的thread_id',
    `thread_title` VARCHAR(500) COMMENT '线程标题，用户可自定义',
    `agent_id` VARCHAR(100) COMMENT '关联的智能体ID',
    `is_archived` BOOLEAN NOT NULL DEFAULT FALSE COMMENT '是否已归档',
    `message_count` INT NOT NULL DEFAULT 0 COMMENT '消息数量统计',
    `last_message_time` DATETIME COMMENT '最后消息时间',
    `create_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    -- 联合唯一索引
    UNIQUE KEY `uk_user_thread` (`user_name`, `thread_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户线程关联表';

CREATE TABLE `openapi_mcp_configs` (
    `id` bigint NOT NULL AUTO_INCREMENT,
    `mcp_server_prefix` varchar(255) NOT NULL COMMENT 'mcpserver前缀',
    `mcp_tool_name` varchar(255) NOT NULL COMMENT '工具名称',
    `mcp_tool_enabled` tinyint NOT NULL DEFAULT '0' COMMENT '是否开启:0关闭,1开启',
    `openapi_schema` longtext NOT NULL COMMENT '原始OpenAPI规范JSON/YAML',
    `auth_config` text NOT NULL COMMENT '认证配置',
    `extra_config` text NOT NULL COMMENT '其他配置',
    `is_deleted` tinyint NOT NULL DEFAULT '0' COMMENT '是否删除:0未删除,1已删除',
    `create_by` varchar(100) NOT NULL COMMENT '创建者',
    `update_by` varchar(100) DEFAULT NULL COMMENT '更新者',
    `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uniq_prefix_tool` (`mcp_server_prefix`, `mcp_tool_name`),
    KEY `idx_mcp_tool_name` (`mcp_tool_name`),
    KEY `idx_create_time` (`create_time`)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='OpenAPI转MCP配置表';