-- 认证模块数据库表创建脚本
-- 注意：这是MySQL语法，其他数据库需要相应调整

-- 1. 用户认证信息表
CREATE TABLE IF NOT EXISTS `auth_users` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` VARCHAR(64) NOT NULL COMMENT '关联RBAC用户ID',
    `password_hash` VARCHAR(255) DEFAULT NULL COMMENT '密码哈希（JWT认证使用）',
    `mfa_secret` VARCHAR(255) DEFAULT NULL COMMENT 'MFA密钥',
    `mfa_enabled` BOOLEAN DEFAULT FALSE COMMENT '是否启用MFA',
    `last_login` DATETIME DEFAULT NULL COMMENT '最后登录时间',
    `last_login_ip` VARCHAR(45) DEFAULT NULL COMMENT '最后登录IP',
    `login_attempts` INT DEFAULT 0 COMMENT '登录尝试次数',
    `locked_until` DATETIME DEFAULT NULL COMMENT '账户锁定到期时间',
    `sso_provider` VARCHAR(50) DEFAULT NULL COMMENT 'SSO提供商标识',
    `sso_user_id` VARCHAR(255) DEFAULT NULL COMMENT 'SSO用户ID',
    `sso_attributes` TEXT DEFAULT NULL COMMENT 'SSO属性（JSON格式）',
    `password_changed_at` DATETIME DEFAULT NULL COMMENT '密码最后修改时间',
    `require_password_change` BOOLEAN DEFAULT FALSE COMMENT '是否需要修改密码',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_user_id` (`user_id`),
    KEY `idx_last_login` (`last_login`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户认证信息表';

-- 2. JWT令牌管理表
CREATE TABLE IF NOT EXISTS `auth_tokens` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` VARCHAR(64) NOT NULL COMMENT '用户ID',
    `token_jti` VARCHAR(255) NOT NULL COMMENT 'JWT的jti标识',
    `token_type` VARCHAR(20) NOT NULL COMMENT '令牌类型：access/refresh',
    `issued_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '签发时间',
    `expires_at` DATETIME NOT NULL COMMENT '过期时间',
    `last_used_at` DATETIME DEFAULT NULL COMMENT '最后使用时间',
    `revoked` BOOLEAN DEFAULT FALSE COMMENT '是否已撤销',
    `revoked_at` DATETIME DEFAULT NULL COMMENT '撤销时间',
    `revoke_reason` VARCHAR(255) DEFAULT NULL COMMENT '撤销原因',
    `device_id` VARCHAR(255) DEFAULT NULL COMMENT '设备标识',
    `device_name` VARCHAR(255) DEFAULT NULL COMMENT '设备名称',
    `ip_address` VARCHAR(45) DEFAULT NULL COMMENT 'IP地址',
    `user_agent` TEXT DEFAULT NULL COMMENT 'User-Agent',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_token_jti` (`token_jti`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_expires_at` (`expires_at`),
    KEY `idx_revoked` (`revoked`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='JWT令牌管理表';

-- 3. SSO会话管理表
CREATE TABLE IF NOT EXISTS `auth_sessions` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `session_id` VARCHAR(255) NOT NULL COMMENT '会话ID',
    `user_id` VARCHAR(64) NOT NULL COMMENT '用户ID',
    `sso_provider` VARCHAR(50) NOT NULL COMMENT 'SSO提供商',
    `sso_session_id` VARCHAR(255) DEFAULT NULL COMMENT 'SSO提供商的会话ID',
    `sso_access_token` TEXT DEFAULT NULL COMMENT 'SSO访问令牌（加密存储）',
    `sso_refresh_token` TEXT DEFAULT NULL COMMENT 'SSO刷新令牌（加密存储）',
    `sso_id_token` TEXT DEFAULT NULL COMMENT 'SSO ID令牌',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `expires_at` DATETIME NOT NULL COMMENT '过期时间',
    `last_accessed_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最后访问时间',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否活跃',
    `terminated_at` DATETIME DEFAULT NULL COMMENT '终止时间',
    `termination_reason` VARCHAR(255) DEFAULT NULL COMMENT '终止原因',
    `ip_address` VARCHAR(45) DEFAULT NULL COMMENT 'IP地址',
    `user_agent` TEXT DEFAULT NULL COMMENT 'User-Agent',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_session_id` (`session_id`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_sso_provider` (`sso_provider`),
    KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SSO会话管理表';

-- 4. 登录历史记录表
20) NOT NULL AUTO_INCREMENT,
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
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COMMENT='登录历史记录表'


-- 5. API密钥表
CREATE TABLE IF NOT EXISTS `auth_api_keys` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `user_id` VARCHAR(64) NOT NULL COMMENT '所属用户ID',
    `key_name` VARCHAR(100) NOT NULL COMMENT '密钥名称',
    `key_prefix` VARCHAR(20) NOT NULL COMMENT '密钥前缀（用于识别）',
    `key_hash` VARCHAR(255) NOT NULL COMMENT '密钥哈希',
    `scopes` TEXT DEFAULT NULL COMMENT '权限范围（JSON数组）',
    `allowed_ips` TEXT DEFAULT NULL COMMENT '允许的IP列表（JSON数组）',
    `issued_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '签发时间',
    `expires_at` DATETIME DEFAULT NULL COMMENT '过期时间（null表示永不过期）',
    `last_used_at` DATETIME DEFAULT NULL COMMENT '最后使用时间',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    `revoked_at` DATETIME DEFAULT NULL COMMENT '撤销时间',
    `revoke_reason` VARCHAR(255) DEFAULT NULL COMMENT '撤销原因',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `create_by` VARCHAR(50) NOT NULL COMMENT '创建人',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_key_hash` (`key_hash`),
    KEY `idx_user_id` (`user_id`),
    KEY `idx_expires_at` (`expires_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='API密钥表';

-- 6. SSO提供商配置表
CREATE TABLE IF NOT EXISTS `auth_sso_providers` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `provider_id` VARCHAR(50) NOT NULL COMMENT '提供商标识',
    `provider_name` VARCHAR(100) NOT NULL COMMENT '提供商名称',
    `provider_type` VARCHAR(50) NOT NULL COMMENT '提供商类型：oauth2/saml/cas',
    `client_id` VARCHAR(255) DEFAULT NULL COMMENT 'OAuth2 Client ID',
    `client_secret` TEXT DEFAULT NULL COMMENT 'OAuth2 Client Secret（加密存储）',
    `authorization_url` VARCHAR(500) DEFAULT NULL COMMENT '授权URL',
    `token_url` VARCHAR(500) DEFAULT NULL COMMENT 'Token URL',
    `userinfo_url` VARCHAR(500) DEFAULT NULL COMMENT '用户信息URL',
    `saml_metadata_url` VARCHAR(500) DEFAULT NULL COMMENT 'SAML元数据URL',
    `saml_entity_id` VARCHAR(255) DEFAULT NULL COMMENT 'SAML实体ID',
    `redirect_uri` VARCHAR(500) DEFAULT NULL COMMENT '回调URI',
    `scopes` VARCHAR(500) DEFAULT NULL COMMENT '请求的权限范围',
    `user_id_attribute` VARCHAR(100) DEFAULT NULL COMMENT '用户ID属性名',
    `username_attribute` VARCHAR(100) DEFAULT NULL COMMENT '用户名属性名',
    `email_attribute` VARCHAR(100) DEFAULT NULL COMMENT '邮箱属性名',
    `display_name_attribute` VARCHAR(100) DEFAULT NULL COMMENT '显示名称属性名',
    `is_active` BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    `priority` INT DEFAULT 0 COMMENT '优先级',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `create_by` VARCHAR(50) NOT NULL COMMENT '创建人',
    `update_by` VARCHAR(50) NOT NULL COMMENT '更新人',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_provider_id` (`provider_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='SSO提供商配置表';

-- 添加索引以优化查询性能
CREATE INDEX idx_auth_users_sso ON auth_users(sso_provider, sso_user_id);
CREATE INDEX idx_auth_tokens_user_device ON auth_tokens(user_id, device_id);
CREATE INDEX idx_auth_sessions_active ON auth_sessions(is_active, expires_at);
CREATE INDEX idx_auth_login_history_user_time ON auth_login_history(user_id, login_time);
CREATE INDEX idx_auth_api_keys_prefix ON auth_api_keys(key_prefix);

-- 插入默认SSO提供商配置示例（可选）
-- INSERT INTO auth_sso_providers (provider_id, provider_name, provider_type, create_by, update_by) 
-- VALUES ('google', 'Google', 'oauth2', 'system', 'system');