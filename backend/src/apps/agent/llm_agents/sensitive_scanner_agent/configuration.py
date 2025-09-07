"""
敏感数据扫描智能体配置
"""

# Agent 装饰器配置，首次注册使用，如果后续需要更新配置，需要手动更新数据库
INIT_AGENT_CONFIG = {
    "agent_id": "sensitive_scanner_agent",
    "description": "敏感数据扫描助手",
    "agent_type": "安全检查",
    "capabilities": ["敏感数据识别", "隐私信息扫描", "数据脱敏建议"],
    "version": "1.0.0",
    "icon": "SafetyOutlined",
    "owner": "gaochao"
}