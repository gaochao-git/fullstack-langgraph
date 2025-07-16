"""
主图 - 智能路由到SOP诊断子图或普通问答子图
"""

import os
import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END, START
from langchain_core.messages import SystemMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from .configuration import Configuration
from .state import DiagnosticState, QuestionAnalysis
from .schemas import IntentAnalysisOutput
from .utils import compile_graph_with_checkpointer
from .sop_diagnosis_subgraph import create_sop_diagnosis_subgraph
from .general_qa_subgraph import create_general_qa_subgraph

logger = logging.getLogger(__name__)


def analyze_intent_node(state: DiagnosticState, config: RunnableConfig) -> Dict[str, Any]:
    """
    意图分析节点 - 判断用户是否需要SOP诊断还是普通问答
    """
    print(f"✅ 执行节点: analyze_intent_node")
    
    configurable = Configuration.from_runnable_config(config)
    messages = state.get("messages", [])
    
    if not messages:
        return {"intent": "general_qa"}
    
    user_question = messages[-1].content if messages else ""
    
    # 使用LLM分析用户意图
    llm = configurable.create_llm(
        model_name=configurable.query_generator_model,
        temperature=0.1  # 低温度确保分类准确
    )
    
    intent_analysis_prompt = f"""
你是一个专业的运维助手意图分析器。请分析用户的问题，判断用户是否需要故障诊断SOP还是普通问答。

判断标准：
1. 故障诊断SOP (sop_diagnosis)：
   - 用户明确提到故障、报错、异常等问题
   - 用户提到需要排查、诊断、解决问题
   - 用户描述了具体的故障现象
   - 用户提到了IP、时间、错误信息等故障要素
   - 关键词：故障、报错、异常、排查、诊断、SOP、问题解决

2. 普通问答 (general_qa)：
   - 用户询问技术知识、操作方法
   - 用户进行日常聊天、问候
   - 用户询问系统信息、配置说明
   - 用户询问历史记录、状态查询
   - 不涉及具体故障排查的技术问题

用户问题：{user_question}

请分析用户意图，返回分类结果和简要理由。
"""
    
    structured_llm = llm.with_structured_output(IntentAnalysisOutput)
    result = structured_llm.invoke(intent_analysis_prompt)
    
    logger.info(f"意图分析结果: {result.intent} - {result.reason}")
    
    return {
        "intent": result.intent,
        "intent_reason": result.reason
    }


def route_to_subgraph(state: DiagnosticState, config: RunnableConfig) -> Literal["sop_diagnosis", "general_qa"]:
    """
    路由函数 - 根据意图分析结果决定进入哪个子图
    """
    print(f"✅ 执行路由函数: route_to_subgraph")
    
    intent = state.get("intent", "general_qa")
    
    logger.info(f"路由决策: {intent}")
    print(f"✅ 路由结果: {intent}")
    
    return intent


def create_main_graph():
    """
    创建主图 - 包含路由逻辑和两个子图
    基于官方文档的子图集成模式
    """
    
    # 创建主图
    builder = StateGraph(DiagnosticState, config_schema=Configuration)
    
    # 添加意图分析节点
    builder.add_node("analyze_intent", analyze_intent_node)
    
    # 创建并添加子图 - 直接作为节点集成
    sop_diagnosis_subgraph = create_sop_diagnosis_subgraph()
    general_qa_subgraph = create_general_qa_subgraph()
    
    # 将子图作为节点添加到主图中
    # 根据官方文档，子图可以直接作为节点使用
    builder.add_node("sop_diagnosis", sop_diagnosis_subgraph)
    builder.add_node("general_qa", general_qa_subgraph)
    
    # 设置路由 - 从意图分析开始
    builder.add_edge(START, "analyze_intent")
    
    # 条件路由到不同的子图
    builder.add_conditional_edges(
        "analyze_intent",
        route_to_subgraph,
        {
            "sop_diagnosis": "sop_diagnosis",
            "general_qa": "general_qa"
        }
    )
    
    # 两个子图执行完成后都结束
    builder.add_edge("sop_diagnosis", END)
    builder.add_edge("general_qa", END)
    
    return builder


# 编译主图
def compile_main_graph():
    """编译主图"""
    builder = create_main_graph()
    checkpointer_type = os.getenv("CHECKPOINTER_TYPE", "memory")
    return compile_graph_with_checkpointer(builder, checkpointer_type)


# 导出编译后的图
graph = compile_main_graph()