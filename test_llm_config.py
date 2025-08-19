#!/usr/bin/env python
"""
测试新的LLM配置结构
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 测试数据
test_agent_data = {
    "agent_name": "测试LLM配置智能体",
    "agent_id": "test_llm_config_agent",
    "agent_type": "测试",
    "agent_description": "用于测试新的LLM配置结构",
    "agent_capabilities": ["测试"],
    "agent_icon": "Bot",
    "visibility_type": "private",
    "tools_info": {
        "system_tools": ["get_current_time"],
        "mcp_tools": []
    },
    "llm_info": [
        {
            "model_name": "deepseek-chat",
            "model_args": {
                "temperature": 0.7,
                "max_tokens": 2000,
                "top_p": 1.0
            }
        },
        {
            "model_name": "gpt-4",
            "model_args": {
                "temperature": 0.5,
                "max_tokens": 4000,
                "top_p": 0.9
            }
        }
    ],
    "prompt_info": {
        "system_prompt": "你是一个测试智能体"
    }
}

def test_create_agent():
    """测试创建智能体"""
    print("1. 测试创建智能体...")
    response = requests.post(
        f"{BASE_URL}/api/v1/agents",
        json=test_agent_data
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ 创建成功: {result}")
        return result.get('data', {}).get('agent_id')
    else:
        print(f"❌ 创建失败: {response.status_code} - {response.text}")
        return None

def test_get_agent(agent_id):
    """测试获取智能体配置"""
    print(f"\n2. 测试获取智能体配置...")
    response = requests.get(f"{BASE_URL}/api/v1/agents/{agent_id}")
    
    if response.status_code == 200:
        result = response.json()
        agent_data = result.get('data', {})
        
        print(f"✅ 获取成功")
        print(f"   agent_id: {agent_data.get('agent_id')}")
        print(f"   agent_name: {agent_data.get('agent_name')}")
        
        llm_info = agent_data.get('llm_info')
        print(f"\n   LLM配置类型: {type(llm_info)}")
        
        if isinstance(llm_info, list):
            print(f"   ✅ LLM配置是列表格式（新格式）")
            for i, config in enumerate(llm_info):
                print(f"\n   配置 {i+1}:")
                print(f"     model_name: {config.get('model_name')}")
                print(f"     model_args: {config.get('model_args')}")
        else:
            print(f"   ❌ LLM配置不是列表格式: {llm_info}")
            
        return agent_data
    else:
        print(f"❌ 获取失败: {response.status_code} - {response.text}")
        return None

def test_update_agent(agent_id):
    """测试更新智能体配置"""
    print(f"\n3. 测试更新智能体配置...")
    
    # 更新LLM配置
    update_data = {
        "llm_info": [
            {
                "model_name": "deepseek-chat",
                "model_args": {
                    "temperature": 0.8,  # 修改温度
                    "max_tokens": 3000,  # 修改token数
                    "top_p": 0.95
                }
            },
            {
                "model_name": "qwen-plus",  # 添加新模型
                "model_args": {
                    "temperature": 0.6,
                    "max_tokens": 2500,
                    "top_p": 0.9
                }
            }
        ]
    }
    
    response = requests.put(
        f"{BASE_URL}/api/v1/agents/{agent_id}",
        json=update_data
    )
    
    if response.status_code == 200:
        print(f"✅ 更新成功")
        
        # 重新获取验证更新
        updated_agent = test_get_agent(agent_id)
        if updated_agent:
            llm_info = updated_agent.get('llm_info')
            if isinstance(llm_info, list) and len(llm_info) > 0:
                print(f"\n   ✅ 更新验证成功:")
                for config in llm_info:
                    print(f"     - {config.get('model_name')}: {config.get('model_args')}")
    else:
        print(f"❌ 更新失败: {response.status_code} - {response.text}")

def test_delete_agent(agent_id):
    """测试删除智能体"""
    print(f"\n4. 测试删除智能体...")
    response = requests.delete(f"{BASE_URL}/api/v1/agents/{agent_id}")
    
    if response.status_code == 200:
        print(f"✅ 删除成功")
    else:
        print(f"❌ 删除失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("=== 测试新的LLM配置结构 ===\n")
    
    # 创建测试智能体
    agent_id = test_create_agent()
    
    if agent_id:
        # 获取智能体配置
        test_get_agent(agent_id)
        
        # 更新智能体配置
        test_update_agent(agent_id)
        
        # 删除测试智能体
        test_delete_agent(agent_id)
    
    print("\n=== 测试完成 ===")