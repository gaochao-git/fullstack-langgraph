import os
import requests
import json

from agent.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send, interrupt, Command
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig

from agent.state import (
    OverallState,
    QueryGenerationState,
    ReflectionState,
    WebSearchState,
)
from agent.configuration import Configuration
from agent.prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from langchain_deepseek import ChatDeepSeek
from agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

load_dotenv()

if os.getenv("DEEPSEEK_API_KEY") is None:
    raise ValueError("DEEPSEEK_API_KEY is not set")

# DeepSeek 客户端初始化（如果将来需要用于网络搜索集成）


# 节点
def generate_query(state: OverallState, config: RunnableConfig) -> QueryGenerationState:
    """LangGraph 节点，基于用户问题生成搜索查询。

    使用 DeepSeek 模型根据用户问题创建优化的搜索查询，用于网络研究。

    参数：
        state: 包含用户问题的当前图状态
        config: 可运行配置，包括 LLM 提供商设置

    返回：
        包含状态更新的字典，包括 search_query 键，其中包含生成的查询
    """
    configurable = Configuration.from_runnable_config(config)

    # 检查自定义初始搜索查询数量
    if state.get("initial_search_query_count") is None:
        state["initial_search_query_count"] = configurable.number_of_initial_queries

    # 初始化 DeepSeek Chat
    llm = ChatDeepSeek(
        model=configurable.query_generator_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    structured_llm = llm.with_structured_output(SearchQueryList)

    # 格式化提示词
    current_date = get_current_date()
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        number_queries=state["initial_search_query_count"],
    )
    # 生成搜索查询
    result = structured_llm.invoke(formatted_prompt)
    return {"search_query": result.query}


def continue_to_web_research(state: QueryGenerationState):
    """LangGraph 节点，将搜索查询发送到网络研究节点。

    用于生成 n 个网络研究节点，每个搜索查询对应一个。
    """
    return [
        Send("web_research", {"search_query": search_query, "id": int(idx)})
        for idx, search_query in enumerate(state["search_query"])
    ]


def web_research(state: WebSearchState, config: RunnableConfig) -> OverallState:
    """LangGraph 节点，直接调用 searchapi.io 百度引擎进行网络研究。"""
    # 先询问用户是否允许搜索
    human_response = interrupt({
        "message": f"是否允许使用百度搜索以下内容？\n\n搜索内容: {state['search_query']}\n\n选择'继续'允许搜索，选择'取消'结束搜索。",
        "current_query": state["search_query"],
    })

    if not human_response:
        return {
            "sources_gathered": [],
            "search_query": [state["search_query"]],
            "web_research_result": ["用户取消了搜索操作"],
            "messages": [AIMessage(content="用户取消了搜索操作，研究过程已结束。")]
        }

    api_key = os.getenv("SEARCHAPI_API_KEY")
    url = "https://www.searchapi.io/api/v1/search"
    params = {
        "engine": "baidu",
        "q": state["search_query"],
        "api_key": api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            results = data.get("organic_results", [])
            if not results:
                result = "未找到相关结果。"
            else:
                lines = []
                for item in results[:5]:
                    title = item.get("title", "")
                    link = item.get("link", "")
                    snippet = item.get("snippet", "")
                    lines.append(f"【{title}】\n{link}\n{snippet}\n")
                result = "\n".join(lines)
        except Exception as e:
            result = f"解析搜索结果失败: {e}"
    else:
        result = f"API请求失败，状态码: {response.status_code}, 错误信息: {response.text}"

    sources_gathered = [{
        "short_url": f"searchapi_{state['id']}",
        "value": "searchapi.io 结果",
        "title": "searchapi.io"
    }]
    print(1111111111111, result)

    return {
        "sources_gathered": sources_gathered,
        "search_query": [state["search_query"]],
        "web_research_result": [result]
    }


def reflection(state: OverallState, config: RunnableConfig) -> ReflectionState:
    """LangGraph 节点，识别知识差距并生成潜在的后续查询。

    分析当前摘要以识别需要进一步研究的领域并生成潜在的后续查询。
    使用结构化输出以 JSON 格式提取后续查询。

    参数：
        state: 包含运行摘要和研究主题的当前图状态
        config: 可运行配置，包括 LLM 提供商设置

    返回：
        包含状态更新的字典，包括 search_query 键，其中包含生成的后续查询
    """
    # 增加研究循环计数
    state["research_loop_count"] = state.get("research_loop_count", 0) + 1
    research_loop_count = state["research_loop_count"]
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model", configurable.reflection_model)

    # 格式化提示词
    current_date = get_current_date()
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n\n---\n\n".join(state["web_research_result"]),
    )
    # 初始化推理模型
    llm = ChatDeepSeek(
        model=reasoning_model,
        temperature=1.0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    result = llm.with_structured_output(Reflection).invoke(formatted_prompt)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "research_loop_count": state["research_loop_count"],
        "number_of_ran_queries": len(state["search_query"]),
    }


def evaluate_research(
    state: ReflectionState,
    config: RunnableConfig,
) -> OverallState:
    """LangGraph 路由函数，确定研究流程中的下一步。

    通过决定是否继续收集信息或根据配置的最大研究循环数完成摘要来控制研究循环。

    参数：
        state: 包含研究循环计数的当前图状态
        config: 可运行配置，包括 max_research_loops 设置

    返回：
        指示要访问的下一个节点的字符串字面量（"web_research" 或 "finalize_summary"）
    """
    configurable = Configuration.from_runnable_config(config)
    max_research_loops = (
        state.get("max_research_loops")
        if state.get("max_research_loops") is not None
        else configurable.max_research_loops
    )
    if state["is_sufficient"] or state["research_loop_count"] >= max_research_loops:
        return "finalize_answer"
    else:
        return [
            Send(
                "web_research",
                {
                    "search_query": follow_up_query,
                    "id": state["number_of_ran_queries"] + int(idx),
                },
            )
            for idx, follow_up_query in enumerate(state["follow_up_queries"])
        ]


def finalize_answer(state: OverallState, config: RunnableConfig):
    """LangGraph 节点，完成研究摘要。

    通过去重和格式化来源，然后将它们与运行摘要结合起来创建具有适当引用的结构良好的研究报告，准备最终输出。

    参数：
        state: 包含运行摘要和收集来源的当前图状态

    返回：
        包含状态更新的字典，包括 running_summary 键，其中包含格式化的带有来源的最终摘要
    """
    # 检查是否需要中断询问用户（当研究循环次数较多时）  
    configurable = Configuration.from_runnable_config(config)
    reasoning_model = state.get("reasoning_model") or configurable.answer_model

    # 格式化提示词
    current_date = get_current_date()
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(state["messages"]),
        summaries="\n---\n\n".join(state["web_research_result"]),
    )

    # 初始化推理模型，默认为 DeepSeek Chat
    llm = ChatDeepSeek(
        model=reasoning_model,
        temperature=0,
        max_retries=2,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
    )
    result = llm.invoke(formatted_prompt)

    # 用原始 URL 替换短 URL，并将所有使用的 URL 添加到 sources_gathered
    unique_sources = []
    for source in state["sources_gathered"]:
        if source["short_url"] in result.content:
            result.content = result.content.replace(
                source["short_url"], source["value"]
            )
            unique_sources.append(source)

    return {
        "messages": [AIMessage(content=result.content)],
        "sources_gathered": unique_sources,
    }


# 创建我们的 Agent 图
builder = StateGraph(OverallState, config_schema=Configuration)

# 定义我们将循环的节点
builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

# 将入口点设置为 `generate_query`
# 这意味着这个节点是第一个被调用的
builder.add_edge(START, "generate_query")
# 添加条件边以在并行分支中继续搜索查询
builder.add_conditional_edges(
    "generate_query", continue_to_web_research, ["web_research"]
)
# 反思网络研究
builder.add_edge("web_research", "reflection")
# 评估研究
builder.add_conditional_edges(
    "reflection", evaluate_research, ["web_research", "finalize_answer"]
)
# 完成答案
builder.add_edge("finalize_answer", END)

graph = builder.compile(name="pro-search-agent")
