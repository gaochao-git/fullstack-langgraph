#!/usr/bin/env python3
"""
测试脚本：带人工审批的 DeepSeek Agent - 串行审批版本
"""

import os
import sys
import uuid
import json
from typing import Literal, Dict, Any, Annotated, Sequence
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.graph.message import add_messages

# 设置环境变量（如果需要）
os.environ["DEEPSEEK_API_KEY"] = "sk-490738f8ce8f4a36bcc0bfb165270008"

def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

def divide(a: int, b: int) -> float:
    """Divide two numbers."""
    if b == 0:
        return "Error: Division by zero"
    return a / b

def subtract(a: int, b: int) -> int:
    """Subtract two numbers."""
    return a - b

# 初始化 DeepSeek 模型
def create_model():
    """创建 DeepSeek 模型"""
    return ChatDeepSeek(
        model="deepseek-chat",
        temperature=0,
        api_key="sk-490738f8ce8f4a36bcc0bfb165270008",
        base_url="https://api.deepseek.com"
    )

# 定义状态类型 - 使用 Annotated 来处理消息列表
class AgentState(Dict[str, Any]):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    approved_tools: list = []

# 串行审批节点
def serial_approval_node(state: AgentState) -> Command[Literal["execute_tools"]]:
    """串行逐个审批工具调用"""
    print("\n" + "="*50)
    print("🔍 串行审批节点")
    print("="*50)
    
    messages = state.get("messages", [])
    if not messages:
        print("❌ 没有消息，跳过审批")
        return Command(goto="execute_tools", update={"approved_tools": []})
    
    last_message = messages[-1]
    if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
        print("❌ 没有工具调用，跳过审批")
        return Command(goto="execute_tools", update={"approved_tools": []})
    
    tool_calls = last_message.tool_calls
    approved_tools = []
    
    print(f"🔍 检测到 {len(tool_calls)} 个工具调用需要审批")
    print("="*50)
    
    # 逐个审批每个工具
    for i, tool_call in enumerate(tool_calls):
        tool_name = tool_call.get('name', 'unknown')
        tool_args = tool_call.get('args', {})
        
        print(f"\n🔧 审批工具 {i+1}/{len(tool_calls)}:")
        print(f"  工具名称: {tool_name}")
        print(f"  工具参数: {tool_args}")
        
        # 构建审批消息
        approval_message = f"工具 {tool_name} 将执行参数: {tool_args}\n\n是否批准执行这个工具调用？"
        
        print(f"\n📋 审批信息:")
        print(approval_message)
        
        # 交互式获取用户输入
        print("\n⏳ 等待用户审批...")
        
        while True:
            user_input = input(f"\n请输入 'y' 批准 或 'n' 拒绝 或 's' 跳过当前工具: ").strip().lower()
            if user_input in ['y', 'yes', '批准', '同意']:
                is_approved = True
                break
            elif user_input in ['n', 'no', '拒绝', '不同意']:
                is_approved = False
                break
            elif user_input in ['s', 'skip', '跳过', '跳过当前']:
                is_approved = None  # 跳过
                break
            else:
                print("❌ 无效输入，请输入 'y'、'n' 或 's'")
        
        print(f"✅ 用户审批结果: {is_approved}")
        
        # 更新审批状态
        if is_approved is True:
            print(f"✅ 用户批准工具: {tool_name}")
            approved_tools.append(tool_call)
        elif is_approved is False:
            print(f"❌ 用户拒绝工具: {tool_name}")
            # 不添加到已批准列表
        else:  # is_approved is None
            print(f"⏭️ 用户跳过工具: {tool_name}")
            # 不添加到已批准列表
        
        # 如果不是最后一个工具，显示进度
        if i < len(tool_calls) - 1:
            print(f"\n⏳ 还有 {len(tool_calls) - i - 1} 个工具需要审批")
            print("-" * 30)
    
    # 所有工具都已审批完成
    print(f"\n✅ 所有工具审批完成，已批准 {len(approved_tools)} 个工具")
    print(f"🔍 调试信息 - 已批准工具: {approved_tools}")
    
    # 返回审批结果和已批准的工具
    return Command(goto="execute_tools", update={"approved_tools": approved_tools})

# 执行工具节点
def execute_tools_node(state: AgentState) -> Dict[str, Any]:
    """执行已审批的工具调用"""
    print("\n" + "="*50)
    print("🔧 执行工具节点")
    print("="*50)
    
    # 调试信息
    print(f"🔍 调试信息 - 完整状态: {state}")
    approved_tools = state.get("approved_tools", [])
    
    print(f"📊 已批准工具数量: {len(approved_tools)}")
    print(f"🔍 调试信息 - 已批准工具: {approved_tools}")
    
    if not approved_tools:
        print("❌ 没有已批准的工具需要执行")
        return {"messages": [AIMessage(content="没有已批准的工具需要执行。")]}
    
    results = []
    
    # 获取工具列表
    tools = [add, multiply, divide, subtract]
    
    print(f"✅ 开始执行 {len(approved_tools)} 个已审批的工具调用")
    
    # 逐个执行工具调用
    for i, tool_call in enumerate(approved_tools):
        tool_name = tool_call.get('name', 'unknown')
        tool_args = tool_call.get('args', {})
        
        print(f"\n🔧 执行工具 {i+1}/{len(approved_tools)}: {tool_name}({tool_args})")
        
        # 查找对应的工具函数
        tool_func = None
        for tool in tools:
            if hasattr(tool, 'name') and tool.name == tool_name:
                tool_func = tool
                break
            elif callable(tool) and tool.__name__ == tool_name:
                tool_func = tool
                break
        
        if tool_func:
            try:
                result = tool_func(**tool_args)
                results.append({
                    "tool_call_id": tool_call.get("id", f"call_{i}"),
                    "name": tool_name,
                    "content": str(result)
                })
                print(f"✅ 工具 {tool_name} 执行成功: {result}")
            except Exception as e:
                print(f"❌ 工具 {tool_name} 执行失败: {e}")
                results.append({
                    "tool_call_id": tool_call.get("id", f"call_{i}"),
                    "name": tool_name,
                    "content": f"执行失败: {str(e)}"
                })
        else:
            print(f"❌ 未找到工具: {tool_name}")
            results.append({
                "tool_call_id": tool_call.get("id", f"call_{i}"),
                "name": tool_name,
                "content": f"未找到工具: {tool_name}"
            })
    
    # 生成最终回答
    if results:
        result_summary = []
        for result in results:
            tool_name = result["name"]
            result_value = result["content"]
            result_summary.append(f"{tool_name} 的结果是: {result_value}")
        
        final_answer = "\n".join(result_summary)
        print(f"\n✅ 工具执行完成，结果: {final_answer}")
        return {"messages": [AIMessage(content=final_answer)]}
    else:
        print("\n❌ 没有工具被执行")
        return {"messages": [AIMessage(content="没有工具被执行。")]}

# 模型节点
def model_node(state: AgentState) -> Dict[str, Any]:
    """调用模型生成响应"""
    print("\n" + "="*50)
    print("🤖 模型节点")
    print("="*50)
    
    messages = state.get("messages", [])
    print(f"📝 输入消息数量: {len(messages)}")
    
    # 创建模型
    model = create_model()
    
    # 绑定工具
    tools = [add, multiply, divide, subtract]
    model_with_tools = model.bind_tools(tools)
    
    # 调用模型
    response = model_with_tools.invoke(messages)
    print(f"🤖 模型响应: {response.content}")
    
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"🔧 模型生成了 {len(response.tool_calls)} 个工具调用")
        for i, tool_call in enumerate(response.tool_calls):
            tool_name = tool_call.get('name', 'unknown')
            tool_args = tool_call.get('args', {})
            print(f"  {i+1}. {tool_name}({tool_args})")
    else:
        print("📝 模型没有生成工具调用")
    
    return {"messages": [response]}

# 创建带串行审批的图
def create_serial_approval_agent():
    """创建带串行审批的 agent"""
    print("🏗️ 创建带串行审批的 Agent...")
    
    builder = StateGraph(AgentState)
    
    # 添加节点
    builder.add_node("model", model_node)
    builder.add_node("serial_approval", serial_approval_node)
    builder.add_node("execute_tools", execute_tools_node)
    
    # 设置边 - 简化的串行审批流程
    builder.add_edge(START, "model")
    builder.add_edge("model", "serial_approval")
    builder.add_edge("execute_tools", END)
    
    # 编译图
    graph = builder.compile()
    
    print("✅ Agent 创建完成")
    return graph

def interactive_test():
    """交互式测试"""
    print("🎯 DeepSeek Agent 串行审批测试")
    print("="*60)
    print("这个测试将演示:")
    print("1. 模型生成工具调用")
    print("2. 串行逐个审批流程")
    print("3. 工具执行")
    print("4. 结果返回")
    print("="*60)
    
    # 检查 API Key
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("❌ 请设置 DEEPSEEK_API_KEY 环境变量")
        sys.exit(1)
    
    print(f"✅ API Key 已设置: {api_key[:10]}...")
    
    # 创建 agent
    agent = create_serial_approval_agent()
    
    print("\n🚀 开始交互式测试")
    print("输入 'quit' 或 'exit' 退出")
    print("-" * 60)
    
    while True:
        try:
            # 获取用户输入
            user_input = input("\n💬 请输入您的问题 (或 'quit' 退出): ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 再见！")
                break
            
            if not user_input:
                print("❌ 请输入有效的问题")
                continue
            
            print(f"\n📝 您的问题: {user_input}")
            print("="*60)
            
            # 运行 agent
            result = agent.invoke({
                "messages": [HumanMessage(content=user_input)]
            })
            
            print(f"\n✅ 处理完成")
            print(f"📊 结果统计:")
            print(f"  消息数量: {len(result.get('messages', []))}")
            
            # 显示最终消息
            final_messages = result.get('messages', [])
            if final_messages:
                last_message = final_messages[-1]
                if hasattr(last_message, 'content'):
                    print(f"  最终回答: {last_message.content}")
            
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 处理失败: {e}")
            import traceback
            traceback.print_exc()

def batch_test():
    """批量测试"""
    print("🧪 批量测试模式")
    
    # 创建 agent
    agent = create_serial_approval_agent()
    
    # 测试用例
    test_cases = [
        {
            "name": "简单计算",
            "input": "3+2等于几，5*4等于几",
            "expected_tools": ["add", "multiply"]
        },
        {
            "name": "除法测试",
            "input": "calculate 10 / 2 and 15 - 3",
            "expected_tools": ["divide", "subtract"]
        },
        {
            "name": "复杂计算",
            "input": "what is 20 + 30, 50 * 2, and 100 / 4?",
            "expected_tools": ["add", "multiply", "divide"]
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 测试用例 {i}: {test_case['name']}")
        print(f"📝 输入: {test_case['input']}")
        print(f"🔧 预期工具: {test_case['expected_tools']}")
        print(f"{'='*60}")
        
        try:
            # 运行 agent
            result = agent.invoke({
                "messages": [HumanMessage(content=test_case['input'])]
            })
            
            print(f"\n✅ 测试用例 {i} 完成")
            print(f"📊 最终结果:")
            print(f"  消息数量: {len(result.get('messages', []))}")
            
            # 显示最终消息
            final_messages = result.get('messages', [])
            if final_messages:
                last_message = final_messages[-1]
                if hasattr(last_message, 'content'):
                    print(f"  最终内容: {last_message.content}")
            
        except Exception as e:
            print(f"❌ 测试用例 {i} 失败: {e}")
            import traceback
            traceback.print_exc()

def main():
    """主函数"""
    print("🎯 DeepSeek Agent 串行审批功能测试")
    print("="*60)
    
    # 选择测试模式
    print("\n请选择测试模式:")
    print("1. 交互式测试 (推荐)")
    print("2. 批量测试")
    
    while True:
        choice = input("\n请输入选择 (1 或 2): ").strip()
        if choice == "1":
            interactive_test()
            break
        elif choice == "2":
            batch_test()
            break
        else:
            print("❌ 无效选择，请输入 1 或 2")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()