-- 优化知识库树形结构存储
-- 添加JSON字段存储完整树结构快照，提升查询性能

-- 为知识库表添加树结构字段
ALTER TABLE knowledge_bases 
ADD COLUMN folder_tree_snapshot JSON COMMENT '目录树结构快照(JSON格式)';

-- 添加更新时间索引用于快照失效检查
ALTER TABLE kb_folders 
ADD INDEX idx_update_time (update_time DESC);

-- 示例JSON结构：
-- {
--   "tree": [
--     {
--       "folder_id": "uuid1",
--       "folder_name": "技术文档", 
--       "sort_order": 1,
--       "children": [
--         {
--           "folder_id": "uuid2",
--           "folder_name": "API文档",
--           "sort_order": 1,
--           "children": []
--         }
--       ]
--     }
--   ],
--   "last_updated": "2024-01-01 00:00:00",
--   "version": 1
-- }

-- 为目录表添加路径字段，方便快速查询
ALTER TABLE kb_folders 
ADD COLUMN folder_path VARCHAR(1000) COMMENT '目录路径，如：/根目录/子目录';

-- 添加路径索引
ALTER TABLE kb_folders 
ADD INDEX idx_folder_path (folder_path);