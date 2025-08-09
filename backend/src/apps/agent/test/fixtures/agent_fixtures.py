"""
Agent模块测试数据和fixture
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List
from src.shared.db.models import now_shanghai


@pytest.fixture
def sample_agent_config_data() -> Dict[str, Any]:
    """样本智能体配置数据"""
    return {
        "agent_id": "test_agent_001",
        "agent_name": "测试智能体",
        "agent_description": "这是一个用于测试的智能体",
        "agent_type": "diagnostic",
        "agent_config": {
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 2000,
            "tools": ["search", "analyze"]
        },
        "is_enabled": True,
        "team_name": "test_team",
        "create_by": "test_user",
        "create_time": now_shanghai(),
        "update_time": now_shanghai()
    }


@pytest.fixture
def sample_agent_create_data() -> Dict[str, Any]:
    """智能体创建请求数据"""
    return {
        "agent_id": "test_agent_create_001",
        "agent_name": "创建测试智能体",
        "agent_description": "用于测试创建功能的智能体",
        "agent_type": "research",
        "agent_config": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.5,
            "tools": ["web_search", "document_analysis"]
        },
        "is_enabled": True,
        "team_name": "create_test_team",
        "create_by": "create_test_user"
    }


@pytest.fixture
def sample_agent_update_data() -> Dict[str, Any]:
    """智能体更新请求数据"""
    return {
        "agent_name": "更新后的智能体名称",
        "agent_description": "更新后的智能体描述",
        "agent_config": {
            "model": "gpt-4",
            "temperature": 0.8,
            "max_tokens": 1500
        },
        "is_enabled": False
    }


@pytest.fixture
def multiple_agent_data() -> List[Dict[str, Any]]:
    """多个智能体测试数据"""
    return [
        {
            "agent_id": f"test_agent_{i:03d}",
            "agent_name": f"测试智能体 {i}",
            "agent_description": f"第{i}个测试智能体",
            "agent_type": ["diagnostic", "research", "generic"][i % 3],
            "agent_config": {
                "model": ["gpt-3.5-turbo", "gpt-4"][i % 2],
                "temperature": 0.5 + (i * 0.1),
                "tools": [f"tool_{j}" for j in range(1, 3)]
            },
            "is_enabled": i % 2 == 0,
            "team_name": f"team_{i % 2}",
            "create_by": "batch_test_user"
        }
        for i in range(1, 6)
    ]