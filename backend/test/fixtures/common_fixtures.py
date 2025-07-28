"""
全局共享测试fixtures
跨模块的通用测试数据和配置
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_datetime():
    """模拟的固定时间"""
    return datetime(2024, 1, 1, 12, 0, 0)


@pytest.fixture
def common_user_data():
    """通用用户数据"""
    return {
        "user_id": "test_user_001",
        "username": "test_user",
        "email": "test@example.com",
        "team_name": "test_team",
        "role": "admin"
    }


@pytest.fixture
def common_pagination_params():
    """通用分页参数"""
    return {
        "limit": 10,
        "offset": 0,
        "page": 1,
        "size": 10
    }


@pytest.fixture
def mock_logger():
    """模拟的日志器"""
    return Mock()


@pytest.fixture
def sample_error_response():
    """样本错误响应"""
    return {
        "error": "Test error",
        "message": "This is a test error message",
        "code": "TEST_ERROR",
        "timestamp": datetime.utcnow().isoformat()
    }


@pytest.fixture
def sample_success_response():
    """样本成功响应"""
    return {
        "success": True,
        "message": "Operation completed successfully",
        "timestamp": datetime.utcnow().isoformat()
    }