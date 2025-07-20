# 数据库脚本说明

## 用户表和用户线程关联表

### 文件说明

- `init.sql` - PostgreSQL版本（默认）
- `init_mysql.sql` - MySQL版本

### 表结构

#### users 表
```sql
users (
    user_id         - 用户ID (VARCHAR(36), 主键)
    username        - 用户名 (VARCHAR(100), 唯一)
    created_at      - 创建时间
)
```

#### user_threads 表
```sql
user_threads (
    id              - 自增主键
    user_id         - 用户ID (VARCHAR(36))
    thread_id       - LangGraph线程ID (VARCHAR(255)) 
    thread_title    - 线程标题 (VARCHAR(200), 可选)
    created_at      - 创建时间
)
```

### 索引

#### users 表索引
- `idx_users_username` - 用户名索引

#### user_threads 表索引
- `idx_user_threads_user_id` - 用户ID索引
- `idx_user_threads_created_at` - 用户ID+创建时间复合索引（降序）
- `unique_user_thread` - 用户ID+线程ID唯一约束

### 使用方法

#### 1. PostgreSQL
```bash
psql -h your_host -U your_user -d your_database -f init.sql
```

#### 2. MySQL
```bash
mysql -h your_host -u your_user -p your_database < init_mysql.sql
```

### 常用SQL操作

```sql
-- 创建用户
INSERT INTO users (user_id, username) 
VALUES ('user-123', 'admin');

-- 创建用户线程关联
INSERT INTO user_threads (user_id, thread_id, thread_title) 
VALUES ('user-123', 'thread-456', '磁盘空间故障诊断');

-- 查询用户的所有线程（关联查询）
SELECT ut.thread_id, ut.thread_title, ut.created_at, u.username
FROM user_threads ut
JOIN users u ON ut.user_id = u.user_id
WHERE ut.user_id = 'user-123' 
ORDER BY ut.created_at DESC 
LIMIT 10;

-- 验证线程归属
SELECT COUNT(*) FROM user_threads 
WHERE user_id = 'user-123' AND thread_id = 'thread-456';

-- 查询用户信息
SELECT * FROM users WHERE username = 'admin';

-- 更新线程标题
UPDATE user_threads 
SET thread_title = '新的标题' 
WHERE user_id = 'user-123' AND thread_id = 'thread-456';

-- 删除线程关联
DELETE FROM user_threads 
WHERE user_id = 'user-123' AND thread_id = 'thread-456';
```

### 集成说明

这两个表用于管理用户和LangGraph线程的关联关系：

#### users 表特性
1. **极简用户管理** - 只保留必要字段
2. **用户名唯一性** - 确保用户名不重复
3. **最小化设计** - 减少存储开销

#### user_threads 表特性
1. **无外键依赖** - 可以独立于其他系统存在
2. **最小字段** - 只包含必要的关联信息
3. **跨数据库兼容** - 支持PostgreSQL和MySQL
4. **高性能索引** - 针对查询场景优化

### 注意事项

- `user_id` 可以是UUID或自定义ID格式
- `thread_id` 是LangGraph自动生成的UUID
- `thread_title` 用户可以自定义，便于识别对话
- `username` 必须唯一，建议使用邮箱或工号
- 建议定期清理过期的线程关联记录
- 无触发器，更新时间需在应用层维护