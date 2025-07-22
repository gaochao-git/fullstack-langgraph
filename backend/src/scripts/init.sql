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
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 表注释 (PostgreSQL)
COMMENT ON TABLE users IS '用户基础信息表';
COMMENT ON COLUMN users.id IS '用户唯一标识，自增主键';
COMMENT ON COLUMN users.user_name IS '用户名，必须唯一';
COMMENT ON COLUMN users.create_time IS '记录创建时间';
COMMENT ON COLUMN users.update_time IS '记录最后更新时间';

-- 用户表索引 (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(user_name);

-- 用户线程关联表 (PostgreSQL)
CREATE TABLE IF NOT EXISTS user_threads (
    id BIGSERIAL PRIMARY KEY,
    user_name VARCHAR(100) NOT NULL,
    thread_id VARCHAR(255) NOT NULL,
    thread_title VARCHAR(200),
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_name, thread_id)
);

-- 表注释 (PostgreSQL)
COMMENT ON TABLE user_threads IS '用户线程关联表，管理用户与LangGraph线程的对应关系';
COMMENT ON COLUMN user_threads.id IS '自增主键';
COMMENT ON COLUMN user_threads.user_name IS '用户名，关联users表';
COMMENT ON COLUMN user_threads.thread_id IS 'LangGraph生成的线程唯一标识';
COMMENT ON COLUMN user_threads.thread_title IS '线程标题，方便用户识别对话内容';
COMMENT ON COLUMN user_threads.create_time IS '记录创建时间';
COMMENT ON COLUMN user_threads.update_time IS '记录最后更新时间';

-- 基础索引 (PostgreSQL)
CREATE INDEX IF NOT EXISTS idx_user_threads_user_id ON user_threads(user_name);
CREATE INDEX IF NOT EXISTS idx_user_threads_create_at ON user_threads(user_name, create_at DESC);

-- 标准操作程序提示词模板表 (PostgreSQL)
CREATE TABLE sop_prompt_templates (
  id BIGSERIAL PRIMARY KEY,
  sop_id VARCHAR(50) NOT NULL UNIQUE,
  sop_title VARCHAR(255) NOT NULL,
  sop_category VARCHAR(50) NOT NULL,
  sop_description TEXT,
  sop_severity VARCHAR(20) DEFAULT 'medium',
  sop_steps TEXT NOT NULL,
  tools_required TEXT,
  sop_recommendations TEXT,
  team_name VARCHAR(50) NOT NULL,
  create_by VARCHAR(50) NOT NULL,
  update_by VARCHAR(50),
  create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX uk_sop_id ON sop_prompt_templates(sop_id);