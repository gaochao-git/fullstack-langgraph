#!/usr/bin/env python3
"""
SOP数据导入脚本
从knowledge_base目录中的JSON文件导入SOP数据到数据库
"""

import json
import os
import sys
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# 添加src目录到Python路径
src_path = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_path)

from database.config import get_async_session, init_database
from services.sop_service import SOPService
from database.models import SOPPromptTemplate

# 知识库目录路径
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "src" / "knowledge_base" / "diagnostic_sop"

def load_json_file(file_path: Path) -> Dict[str, Any]:
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 加载文件 {file_path} 失败: {e}")
        return {}

def transform_sop_data(sop_id: str, sop_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将JSON格式的SOP数据转换为数据库格式
    
    JSON结构映射到数据库字段:
    - id -> sop_id
    - title -> sop_title  
    - category -> sop_category
    - description -> sop_description
    - severity -> sop_severity
    - steps -> sop_steps (JSON string)
    - tools_required -> tools_required (JSON string)
    - recommendations -> sop_recommendations
    - team_name -> 默认 "ops-team"
    """
    
    # 处理steps数据
    steps = sop_data.get('steps', [])
    steps_json = json.dumps(steps, ensure_ascii=False) if steps else "[]"
    
    # 处理tools_required数据
    tools_required = sop_data.get('tools_required', [])
    tools_json = json.dumps(tools_required, ensure_ascii=False) if tools_required else "[]"
    
    # 转换后的数据
    transformed_data = {
        'sop_id': sop_data.get('id', sop_id),
        'sop_title': sop_data.get('title', ''),
        'sop_category': sop_data.get('category', ''),
        'sop_description': sop_data.get('description', ''),
        'sop_severity': sop_data.get('severity', 'medium'),
        'sop_steps': steps_json,
        'tools_required': tools_json,
        'sop_recommendations': sop_data.get('recommendations', ''),
        'team_name': 'ops-team'  # 默认团队
    }
    
    return transformed_data

async def import_sop_file(file_path: Path, sop_service: SOPService) -> int:
    """导入单个SOP文件"""
    print(f"📁 正在处理文件: {file_path.name}")
    
    data = load_json_file(file_path)
    if not data:
        return 0
    
    imported_count = 0
    
    for sop_id, sop_data in data.items():
        try:
            # 检查SOP是否已存在
            existing_sop = await sop_service.get_sop_by_id(sop_id)
            if existing_sop:
                print(f"  ⚠️  SOP {sop_id} 已存在，跳过导入")
                continue
            
            # 转换数据格式
            transformed_data = transform_sop_data(sop_id, sop_data)
            
            # 创建SOP
            result = await sop_service.create_sop(transformed_data)
            if result:
                print(f"  ✅ 成功导入 SOP: {sop_id} - {sop_data.get('title', '')}")
                imported_count += 1
            else:
                print(f"  ❌ 导入失败 SOP: {sop_id}")
                
        except Exception as e:
            print(f"  ❌ 导入 SOP {sop_id} 时发生错误: {e}")
    
    return imported_count

async def main():
    """主函数"""
    print("🚀 开始导入SOP数据到数据库...")
    
    # 检查知识库目录
    if not KNOWLEDGE_BASE_DIR.exists():
        print(f"❌ 知识库目录不存在: {KNOWLEDGE_BASE_DIR}")
        return
    
    # 查找JSON文件
    json_files = list(KNOWLEDGE_BASE_DIR.glob("*.json"))
    if not json_files:
        print(f"❌ 在 {KNOWLEDGE_BASE_DIR} 中未找到JSON文件")
        return
    
    print(f"📊 找到 {len(json_files)} 个JSON文件")
    
    total_imported = 0
    
    try:
        # 初始化数据库
        await init_database()
        
        # 创建数据库会话
        async for db_session in get_async_session():
            sop_service = SOPService(db_session)
            
            # 逐个处理文件
            for json_file in json_files:
                imported_count = await import_sop_file(json_file, sop_service)
                total_imported += imported_count
                print(f"📄 {json_file.name}: 导入 {imported_count} 条SOP")
            
            print(f"\n🎉 数据导入完成！")
            print(f"📈 总计导入: {total_imported} 条SOP记录")
            
            # 显示数据库统计信息
            all_sops = await sop_service.get_sops()
            print(f"📊 数据库中现有SOP总数: {all_sops['total']}")
            
    except Exception as e:
        print(f"❌ 数据导入过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())