"""
示例智能体配置
"""

# Agent 装饰器配置，首次注册使用，如果后续需要更新，需要手动更新数据库
INIT_AGENT_CONFIG = {
    "agent_id": "example_agent",
    "description": "示例助手 - 展示自定义工作流",
    "agent_type": "内置",
    "capabilities": ["文本分析", "字数统计", "工作流演示", "条件路由"],
    "version": "1.0.0",
    "icon": "WorkflowOutlined",
    "owner": "system"
}