"""
Deep Agent 配置
注意：Deep Agent 是一个通用框架，通过前端配置来实现不同功能
"""

# Deep Agent 不需要装饰器注册，因为它是一个通用模板
# 类似于 generic_agent，通过前端创建和配置

DEEP_AGENT_FEATURES = {
    "planning": True,      # 支持任务规划（write_todos）
    "file_system": True,   # 支持虚拟文件系统
    "sub_agents": True,    # 支持子任务（简化版）
    "flexible": True       # 灵活配置
}