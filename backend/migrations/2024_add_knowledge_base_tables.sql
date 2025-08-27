-- 知识库管理相关表结构
-- 创建时间: 2024-12

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kb_id VARCHAR(36) NOT NULL UNIQUE COMMENT '知识库唯一标识',
    kb_name VARCHAR(255) NOT NULL COMMENT '知识库名称',
    kb_description TEXT COMMENT '知识库描述',
    kb_type VARCHAR(50) DEFAULT 'general' COMMENT '知识库类型: general, technical, faq, training',
    kb_status TINYINT DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
    visibility VARCHAR(20) DEFAULT 'private' COMMENT '可见性: private, internal, public',
    
    -- 业务字段
    owner_id VARCHAR(100) NOT NULL COMMENT '所有者用户名',
    department VARCHAR(100) COMMENT '部门',
    tags TEXT COMMENT '标签(JSON格式)',
    settings TEXT COMMENT '设置(JSON格式，搜索配置、权限设置等)',
    
    -- 统计字段
    doc_count INT DEFAULT 0 COMMENT '文档数量',
    total_chunks INT DEFAULT 0 COMMENT '总分块数',
    
    -- 标准字段
    create_by VARCHAR(100) NOT NULL COMMENT '创建人',
    update_by VARCHAR(100) COMMENT '更新人',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    INDEX idx_owner (owner_id),
    INDEX idx_status (kb_status),
    INDEX idx_type (kb_type),
    INDEX idx_create_time (create_time DESC)
) COMMENT='知识库表';

-- 知识库目录表（树形结构）
CREATE TABLE IF NOT EXISTS kb_folders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    folder_id VARCHAR(36) NOT NULL UNIQUE COMMENT '目录唯一标识',
    kb_id VARCHAR(36) NOT NULL COMMENT '所属知识库ID',
    parent_folder_id VARCHAR(36) COMMENT '父目录ID，NULL表示根目录',
    
    folder_name VARCHAR(255) NOT NULL COMMENT '目录名称',
    folder_description TEXT COMMENT '目录描述',
    folder_type VARCHAR(50) DEFAULT 'folder' COMMENT '目录类型',
    sort_order INT DEFAULT 0 COMMENT '排序权重',
    
    -- 权限继承
    inherit_permissions BOOLEAN DEFAULT TRUE COMMENT '是否继承权限',
    custom_permissions TEXT COMMENT '自定义权限(JSON格式)',
    
    -- 标准字段
    create_by VARCHAR(100) NOT NULL COMMENT '创建人',
    update_by VARCHAR(100) COMMENT '更新人',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- FOREIGN KEY (kb_id) REFERENCES knowledge_bases(kb_id) ON DELETE CASCADE,
    INDEX idx_kb_id (kb_id),
    INDEX idx_parent_folder (parent_folder_id),
    INDEX idx_sort_order (kb_id, parent_folder_id, sort_order)
) COMMENT='知识库目录表';

-- 知识库文档关联表
CREATE TABLE IF NOT EXISTS kb_documents (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kb_id VARCHAR(36) NOT NULL COMMENT '知识库ID',
    file_id VARCHAR(36) NOT NULL COMMENT '文件ID',
    
    -- 文档在知识库中的属性
    doc_title VARCHAR(500) COMMENT '文档标题(可重命名)',
    doc_category VARCHAR(100) COMMENT '文档分类',
    doc_priority INT DEFAULT 0 COMMENT '权重',
    doc_status TINYINT DEFAULT 1 COMMENT '在此知识库中的状态: 1-正常, 0-禁用',
    
    -- 移除版本管理字段
    
    -- 标准字段
    create_by VARCHAR(100) NOT NULL COMMENT '添加人',
    update_by VARCHAR(100) COMMENT '更新人',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '添加时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_kb_file (kb_id, file_id),
    -- FOREIGN KEY (kb_id) REFERENCES knowledge_bases(kb_id) ON DELETE CASCADE,
    -- FOREIGN KEY (file_id) REFERENCES agent_document_upload(file_id) ON DELETE CASCADE,
    INDEX idx_kb_status (kb_id, doc_status),
    INDEX idx_category (kb_id, doc_category)
) COMMENT='知识库文档关联表';

-- 文档与目录关联表
CREATE TABLE IF NOT EXISTS kb_document_folders (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kb_id VARCHAR(36) NOT NULL COMMENT '知识库ID',
    file_id VARCHAR(36) NOT NULL COMMENT '文件ID',
    folder_id VARCHAR(36) COMMENT '目录ID，NULL表示根目录',
    
    -- 在目录中的属性
    display_name VARCHAR(255) COMMENT '在此目录中的显示名',
    sort_order INT DEFAULT 0 COMMENT '排序权重',
    is_pinned BOOLEAN DEFAULT FALSE COMMENT '是否置顶',
    
    -- 标准字段
    create_by VARCHAR(100) NOT NULL COMMENT '操作人',
    update_by VARCHAR(100) COMMENT '更新人',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_kb_file_folder (kb_id, file_id, folder_id),
    -- FOREIGN KEY (kb_id) REFERENCES knowledge_bases(kb_id) ON DELETE CASCADE,
    -- FOREIGN KEY (file_id) REFERENCES agent_document_upload(file_id) ON DELETE CASCADE,
    -- FOREIGN KEY (folder_id) REFERENCES kb_folders(folder_id) ON DELETE CASCADE,
    INDEX idx_folder_sort (folder_id, sort_order),
    INDEX idx_kb_folder (kb_id, folder_id)
) COMMENT='文档目录关联表';

-- 知识库权限表
CREATE TABLE IF NOT EXISTS kb_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kb_id VARCHAR(36) NOT NULL COMMENT '知识库ID',
    user_id VARCHAR(100) NOT NULL COMMENT '用户ID',
    permission_type VARCHAR(20) NOT NULL COMMENT '权限类型: read, write, admin',
    
    -- 权限来源
    granted_by VARCHAR(100) COMMENT '授权人',
    granted_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '授权时间',
    expire_time DATETIME COMMENT '过期时间，NULL表示永不过期',
    
    -- 标准字段
    create_by VARCHAR(100) NOT NULL COMMENT '创建人',
    update_by VARCHAR(100) COMMENT '更新人', 
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_kb_user (kb_id, user_id),
    -- FOREIGN KEY (kb_id) REFERENCES knowledge_bases(kb_id) ON DELETE CASCADE,
    INDEX idx_user_permission (user_id, permission_type)
) COMMENT='知识库权限表';

-- 知识库分类表（可选）
CREATE TABLE IF NOT EXISTS kb_categories (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    kb_id VARCHAR(36) NOT NULL COMMENT '知识库ID',
    category_name VARCHAR(100) NOT NULL COMMENT '分类名称',
    parent_id BIGINT COMMENT '父分类ID',
    sort_order INT DEFAULT 0 COMMENT '排序权重',
    category_description TEXT COMMENT '分类描述',
    
    -- 标准字段
    create_by VARCHAR(100) NOT NULL COMMENT '创建人',
    update_by VARCHAR(100) COMMENT '更新人',
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- FOREIGN KEY (kb_id) REFERENCES knowledge_bases(kb_id) ON DELETE CASCADE,
    -- FOREIGN KEY (parent_id) REFERENCES kb_categories(id) ON DELETE SET NULL,
    INDEX idx_kb_category (kb_id, parent_id),
    INDEX idx_sort_order (kb_id, sort_order)
) COMMENT='知识库分类表';