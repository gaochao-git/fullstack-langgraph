-- MySQL Migration Script
-- Converted from SQLite database unla_real.db
-- Generated on 2025-07-31

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for messages
-- ----------------------------
DROP TABLE IF EXISTS `messages`;
CREATE TABLE `messages` (
  `id` varchar(64) NOT NULL,
  `session_id` varchar(64) DEFAULT NULL,
  `content` text,
  `reasoning_content` text,
  `sender` varchar(50) DEFAULT NULL,
  `timestamp` datetime DEFAULT NULL,
  `tool_calls` text,
  `tool_result` text,
  PRIMARY KEY (`id`),
  KEY `idx_messages_timestamp` (`timestamp`),
  KEY `idx_messages_session_id` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for sessions
-- ----------------------------
DROP TABLE IF EXISTS `sessions`;
CREATE TABLE `sessions` (
  `id` varchar(64) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `title` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(50) DEFAULT NULL,
  `password` text NOT NULL,
  `role` text NOT NULL DEFAULT 'normal',
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_users_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for tenants
-- ----------------------------
DROP TABLE IF EXISTS `tenants`;
CREATE TABLE `tenants` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `prefix` varchar(50) DEFAULT NULL,
  `description` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_tenants_prefix` (`prefix`),
  UNIQUE KEY `idx_tenants_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for user_tenants
-- ----------------------------
DROP TABLE IF EXISTS `user_tenants`;
CREATE TABLE `user_tenants` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `tenant_id` int(11) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_user_tenant` (`user_id`,`tenant_id`),
  KEY `fk_user_tenants_tenant` (`tenant_id`),
  CONSTRAINT `fk_user_tenants_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_user_tenants_tenant` FOREIGN KEY (`tenant_id`) REFERENCES `tenants` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for system_prompts
-- ----------------------------
DROP TABLE IF EXISTS `system_prompts`;
CREATE TABLE `system_prompts` (
  `user_id` int(11) NOT NULL,
  `prompt` text NOT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`user_id`),
  CONSTRAINT `fk_system_prompts_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for mcp_configs
-- ----------------------------
DROP TABLE IF EXISTS `mcp_configs`;
CREATE TABLE `mcp_configs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `tenant` varchar(50) DEFAULT '',
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `routers` text,
  `servers` text,
  `tools` text,
  `prompts` text,
  `mcp_servers` text,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_name_tenant` (`tenant`,`name`),
  KEY `idx_mcp_configs_deleted_at` (`deleted_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for mcp_config_versions
-- ----------------------------
DROP TABLE IF EXISTS `mcp_config_versions`;
CREATE TABLE `mcp_config_versions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(50) DEFAULT NULL,
  `tenant` varchar(50) DEFAULT NULL,
  `version` int(11) DEFAULT NULL,
  `action_type` text NOT NULL,
  `created_by` text,
  `created_at` datetime DEFAULT NULL,
  `routers` text,
  `servers` text,
  `tools` text,
  `prompts` text,
  `mcp_servers` text,
  `hash` text NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_mcp_config_versions_deleted_at` (`deleted_at`),
  KEY `idx_name_tenant_version` (`name`,`tenant`,`version`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Table structure for active_versions
-- ----------------------------
DROP TABLE IF EXISTS `active_versions`;
CREATE TABLE `active_versions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tenant` varchar(50) NOT NULL,
  `name` varchar(50) NOT NULL,
  `version` int(11) NOT NULL,
  `updated_at` datetime NOT NULL,
  `deleted_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_tenant_name` (`tenant`,`name`),
  KEY `idx_active_versions_deleted_at` (`deleted_at`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Data for table messages
-- ----------------------------
-- No data found for messages table

-- ----------------------------
-- Data for table sessions
-- ----------------------------
-- No data found for sessions table

-- ----------------------------
-- Data for table users
-- ----------------------------
INSERT INTO `users` VALUES (1, 'admin', '$2a$10$5TNAlruDjM0fQ3A4kv6FfOCn85jAkyZJyJKl58MOJUTkZvqtYZFOG', 'admin', 1, '2025-07-31 19:23:03.597796', '2025-07-31 19:23:03.597797');

-- ----------------------------
-- Data for table tenants
-- ----------------------------
INSERT INTO `tenants` VALUES (1, 'default', '/gateway', 'Default tenant for MCP Gateway', 1, '2025-07-31 19:23:03.487309', '2025-07-31 19:23:03.487309');

-- ----------------------------
-- Data for table user_tenants
-- ----------------------------
-- No data found for user_tenants table

-- ----------------------------
-- Data for table system_prompts
-- ----------------------------
-- No data found for system_prompts table

-- ----------------------------
-- Data for table mcp_configs
-- ----------------------------
INSERT INTO `mcp_configs` VALUES (1, 'systemhaha', 'default', '2025-07-31 11:23:13.337000', '2025-07-31 19:42:07.924994', '[{\"server\":\"nn\",\"prefix\":\"/gateway/9xuv\",\"ssePrefix\":\"\"}]', '[{\"name\":\"nn\",\"description\":\"\",\"allowedTools\":[\"systeminfo\"]}]', '[{\"name\":\"systeminfo\",\"method\":\"POST\",\"endpoint\":\"http://172.20.10.2:8000/api/v1/mcp/tools/system_info\",\"headers\":{\"Content-Type\":\"application/json\"},\"requestBody\":\"\",\"responseBody\":\"{{.Response.Body}}\"}]', '[]', '[]', NULL);

-- ----------------------------
-- Data for table mcp_config_versions
-- ----------------------------
INSERT INTO `mcp_config_versions` VALUES 
(1, 'systemhaha', 'default', 1, 'Create', 'system', '2025-07-31 19:24:26.780130', '[]', '[]', '[{\"name\":\"systeminfo\",\"method\":\"POST\",\"endpoint\":\"http://172.20.10.2:8000/api/v1/mcp/tools/system_info\",\"headers\":{\"Content-Type\":\"application/json\"},\"requestBody\":\"\",\"responseBody\":\"{{.Response.data}}\"}]', '[]', '[]', '450792555b2196a49b8030c35f8474c75c62eb23b10a218446355be48b36b65c', NULL),
(2, 'systemhaha', 'default', 2, 'Update', 'system', '2025-07-31 19:25:40.161686', '[]', '[{\"name\":\"nn\",\"description\":\"\"}]', '[{\"name\":\"systeminfo\",\"method\":\"POST\",\"endpoint\":\"http://172.20.10.2:8000/api/v1/mcp/tools/system_info\",\"headers\":{\"Content-Type\":\"application/json\"},\"requestBody\":\"\",\"responseBody\":\"{{.Response.data}}\"}]', '[]', '[]', 'c98331be79b9a948dd08ad9c37cb5559109d2433c5bc75decf9e3f5bdae91912', NULL),
(3, 'systemhaha', 'default', 3, 'Update', 'system', '2025-07-31 19:25:48.121670', '[{\"server\":\"nn\",\"prefix\":\"/gateway/9xuv\",\"ssePrefix\":\"\"}]', '[{\"name\":\"nn\",\"description\":\"\"}]', '[{\"name\":\"systeminfo\",\"method\":\"POST\",\"endpoint\":\"http://172.20.10.2:8000/api/v1/mcp/tools/system_info\",\"headers\":{\"Content-Type\":\"application/json\"},\"requestBody\":\"\",\"responseBody\":\"{{.Response.data}}\"}]', '[]', '[]', '25f002a43dc45eed4301bcfea7e781351910abb3954908524d73408d5a08d839', NULL),
(4, 'systemhaha', 'default', 4, 'Update', 'system', '2025-07-31 19:32:31.912549', '[{\"server\":\"nn\",\"prefix\":\"/gateway/9xuv\",\"ssePrefix\":\"\"}]', '[{\"name\":\"nn\",\"description\":\"\",\"allowedTools\":[\"systeminfo\"]}]', '[{\"name\":\"systeminfo\",\"method\":\"POST\",\"endpoint\":\"http://172.20.10.2:8000/api/v1/mcp/tools/system_info\",\"headers\":{\"Content-Type\":\"application/json\"},\"requestBody\":\"\",\"responseBody\":\"{{.Response.data}}\"}]', '[]', '[]', 'c70f487246f3ed2757e6251f34d3826d41b162a9a5a66f9b64e474227a78d2b0', NULL),
(5, 'systemhaha', 'default', 5, 'Update', 'system', '2025-07-31 19:42:07.925459', '[{\"server\":\"nn\",\"prefix\":\"/gateway/9xuv\",\"ssePrefix\":\"\"}]', '[{\"name\":\"nn\",\"description\":\"\",\"allowedTools\":[\"systeminfo\"]}]', '[{\"name\":\"systeminfo\",\"method\":\"POST\",\"endpoint\":\"http://172.20.10.2:8000/api/v1/mcp/tools/system_info\",\"headers\":{\"Content-Type\":\"application/json\"},\"requestBody\":\"\",\"responseBody\":\"{{.Response.Body}}\"}]', '[]', '[]', '74aa498e0820817e886ce960fe91fdbb6b900283d7f20ef7c43ae50c7f2903e3', NULL);

-- ----------------------------
-- Data for table active_versions
-- ----------------------------
INSERT INTO `active_versions` VALUES (1, 'default', 'systemhaha', 5, '2025-07-31 19:42:07.925845', NULL);

SET FOREIGN_KEY_CHECKS = 1;