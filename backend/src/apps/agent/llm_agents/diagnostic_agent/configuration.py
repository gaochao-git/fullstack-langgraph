"""
诊断智能体配置
"""

# Agent 装饰器配置,首次注册使用，如果后续需要更新，需要手动更新数据库
INIT_AGENT_CONFIG = {
    "agent_id": "diagnostic_agent",
    "description": "智能运维诊断助手",
    "agent_type": "故障诊断",
    "capabilities": ["故障诊断","性能分析", "日志分析","系统监控","根因分析","解决方案推荐"],
    "version": "1.0.0",
    "icon": "MedicineBoxOutlined",
    "owner": "gaochao"
}
