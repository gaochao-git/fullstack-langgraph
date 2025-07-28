"""
MCP模块测试数据和fixture
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List


@pytest.fixture
def sample_mcp_server_data() -> Dict[str, Any]:
    """样本MCP服务器数据"""
    return {
        "server_id": "test_mcp_001",
        "server_name": "测试MCP服务器",
        "server_uri": "http://localhost:3001/sse",
        "server_description": "这是一个用于测试的MCP服务器",
        "is_enabled": "on",
        "connection_status": "connected",
        "auth_type": "none",
        "auth_token": None,
        "api_key_header": None,
        "read_timeout_seconds": 10,
        "server_tools": [
            {
                "name": "test_tool",
                "description": "测试工具"
            }
        ],
        "server_config": {
            "retry_count": 3,
            "retry_delay": 1
        },
        "team_name": "test_team",
        "create_by": "test_user",
        "create_time": datetime.utcnow(),
        "update_time": datetime.utcnow()
    }


@pytest.fixture
def sample_mcp_create_data() -> Dict[str, Any]:
    """MCP服务器创建请求数据"""
    return {
        "server_id": "test_mcp_create_001",
        "server_name": "创建测试MCP服务器",
        "server_uri": "http://localhost:3002/sse",
        "server_description": "用于测试创建功能的MCP服务器",
        "is_enabled": "on",
        "connection_status": "disconnected",
        "auth_type": "api_key",
        "auth_token": "test_token_123",
        "api_key_header": "X-API-Key",
        "read_timeout_seconds": 15,
        "server_tools": [],
        "server_config": {},
        "team_name": "create_test_team",
        "create_by": "create_test_user"
    }


@pytest.fixture
def sample_mcp_update_data() -> Dict[str, Any]:
    """MCP服务器更新请求数据"""
    return {
        "server_name": "更新后的MCP服务器",
        "server_description": "更新后的服务器描述",
        "server_uri": "https://localhost:3001/sse",
        "is_enabled": "off",
        "read_timeout_seconds": 20,
        "server_config": {
            "retry_count": 5,
            "retry_delay": 2,
            "max_connections": 10
        }
    }


@pytest.fixture
def sample_mcp_test_request() -> Dict[str, Any]:
    """MCP连接测试请求数据"""
    return {
        "url": "http://localhost:3001/sse"
    }


@pytest.fixture
def multiple_mcp_servers() -> List[Dict[str, Any]]:
    """多个MCP服务器测试数据"""
    return [
        {
            "server_id": f"test_mcp_{i:03d}",
            "server_name": f"测试MCP服务器 {i}",
            "server_uri": f"http://localhost:{3000+i}/sse",
            "server_description": f"第{i}个测试MCP服务器",
            "is_enabled": "on" if i % 2 == 0 else "off",
            "connection_status": ["connected", "disconnected", "error"][i % 3],
            "auth_type": ["none", "api_key", "bearer"][i % 3],
            "read_timeout_seconds": 10 + i,
            "server_tools": [{"name": f"tool_{i}", "description": f"工具{i}"}],
            "team_name": f"team_{i % 2}",
            "create_by": "batch_test_user"
        }
        for i in range(1, 6)
    ]