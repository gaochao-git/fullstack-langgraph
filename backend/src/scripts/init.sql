-- ================================================================
-- 用户表和用户线程关联表创建脚本
-- 支持 PostgreSQL 和 MySQL
-- ================================================================

-- PostgreSQL 版本
-- ================================================================

-- 用户表 (PostgreSQL)
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    user_name VARCHAR(100) UNIQUE NOT NULL,
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 表注释 (PostgreSQL)
COMMENT ON TABLE users IS '用户基础信息表';
COMMENT ON COLUMN users.id IS '用户唯一标识，自增主键';
COMMENT ON COLUMN users.user_name IS '用户名，必须唯一';
COMMENT ON COLUMN users.create_at IS '记录创建时间';
COMMENT ON COLUMN users.update_at IS '记录最后更新时间';

-- 用户表索引 (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(user_name);

-- 用户线程关联表 (PostgreSQL)
CREATE TABLE IF NOT EXISTS user_threads (
    id BIGSERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    thread_id VARCHAR(255) NOT NULL,
    thread_title VARCHAR(200),
    create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_name, thread_id)
);

-- 表注释 (PostgreSQL)
COMMENT ON TABLE user_threads IS '用户线程关联表，管理用户与LangGraph线程的对应关系';
COMMENT ON COLUMN user_threads.id IS '自增主键';
COMMENT ON COLUMN user_threads.user_name IS '用户名，关联users表';
COMMENT ON COLUMN user_threads.thread_id IS 'LangGraph生成的线程唯一标识';
COMMENT ON COLUMN user_threads.thread_title IS '线程标题，方便用户识别对话内容';
COMMENT ON COLUMN user_threads.create_at IS '记录创建时间';
COMMENT ON COLUMN user_threads.update_at IS '记录最后更新时间';

-- 基础索引 (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_user_threads_user_id ON user_threads(user_name);
CREATE INDEX IF NOT EXISTS idx_user_threads_create_at ON user_threads(user_name, create_at DESC);

-- ================================================================
-- MySQL 版本 (注释掉，需要时取消注释)
-- ================================================================

/*
-- 用户表 (MySQL)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一标识，自增主键',
    user_name VARCHAR(100) UNIQUE NOT NULL COMMENT '用户名，唯一',
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_users_username (user_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户基础信息表';

-- 用户线程关联表 (MySQL)
CREATE TABLE IF NOT EXISTS user_threads (
    id BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    user_name VARCHAR(100) UNIQUE NOT NULL COMMENT '用户名，关联users表',
    thread_id VARCHAR(255) NOT NULL COMMENT 'LangGraph线程ID',
    thread_title VARCHAR(200) COMMENT '线程标题，用户可自定义',
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY unique_user_thread (user_name, thread_id),
    INDEX idx_user_threads_user_id (user_name),
    INDEX idx_user_threads_create_at (user_name, create_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户线程关联表，管理用户与LangGraph线程的对应关系';
*/