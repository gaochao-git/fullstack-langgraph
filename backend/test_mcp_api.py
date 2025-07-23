#!/usr/bin/env python3
"""测试MCP API接口的简单脚本"""
import requests
import json
import uuid

BASE_URL = "http://localhost:8000/api/mcp"

def test_create_server():
    """测试创建MCP服务器"""
    server_data = {
        "server_id": f"test-server-{str(uuid.uuid4())[:8]}",
        "server_name": "测试MCP服务器",
        "server_uri": "http://localhost:3000",
        "server_description": "用于测试的MCP服务器",
        "is_enabled": "on",
        "connection_status": "disconnected",
        "auth_type": "none",
        "team_name": "test_team",
        "create_by": "test_user",
        "server_tools": [
            {"name": "test_tool", "description": "测试工具"}
        ],
        "server_config": {"timeout": 30}
    }
    
    response = requests.post(f"{BASE_URL}/servers", json=server_data)
    print(f"创建服务器: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        return response.json()["server_id"]
    else:
        print(f"错误: {response.text}")
        return None

def test_get_servers():
    """测试获取服务器列表"""
    response = requests.get(f"{BASE_URL}/servers")
    print(f"获取服务器列表: {response.status_code}")
    if response.status_code == 200:
        servers = response.json()
        print(f"找到 {len(servers)} 个服务器")
        for server in servers:
            print(f"  - {server['server_name']} ({server['server_id']})")
        return servers
    else:
        print(f"错误: {response.text}")
        return []

def test_get_server(server_id):
    """测试获取单个服务器"""
    response = requests.get(f"{BASE_URL}/servers/{server_id}")
    print(f"获取服务器详情: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_update_server(server_id):
    """测试更新服务器"""
    update_data = {
        "server_name": "更新后的MCP服务器",
        "server_description": "这是更新后的描述",
        "update_by": "test_user"
    }
    
    response = requests.put(f"{BASE_URL}/servers/{server_id}", json=update_data)
    print(f"更新服务器: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_test_server(server_id):
    """测试服务器连接"""
    response = requests.post(f"{BASE_URL}/servers/{server_id}/test")
    print(f"测试服务器连接: {response.status_code}")
    if response.status_code == 200:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_delete_server(server_id):
    """测试删除服务器"""
    response = requests.delete(f"{BASE_URL}/servers/{server_id}")
    print(f"删除服务器: {response.status_code}")
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"错误: {response.text}")

def main():
    print("=== MCP API 测试 ===")
    
    # 1. 测试获取服务器列表
    print("\n1. 获取现有服务器列表")
    existing_servers = test_get_servers()
    
    # 2. 测试创建服务器
    print("\n2. 创建新服务器")
    server_id = test_create_server()
    
    if server_id:
        # 3. 测试获取单个服务器
        print(f"\n3. 获取服务器详情 ({server_id})")
        test_get_server(server_id)
        
        # 4. 测试更新服务器
        print(f"\n4. 更新服务器 ({server_id})")
        test_update_server(server_id)
        
        # 5. 测试连接测试
        print(f"\n5. 测试服务器连接 ({server_id})")
        test_test_server(server_id)
        
        # 6. 再次获取服务器列表
        print("\n6. 再次获取服务器列表")
        test_get_servers()
        
        # 7. 测试删除服务器
        print(f"\n7. 删除服务器 ({server_id})")
        test_delete_server(server_id)
        
        # 8. 最终获取服务器列表
        print("\n8. 最终获取服务器列表")
        test_get_servers()
    
    print("\n=== 测试完成 ===")

if __name__ == "__main__":
    main()