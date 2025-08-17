#!/usr/bin/env python3
"""
文档目录迁移脚本
将旧的目录结构迁移到新的统一目录结构
"""

import os
import shutil
from pathlib import Path

def migrate_documents():
    """执行文档目录迁移"""
    
    # 定义路径
    backend_dir = Path(__file__).parent.parent
    old_uploads_dir = backend_dir / "uploads"
    old_documents_dir = backend_dir / "documents"
    new_documents_dir = backend_dir / "documents"
    
    print(f"开始迁移文档目录...")
    print(f"后端目录: {backend_dir}")
    
    # 1. 创建新的目录结构
    new_uploads = new_documents_dir / "uploads"
    new_templates = new_documents_dir / "templates"
    new_generated = new_documents_dir / "generated"
    
    # 创建目录
    new_uploads.mkdir(parents=True, exist_ok=True)
    new_templates.mkdir(parents=True, exist_ok=True)
    new_generated.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ 创建新目录结构:")
    print(f"   - {new_uploads}")
    print(f"   - {new_templates}")
    print(f"   - {new_generated}")
    
    # 2. 迁移上传文件 (uploads/* -> documents/uploads/)
    if old_uploads_dir.exists() and old_uploads_dir.is_dir():
        print(f"\n迁移上传文件...")
        file_count = 0
        
        for item in old_uploads_dir.rglob("*"):
            if item.is_file():
                # 计算相对路径
                relative_path = item.relative_to(old_uploads_dir)
                target_path = new_uploads / relative_path
                
                # 创建目标目录
                target_path.parent.mkdir(parents=True, exist_ok=True)
                
                # 移动文件
                if not target_path.exists():
                    shutil.move(str(item), str(target_path))
                    file_count += 1
                    print(f"   移动: {relative_path}")
        
        print(f"✅ 迁移了 {file_count} 个上传文件")
        
        # 删除旧的uploads目录（如果为空）
        try:
            if old_uploads_dir != new_documents_dir:
                shutil.rmtree(old_uploads_dir)
                print(f"✅ 删除旧的uploads目录")
        except:
            print(f"⚠️  无法删除旧的uploads目录，可能还有文件")
    
    # 3. 迁移模板文件
    old_templates = old_documents_dir / "templates"
    if old_templates.exists() and old_templates != new_templates:
        print(f"\n迁移模板文件...")
        template_count = 0
        
        for item in old_templates.glob("*.docx"):
            target_path = new_templates / item.name
            if not target_path.exists():
                shutil.move(str(item), str(target_path))
                template_count += 1
                print(f"   移动模板: {item.name}")
        
        print(f"✅ 迁移了 {template_count} 个模板文件")
    
    # 4. 确保公文模板存在
    gongwen_template = new_templates / "公文写作规范模板.docx"
    if not gongwen_template.exists():
        print(f"⚠️  请手动将公文写作规范模板.docx放置到: {new_templates}")
    else:
        print(f"✅ 公文模板已存在: {gongwen_template.name}")
    
    print(f"\n✅ 文档目录迁移完成!")
    print(f"\n新的目录结构:")
    print(f"documents/")
    print(f"├── uploads/     # 用户上传的文件")
    print(f"├── templates/   # Word模板文件")
    print(f"└── generated/   # 生成的文档")

if __name__ == "__main__":
    migrate_documents()