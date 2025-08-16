#!/usr/bin/env python3
"""
测试认证和权限访问
"""

import requests
import json

# 测试配置
BASE_URL = "http://localhost:8000"

def test_without_auth():
    """测试未认证访问"""
    print("\n=== 测试未认证访问 ===")
    
    # 测试一个需要认证的接口
    response = requests.get(f"{BASE_URL}/api/v1/auth/me/profile")
    print(f"GET /api/v1/auth/me/profile")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:200]}")
    
    # 测试用户列表接口
    response = requests.get(f"{BASE_URL}/api/v1/rbac/users")
    print(f"\nGET /api/v1/rbac/users")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:200]}")

def test_with_auth(token):
    """测试带认证访问"""
    print("\n=== 测试带认证访问 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 测试获取当前用户信息
    response = requests.get(f"{BASE_URL}/api/v1/auth/me/profile", headers=headers)
    print(f"GET /api/v1/auth/me/profile")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:200]}")
    
    # 测试获取用户菜单
    response = requests.get(f"{BASE_URL}/api/v1/auth/me/menus", headers=headers)
    print(f"\nGET /api/v1/auth/me/menus")
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        menus = response.json()
        print(f"菜单数量: {len(menus.get('menus', []))}")
    
    # 测试访问用户管理接口
    response = requests.get(f"{BASE_URL}/api/v1/rbac/users", headers=headers)
    print(f"\nGET /api/v1/rbac/users")
    print(f"状态码: {response.status_code}")
    if response.status_code != 200:
        print(f"错误详情: {response.text}")

def test_login_and_access():
    """测试登录并访问资源"""
    print("\n=== 测试登录流程 ===")
    
    # 使用默认用户登录
    login_data = {
        "username": "gaochao",
        "password": "123456"  # 请替换为实际密码
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"POST /api/v1/auth/login")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        access_token = data.get("access_token")
        print(f"登录成功，获得token")
        
        # 使用token测试访问
        test_with_auth(access_token)
    else:
        print(f"登录失败: {response.text}")

def check_user_roles(token):
    """检查用户的角色和权限"""
    print("\n=== 检查用户角色和权限 ===")
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    # 获取用户权限树
    response = requests.get(f"{BASE_URL}/api/v1/auth/me/permissions", headers=headers)
    print(f"GET /api/v1/auth/me/permissions")
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"角色: {[r['role_name'] for r in data.get('roles', [])]}")
        print(f"权限数量: {len(data.get('permissions', []))}")
        print(f"菜单数量: {len(data.get('menus', []))}")

def test_specific_api(path, method="GET", token=None):
    """测试特定的API"""
    print(f"\n=== 测试 {method} {path} ===")
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    if method == "GET":
        response = requests.get(f"{BASE_URL}{path}", headers=headers)
    elif method == "POST":
        response = requests.post(f"{BASE_URL}{path}", headers=headers, json={})
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:300]}")
    
    return response.status_code

if __name__ == "__main__":
    print("API认证和权限测试工具")
    print("=" * 50)
    
    # 1. 测试未认证访问
    test_without_auth()
    
    # 2. 测试登录
    print("\n" + "=" * 50)
    print("请提供登录凭据进行测试")
    username = input("用户名 (默认: gaochao): ").strip() or "gaochao"
    password = input("密码: ").strip()
    
    if password:
        login_data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print("\n✅ 登录成功")
            
            # 检查用户角色
            check_user_roles(token)
            
            # 测试各种访问
            test_with_auth(token)
            
            # 测试特定API
            print("\n" + "=" * 50)
            test_path = input("输入要测试的API路径 (例如: /api/v1/rbac/users): ").strip()
            if test_path:
                test_specific_api(test_path, token=token)
        else:
            print(f"\n❌ 登录失败: {response.text}")