-- 为 scan_tasks 表添加 notify_status 字段
-- 执行时间: 2025-10-11

-- 添加 notify_status 字段
ALTER TABLE scan_tasks ADD COLUMN notify_status VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '通知状态：pending-待通知，sent-已发送，failed-发送失败';

-- 创建索引
CREATE INDEX idx_notify_status ON scan_tasks(notify_status);

-- 说明：
-- 1. notify_status 默认值为 'pending'，表示待通知
-- 2. 当任务完成（completed）或失败（failed）时，定时任务会扫描 notify_status='pending' 的记录进行通知
-- 3. 通知成功后更新为 'sent'，失败则更新为 'failed'
