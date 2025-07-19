#!/usr/bin/env python3
"""
可复用的串行审批 Agent 类
"""

import os
from typing import Literal, Dict, Any, Annotated, Sequence, List, Callable
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import AIMessage, HumanMessage, BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.graph.message import add_messages

class SerialApprovalAgent:
    """串行审批 Agent 类"""
    
    def __init__(self, 
                 api_key: str,
                 model_name: str = "deepseek-chat",
                 base_url: str = "https://api.deepseek.com",
                 tools: List[Callable] = None):
        """
        初始化串行审批 Agent
        
        Args:
            api_key: DeepSeek API Key
            model_name: 模型名称
            base_url: API 基础 URL
            tools: 工具函数列表
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.tools = tools or []
        
        # 设置环境变量
        os.environ["DEEPSEEK_API_KEY"] = api_key
        
        # 创建 Agent
        self.agent = self._create_agent()
    
    def _create_model(self):
        """创建 DeepSeek 模型"""
        return ChatDeepSeek(
            model=self.model_name,
            temperature=0,
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    def _create_agent(self):
        """创建 Agent"""
        # 定义状态
        class AgentState(Dict[str, Any]):
            messages: Annotated[Sequence[BaseMessage], add_messages]
            approved_tools: list = []
        
        # 模型节点
        def model_node(state: AgentState) -> Dict[str, Any]:
            model = self._create_model()
            model_with_tools = model.bind_tools(self.tools)
            response = model_with_tools.invoke(state.get("messages", []))
            
            print(f"🤖 模型生成了 {len(response.tool_calls) if response.tool_calls else 0} 个工具调用")
            return {"messages": [response]}
        
        # 串行审批节点
        def serial_approval_node(state: AgentState) -> Command[Literal["execute_tools"]]:
            messages = state.get("messages", [])
            if not messages or not hasattr(messages[-1], 'tool_calls') or not messages[-1].tool_calls:
                return Command(goto="execute_tools", update={"approved_tools": []})
            
            tool_calls = messages[-1].tool_calls
            approved_tools = []
            
            print(f"\n🔍 检测到 {len(tool_calls)} 个工具调用需要审批")
            
            for i, tool_call in enumerate(tool_calls):
                tool_name = tool_call.get('name', 'unknown')
                tool_args = tool_call.get('args', {})
                
                print(f"\n🔧 审批工具 {i+1}/{len(tool_calls)}: {tool_name}({tool_args})")
                
                while True:
                    user_input = input("请输入 'y' 批准 或 'n' 拒绝 或 's' 跳过: ").strip().lower()
                    if user_input in ['y', 'yes', '批准', '同意']:
                        approved_tools.append(tool_call)
                        print(f"✅ 批准: {tool_name}")
                        break
                    elif user_input in ['n', 'no', '拒绝', '不同意']:
                        print(f"❌ 拒绝: {tool_name}")
                        break
                    elif user_input in ['s', 'skip', '跳过']:
                        print(f"⏭️ 跳过: {tool_name}")
                        break
                    else:
                        print("❌ 无效输入，请输入 'y'、'n' 或 's'")
            
            print(f"\n✅ 审批完成，已批准 {len(approved_tools)} 个工具")
            return Command(goto="execute_tools", update={"approved_tools": approved_tools})
        
        # 执行工具节点
        def execute_tools_node(state: AgentState) -> Dict[str, Any]:
            approved_tools = state.get("approved_tools", [])
            
            if not approved_tools:
                return {"messages": [AIMessage(content="没有已批准的工具需要执行。")]}
            
            results = []
            
            print(f"\n🔧 开始执行 {len(approved_tools)} 个已批准的工具")
            
            for i, tool_call in enumerate(approved_tools):
                tool_name = tool_call.get('name', 'unknown')
                tool_args = tool_call.get('args', {})
                
                # 查找工具函数
                tool_func = next((tool for tool in self.tools if tool.__name__ == tool_name), None)
                
                if tool_func:
                    try:
                        result = tool_func(**tool_args)
                        results.append(f"{tool_name} 的结果是: {result}")
                        print(f"✅ {tool_name}({tool_args}) = {result}")
                    except Exception as e:
                        results.append(f"{tool_name} 执行失败: {e}")
                        print(f"❌ {tool_name} 执行失败: {e}")
                else:
                    results.append(f"未找到工具: {tool_name}")
                    print(f"❌ 未找到工具: {tool_name}")
            
            final_answer = "\n".join(results)
            return {"messages": [AIMessage(content=final_answer)]}
        
        # 创建图
        builder = StateGraph(AgentState)
        builder.add_node("model", model_node)
        builder.add_node("serial_approval", serial_approval_node)
        builder.add_node("execute_tools", execute_tools_node)
        
        builder.add_edge(START, "model")
        builder.add_edge("model", "serial_approval")
        builder.add_edge("execute_tools", END)
        
        return builder.compile()
    
    def invoke(self, user_input: str) -> Dict[str, Any]:
        """
        执行 Agent
        
        Args:
            user_input: 用户输入
            
        Returns:
            Agent 执行结果
        """
        return self.agent.invoke({
            "messages": [HumanMessage(content=user_input)]
        })
    
    def get_final_result(self, result: Dict[str, Any]) -> str:
        """
        获取最终结果
        
        Args:
            result: Agent 执行结果
            
        Returns:
            最终结果字符串
        """
        final_messages = result.get('messages', [])
        if final_messages:
            last_message = final_messages[-1]
            if hasattr(last_message, 'content'):
                return last_message.content
        return "没有结果"

# 示例工具函数
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

def divide(a: int, b: int) -> float:
    """Divide two numbers"""
    return a / b if b != 0 else "Error: Division by zero"

def subtract(a: int, b: int) -> int:
    """Subtract two numbers"""
    return a - b

# 使用示例
def main():
    """使用示例"""
    # 创建 Agent
    agent = SerialApprovalAgent(
        api_key="sk-490738f8ce8f4a36bcc0bfb165270008",
        tools=[add, multiply, divide, subtract]
    )
    
    print("🎯 串行审批 Agent 测试")
    print("="*50)
    
    while True:
        user_input = input("\n💬 请输入问题 (或 'quit' 退出): ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("👋 再见！")
            break
        
        if not user_input:
            continue
        
        print(f"\n📝 问题: {user_input}")
        print("="*50)
        
        try:
            result = agent.invoke(user_input)
            final_result = agent.get_final_result(result)
            print(f"\n📊 最终结果: {final_result}")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")

if __name__ == "__main__":
    main() 