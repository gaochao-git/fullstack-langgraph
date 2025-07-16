"""
故障诊断代理工具函数模块
包含各种辅助工具函数
"""

import json
import logging
import os
from datetime import datetime
from langchain_core.messages import ToolMessage
from .state import SOPStep

logger = logging.getLogger(__name__)

def get_current_datetime():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 排除的SOP工具名常量
EXCLUDED_SOP_TOOLS = {"get_sop_content", "get_sop_detail", "list_sops", "search_sops"}

# 白名单工具：无需审批的安全工具
SAFE_TOOLS_WHITELIST = {
    "get_sop_content", "get_sop_detail", "list_sops", "search_sops",  # SOP相关工具
    "ping", "nslookup", "dig",  # 基础网络查询工具
    "get_system_info", "get_process_info",  # 只读系统信息工具
    "check_port_status", "get_network_status",  # 网络状态查询
    "get_log_info", "search_logs",  # 日志查询工具
    # 可以根据实际需求添加更多安全工具
}


def merge_field(new_value, old_value, field_name=None):
    # 合并信息：优先使用新信息，无新信息时保持原值
    # 如果新值有效且不是待提取，使用新值
    if new_value and new_value != "待提取" and new_value.strip():
        return new_value
    # 如果旧值有效且不是待提取，保持旧值
    elif old_value and old_value != "待提取" and old_value.strip():
        return old_value
    # 特殊处理：如果是时间字段且没有明确时间，使用当前时间
    elif field_name == "fault_time":
        return get_current_datetime()
    # 否则返回待提取
    else:
        return "待提取"


def find_matching_sop_step(tool_calls, raw_sop_data):
    """
    查找与工具调用匹配的SOP步骤
    
    Args:
        tool_calls: 工具调用列表
        raw_sop_data: 原始SOP数据
        
    Returns:
        SOPStep对象或None
    """
    if not raw_sop_data or not tool_calls:
        return None
        
    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "")
        tool_args = tool_call.get("args", {})
        
        # 跳过SOP加载相关的工具调用
        if tool_name in EXCLUDED_SOP_TOOLS:
            continue
            
        # 在原始SOP步骤中查找匹配的工具和命令
        for sop_step in raw_sop_data.get("steps", []):
            step_tool = sop_step.get("tool", "")
            step_command = sop_step.get("command", "")
            
            # 检查工具名称是否匹配
            if tool_name == step_tool:
                # 如果有命令参数，检查命令是否匹配
                if "command" in tool_args:
                    if tool_args["command"] == step_command:
                        return _create_sop_step_from_data(sop_step)
                else:
                    # 没有具体命令参数，只根据工具匹配
                    return _create_sop_step_from_data(sop_step)
    
    return None


def _create_sop_step_from_data(sop_step_data):
    """
    从SOP步骤数据创建SOPStep对象
    
    Args:
        sop_step_data: SOP步骤原始数据
        
    Returns:
        SOPStep对象
    """
    return SOPStep(
        title=sop_step_data.get("action", ""),
        description=sop_step_data.get("description", ""),
        action=sop_step_data.get("action", ""),
        requires_approval=sop_step_data.get("requires_approval", False),
        status="pending",
        approved=False,
        approved_at=None,
        approval_id=None
    )


def extract_raw_sop_data(messages):
    """
    从消息中提取原始SOP数据
    
    Args:
        messages: 消息列表
        
    Returns:
        原始SOP数据字典或None
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage) and msg.name == "get_sop_content":
            try:
                result = json.loads(msg.content)
                if result.get("success") and result.get("sop_content"):
                    return result["sop_content"]
            except (json.JSONDecodeError, TypeError):
                continue
    return None


def check_approval_needed(state):
    """
    检查是否需要审批，返回审批信息或None
    
    Returns:
        dict: 包含审批信息的字典，或None表示无需审批
    """
    messages = state.get("messages", [])
    if not messages:
        return None
    
    last_message = messages[-1]
    if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
        return None
    
    tool_calls = last_message.tool_calls
    question_analysis = state.get("question_analysis")
    
    # 获取原始SOP数据
    raw_sop_data = extract_raw_sop_data(messages)
    current_step_info = None
    
    if raw_sop_data:
        # 有SOP数据，查找匹配的SOP步骤
        current_step_info = find_matching_sop_step(tool_calls, raw_sop_data)
    else:
        # 无SOP数据，检查白名单
        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            if tool_name not in SAFE_TOOLS_WHITELIST:
                # 创建虚拟审批步骤
                current_step_info = SOPStep(
                    title=f"执行工具: {tool_name}",
                    description=f"由于无法获取SOP数据且工具不在白名单中，为安全起见需要审批",
                    action=f"execute_{tool_name}",
                    requires_approval=True,
                    status="pending"
                )
                break
    
    # 检查是否需要审批
    if current_step_info and current_step_info.requires_approval:
        sop_id = question_analysis.sop_id if question_analysis else "no_sop"
        step_id = f"{sop_id}:{current_step_info.action}"
        
        return {
            "step_info": current_step_info,
            "step_id": step_id,
            "tool_calls": tool_calls,
            "sop_id": sop_id
        }
    
    return None


def is_already_approved(state, approval_info):
    """检查步骤是否已经审批过"""
    sop_detail = state.get("sop_detail")
    if not sop_detail or not sop_detail.steps:
        return False
    
    step_id = approval_info["step_id"]
    sop_id = approval_info["sop_id"]
    action = approval_info["step_info"].action
    
    # 在SOP步骤中查找匹配的步骤
    for step in sop_detail.steps:
        if step.action == action and step.approved:
            return True
    
    return False


def is_sop_loaded(sop_detail):
    """
    判断SOP是否已加载
    
    Args:
        sop_detail: SOPDetail对象
        
    Returns:
        bool: 是否已加载
    """
    return bool(sop_detail.sop_id and sop_detail.steps)


def process_sop_loading(messages, current_sop_detail):
    """
    处理SOP加载结果
    
    Returns:
        SOPDetail: 更新后的SOP详情
    """
    if not (messages and isinstance(messages[-1], ToolMessage) and 
            messages[-1].name == "get_sop_content"):
        return current_sop_detail
    
    try:
        from .state import SOPDetail, SOPStep
        result = json.loads(messages[-1].content)
        if not (result.get("success") and result.get("sop_content")):
            return current_sop_detail
            
        sop_content = result["sop_content"]
        
        # 解析步骤
        steps = [
            SOPStep(
                title=step_data.get("title", ""),
                description=step_data.get("description", ""),
                action=step_data.get("action", ""),
                requires_approval=step_data.get("requires_approval", False),
                status="pending",
                approved=False,
                approved_at=None,
                approval_id=None
            )
            for step_data in sop_content.get("steps", [])
        ]
        
        # 创建SOPDetail对象
        updated_sop_detail = SOPDetail(
            sop_id=sop_content.get("id", ""),
            title=sop_content.get("title", ""),
            description=sop_content.get("description", ""),
            steps=steps,
            total_steps=len(steps)
        )
        
        logger.info(f"SOP加载成功: {updated_sop_detail.sop_id}, 步骤数: {len(steps)}")
        return updated_sop_detail
        
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"解析SOP内容失败: {e}")
        return current_sop_detail


def update_diagnosis_step(messages, current_step):
    """
    更新诊断步骤计数
    
    Returns:
        tuple: (new_step, has_new_execution, tool_name)
    """
    if not (messages and isinstance(messages[-1], ToolMessage)):
        return current_step, False, None
    
    last_tool_name = messages[-1].name
    
    # 只有非SOP工具才算诊断步骤
    if last_tool_name not in EXCLUDED_SOP_TOOLS:
        new_step = current_step + 1
        logger.info(f"检测到诊断工具执行: {last_tool_name}，步骤数更新为: {new_step}")
        return new_step, True, last_tool_name
    else:
        return current_step, False, last_tool_name


def check_diagnosis_completion(current_step, max_steps, sop_detail):
    """
    检查诊断是否完成
    
    Returns:
        tuple: (is_complete, termination_reason)
    """
    # 达到最大步骤限制
    if current_step >= max_steps:
        logger.warning(f"达到最大步骤限制退出: {current_step}/{max_steps}")
        return True, "max_steps_reached"
    
    # 检查SOP是否已完全执行
    if (sop_detail.steps and len(sop_detail.steps) > 0 and 
        current_step >= len(sop_detail.steps) and current_step >= 3):
        logger.info(f"SOP步骤完成退出: {current_step} >= {len(sop_detail.steps)}")
        return True, "sop_completed"
    
    return False, "continue"


def check_info_sufficient(state):
    """检查信息是否充足"""
    print(f"✅ 执行路由函数: check_info_sufficient")
    from .state import QuestionAnalysis
    question_analysis = state.get("question_analysis", QuestionAnalysis())
    if question_analysis.info_sufficient:
        print(f"✅ 路由结果: plan_tools")
        return "plan_tools"
    else:
        print(f"✅ 路由结果: handle_insufficient_info")
        return "handle_insufficient_info"


def check_tool_calls(state):
    """检查是否有工具调用需要执行"""
    messages = state.get("messages", [])
    if not messages:
        return "reflection"
    
    last_message = messages[-1]
    has_tool_calls = hasattr(last_message, 'tool_calls') and last_message.tool_calls
    
    if has_tool_calls:
        return "approval"
    else:
        return "reflection"


def save_graph_image(graph, mode_name, filename="graph.png"):
    """保存图结构图像到文件"""
    try:
        graph_image = graph.get_graph().draw_mermaid_png()
        current_dir = os.path.dirname(os.path.abspath(__file__))
        graph_image_path = os.path.join(current_dir, filename)
        with open(graph_image_path, "wb") as f:
            f.write(graph_image)
        print(f"📝 {mode_name}：图已保存到 {graph_image_path}")
    except Exception as e:
        logger.warning(f"保存图结构图像失败: {e}")


def auto_generate_subgraph_images():
    """程序启动时自动生成所有子图的图片"""
    try:
        # 导入子图创建函数
        from .sop_diagnosis_subgraph import create_sop_diagnosis_subgraph
        from .general_qa_subgraph import create_general_qa_subgraph
        
        # 生成SOP诊断子图
        try:
            sop_subgraph = create_sop_diagnosis_subgraph()
            save_graph_image(sop_subgraph, "SOP诊断子图", "graph_sop_diagnosis_subgraph.png")
        except Exception as e:
            logger.warning(f"生成SOP诊断子图失败: {e}")
        
        # 生成普通问答子图
        try:
            qa_subgraph = create_general_qa_subgraph()
            save_graph_image(qa_subgraph, "普通问答子图", "graph_general_qa_subgraph.png")
        except Exception as e:
            logger.warning(f"生成普通问答子图失败: {e}")
            
    except ImportError as e:
        logger.warning(f"导入子图模块失败，跳过子图图片生成: {e}")


def compile_graph_with_checkpointer(builder, checkpointer_type="memory"):
    """
    根据checkpointer类型编译图
    
    Args:
        builder: StateGraph构建器
        checkpointer_type: checkpointer类型 ("memory" 或 "postgres")
        
    Returns:
        tuple: (graph, mode_name)
    """
    # 首先自动生成所有子图的图片
    auto_generate_subgraph_images()
    
    if checkpointer_type == "postgres":
        # PostgreSQL模式：不在这里编译，在API请求时用async with编译
        graph = builder.compile(name="diagnostic-agent")
        save_graph_image(graph, "PostgreSQL模式")
        graph = None
        print("📝 PostgreSQL模式：图将在API请求时用async with编译")
        return graph, "PostgreSQL模式"
    else:
        # 内存模式：直接使用MemorySaver
        from langgraph.checkpoint.memory import MemorySaver
        checkpointer = MemorySaver()
        graph = builder.compile(checkpointer=checkpointer, name="diagnostic-agent")
        save_graph_image(graph, "内存模式")
        print(f"📝 内存模式：图已编译完成")
        return graph, "内存模式"


def extract_diagnosis_results_from_messages(messages, max_results: int = 10):
    """
    从 messages 中提取诊断结果
    
    Args:
        messages: 消息列表
        max_results: 最大提取结果数量
    
    Returns:
        格式化的诊断结果列表
    """
    diagnosis_results = []
    
    for message in messages:
        if isinstance(message, ToolMessage):
            # 过滤掉一些不需要的工具
            if message.name in ['QuestionInfoExtraction', 'DiagnosisReflectionOutput']:
                continue
                
            # 格式化工具结果
            result = f"Tool: {message.name}, Result: {message.content}"
            diagnosis_results.append(result)
    
    # 返回最近的 max_results 个结果
    return diagnosis_results[-max_results:] if diagnosis_results else []


def format_diagnosis_results_for_prompt(messages, max_results: int = 5):
    """
    格式化诊断结果用于提示词
    
    Args:
        messages: 消息列表
        max_results: 最大结果数量
    
    Returns:
        格式化的字符串
    """
    results = extract_diagnosis_results_from_messages(messages, max_results)
    return '\n'.join(results) if results else '无诊断结果'
