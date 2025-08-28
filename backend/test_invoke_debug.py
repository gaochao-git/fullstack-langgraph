#!/usr/bin/env python
"""
调试非流式API
"""
import asyncio
import sys
sys.path.insert(0, '/Users/gaochao/gaochao-git/gaochao_repo/fullstack-langgraph/backend')

from src.apps.agent.service.streaming import invoke_run_standard, RunCreate

async def test_invoke():
    """直接测试invoke_run_standard函数"""
    request_body = RunCreate(
        assistant_id="diagnostic_agent",
        input={
            "messages": [{"role": "human", "content": "你好"}],
            "user_name": "test_user"
        },
        agent_key="f402e4f040d3b55075847c5ce4fc684898721358cc20991851b67411c9280462"
    )
    
    thread_id = "test_debug_123"
    
    try:
        print("🚀 开始测试非流式调用...")
        result = await invoke_run_standard(thread_id, request_body)
        print("✅ 调用成功!")
        print(f"结果: {result}")
    except Exception as e:
        print(f"❌ 调用失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_invoke())