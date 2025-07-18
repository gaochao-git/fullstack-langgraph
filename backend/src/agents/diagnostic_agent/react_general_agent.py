"""
基于 create_react_agent 的新通用智能体
用于替代原有的 general_qa_subgraph
"""

import logging
from typing import Dict, Any
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import create_react_agent

from .configuration import Configuration
from .tools import all_tools
from .state import DiagnosticState

logger = logging.getLogger(__name__)

# 通用智能体的系统提示词
GENERAL_AGENT_PROMPT = """你是一个专业的运维技术助手，专门帮助用户解答各种技术问题和提供运维支持。

你的核心能力：
1. 技术问答 - 回答各种运维、开发、系统管理相关问题
2. 故障排查 - 协助用户进行基础的故障分析和排查
3. 配置指导 - 提供系统配置、软件部署的建议和指导
4. 最佳实践 - 分享行业最佳实践和经验
5. 工具使用 - 灵活使用各种运维工具来解决问题

可用工具类型：
- SSH工具：系统信息查询、进程分析、服务状态检查、日志分析、命令执行
- SOP工具：查找和参考标准操作程序
- MySQL工具：数据库连接、查询执行、性能监控
- Elasticsearch工具：集群状态查询、索引管理、数据分析
- Zabbix工具：监控数据获取、告警信息查询
- 通用工具：时间获取等实用功能

工作原则：
1. 理解用户问题的核心需求
2. 选择合适的工具来获取必要信息
3. 基于获取的信息提供准确、实用的建议
4. 如果问题复杂，提供分步骤的解决方案
5. 始终考虑安全性和最佳实践

注意事项：
- 优先提供安全可靠的解决方案
- 对于复杂操作，建议用户先在测试环境验证
- 如果涉及数据安全，提醒用户注意备份
- 提供具体可执行的操作步骤
- 如果需要更多信息才能准确回答，主动询问

请以友好、专业的态度协助用户解决技术问题。"""


def create_react_general_subgraph():
    """
    创建基于 create_react_agent 的通用智能体子图
    包装在我们自己的状态图中，以保持兼容性
    """
    # 从配置中获取LLM实例
    def get_llm_from_config(config: RunnableConfig):
        configurable = Configuration.from_runnable_config(config)
        return configurable.create_llm(
            model_name=configurable.query_generator_model,
            temperature=configurable.model_temperature
        )
    
    # 创建带工具审批的 react agent 节点
    def create_react_agent_node(state: DiagnosticState, config: RunnableConfig):
        """创建 react agent 节点"""
        print(f"✅ 执行新通用智能体: react_general_agent")
        print(f"🔍 react_general_agent - 输入状态: {list(state.keys())}")
        
        # 动态获取LLM
        llm = get_llm_from_config(config)
        
        # 创建 react agent，使用 interrupt_before=["tools"] 实现工具审批
        react_agent = create_react_agent(
            model=llm,
            tools=all_tools,
            prompt=GENERAL_AGENT_PROMPT,
            interrupt_before=["tools"],  # 在工具执行前暂停，等待审批
        )
        
        # 准备消息 - 转换为 react agent 需要的格式
        messages = state.get("messages", [])
        react_state = {"messages": messages}
        
        print(f"🚀 react_general_agent - 开始调用 create_react_agent...")
        
        # 调用 react agent
        result = react_agent.invoke(react_state, config)
        
        print(f"✅ react_general_agent - 调用完成")
        print(f"📝 react_general_agent - 返回消息数量: {len(result.get('messages', []))}")
        
        # 返回更新的消息，保持与原有状态的兼容
        return {"messages": result.get("messages", [])}
    
    # 创建包装的状态图
    from langgraph.graph import StateGraph, START, END
    builder = StateGraph(DiagnosticState)
    
    # 添加 react agent 节点
    builder.add_node("react_general_agent", create_react_agent_node)
    
    # 设置边
    builder.add_edge(START, "react_general_agent")
    builder.add_edge("react_general_agent", END)
    
    print(f"✅ 创建新的 create_react_agent 通用智能体子图")
    return builder.compile()