#!/usr/bin/env python
"""测试新的API密钥格式 ak-"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.apps.auth.utils import APIKeyUtils

def test_api_key_format():
    """测试API密钥格式"""
    print("🔍 测试新的API密钥格式...\n")
    
    # 生成5个API密钥示例
    for i in range(5):
        api_key, key_hash = APIKeyUtils.generate_api_key()
        print(f"示例 {i+1}:")
        print(f"  API密钥: {api_key}")
        print(f"  格式验证: {'✅ 正确' if api_key.startswith('ak-') else '❌ 错误'}")
        print(f"  长度: {len(api_key)} 字符")
        print()
    
    # 测试密钥验证
    print("🔐 测试密钥验证功能...")
    test_key, test_hash = APIKeyUtils.generate_api_key()
    
    # 验证正确的密钥
    is_valid = APIKeyUtils.verify_api_key(test_key, test_hash)
    print(f"验证正确密钥: {'✅ 通过' if is_valid else '❌ 失败'}")
    
    # 验证错误的密钥
    is_valid = APIKeyUtils.verify_api_key("ak-wrong_key", test_hash)
    print(f"验证错误密钥: {'✅ 正确拒绝' if not is_valid else '❌ 错误通过'}")
    
    print("\n✅ 测试完成！新的API密钥格式为: ak-<随机字符串>")

if __name__ == "__main__":
    test_api_key_format()