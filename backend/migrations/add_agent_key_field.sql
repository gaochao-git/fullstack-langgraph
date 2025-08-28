-- 为智能体配置表添加调用密钥字段
ALTER TABLE agent_configs ADD COLUMN agent_key VARCHAR(64) UNIQUE COMMENT '智能体调用密钥' after agent_name;

-- 为已有的智能体生成随机密钥（可选，也可以在应用层处理）
-- UPDATE agent_configs 
-- SET agent_key = MD5(CONCAT(agent_id, UNIX_TIMESTAMP(), RAND())) 
-- WHERE agent_key IS NULL;