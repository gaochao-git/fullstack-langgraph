#!/usr/bin/env python3
"""测试CAS票据验证"""
import requests
from urllib.parse import urlencode

# CAS配置
cas_server_url = "http://localhost:8080/cas"
service_url = "http://localhost:3000/api/v1/auth/cas/callback"
ticket = "ST-1-abc123"  # 替换为实际的ticket

# 构建验证URL
validate_url = f"{cas_server_url}/serviceValidate"
params = {
    'service': service_url,
    'ticket': ticket
}

print(f"验证URL: {validate_url}")
print(f"参数: {params}")

# 发送验证请求
full_url = f"{validate_url}?{urlencode(params)}"
print(f"完整URL: {full_url}")

try:
    response = requests.get(full_url, verify=False)
    print(f"\nHTTP状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"\n响应内容:")
    print(response.text[:500])  # 只打印前500个字符
    
    # 检查是否是XML
    if response.text.strip().startswith('<'):
        print("\n响应是XML格式")
    else:
        print("\n警告：响应不是XML格式!")
        
except Exception as e:
    print(f"请求失败: {e}")