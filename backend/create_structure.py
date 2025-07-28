#!/usr/bin/env python3
"""
创建业务模块目录结构
"""

import os

base_path = "/Users/gaochao/gaochao-git/gaochao_repo/fullstack-langgraph/backend/src"

# 定义目录结构
structure = {
    "apps": {
        "sop": ["api", "services", "dao", "models", "schemas", "tests"],
        "agent": ["api", "services", "dao", "models", "workflows", "tests"], 
        "mcp": ["api", "services", "dao", "models", "schemas", "tests"],
        "user": ["api", "services", "dao", "models", "tests"]
    },
    "shared": {
        "core": [],
        "db": [],
        "tools": []
    }
}

def create_init_file(path, content=""):
    """创建__init__.py文件"""
    init_path = os.path.join(path, "__init__.py")
    with open(init_path, "w", encoding="utf-8") as f:
        f.write(f'"""\n{content}\n"""\n' if content else '"""\n模块初始化文件\n"""\n')

def create_structure():
    """创建目录结构"""
    for main_dir, modules in structure.items():
        main_path = os.path.join(base_path, main_dir) 
        
        # 创建主目录
        os.makedirs(main_path, exist_ok=True)
        create_init_file(main_path, f"{main_dir.title()} modules")
        
        for module_name, subdirs in modules.items():
            module_path = os.path.join(main_path, module_name)
            os.makedirs(module_path, exist_ok=True)
            create_init_file(module_path, f"{module_name.title()} module")
            
            # 创建子目录
            for subdir in subdirs:
                subdir_path = os.path.join(module_path, subdir)
                os.makedirs(subdir_path, exist_ok=True)
                create_init_file(subdir_path, f"{module_name.title()} {subdir}")

if __name__ == "__main__":
    create_structure()
    print("✅ 目录结构创建完成!")