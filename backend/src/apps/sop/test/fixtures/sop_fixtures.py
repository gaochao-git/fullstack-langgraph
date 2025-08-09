"""
SOP模块测试数据和fixture
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from src.shared.db.models import now_shanghai


@pytest.fixture
def sample_sop_data() -> Dict[str, Any]:
    """样本SOP数据"""
    return {
        "sop_id": "test_sop_001",
        "sop_title": "测试SOP模板",
        "sop_description": "这是一个用于测试的SOP模板",
        "sop_category": "测试分类",
        "sop_severity": "medium",
        "sop_steps": [
            "第一步：准备测试环境",
            "第二步：执行测试用例", 
            "第三步：验证测试结果",
            "第四步：清理测试数据"
        ],
        "team_name": "test_team",
        "create_by": "test_user",
        "create_time": now_shanghai(),
        "update_time": now_shanghai()
    }


@pytest.fixture
def sample_sop_create_data() -> Dict[str, Any]:
    """SOP创建请求数据"""
    return {
        "sop_id": "test_sop_create_001",
        "sop_title": "创建测试SOP",
        "sop_description": "用于测试创建功能的SOP",
        "sop_category": "创建测试",
        "sop_severity": "high",
        "steps": [
            "准备创建环境",
            "执行创建操作",
            "验证创建结果"
        ],
        "team_name": "create_test_team",
        "create_by": "create_test_user"
    }


@pytest.fixture
def sample_sop_update_data() -> Dict[str, Any]:
    """SOP更新请求数据"""
    return {
        "sop_title": "更新后的SOP标题",
        "sop_description": "更新后的SOP描述",
        "sop_severity": "low", 
        "steps": [
            "更新步骤1",
            "更新步骤2"
        ]
    }


@pytest.fixture
def sample_sop_query_params() -> Dict[str, Any]:
    """SOP查询参数"""
    return {
        "category": "测试分类",
        "severity": "medium",
        "team_name": "test_team",
        "search": "测试",
        "limit": 10,
        "offset": 0
    }


@pytest.fixture
def multiple_sop_data() -> list[Dict[str, Any]]:
    """多个SOP测试数据"""
    return [
        {
            "sop_id": f"test_sop_{i:03d}",
            "sop_title": f"测试SOP {i}",
            "sop_description": f"第{i}个测试SOP",
            "sop_category": "批量测试",
            "sop_severity": ["low", "medium", "high"][i % 3],
            "sop_steps": [f"步骤{j}" for j in range(1, 4)],
            "team_name": f"team_{i % 2}",
            "create_by": "batch_test_user"
        }
        for i in range(1, 6)
    ]