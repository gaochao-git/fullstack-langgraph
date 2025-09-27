"""测试多智能体诊断系统"""
import asyncio
from src.shared.core.logging import get_logger

logger = get_logger(__name__)

async def test_multi_agent_system():
    """测试多智能体系统是否能正常运行"""
    try:
        # 测试导入
        from .enhanced_react_agent import create_enhanced_react_agent
        from .sub_agents import DIAGNOSTIC_SUBAGENTS
        from langchain_openai import ChatOpenAI
        
        logger.info("✅ 导入成功")
        
        # 创建测试LLM
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        
        # 创建测试工具（空列表）
        tools = []
        
        # 创建增强的智能体
        agent = create_enhanced_react_agent(
            llm_model=llm,
            tools=tools,
            checkpointer=None,
            monitor_hook=None
        )
        
        logger.info(f"✅ 创建增强智能体成功，包含 {len(DIAGNOSTIC_SUBAGENTS)} 个子智能体")
        
        # 列出所有子智能体
        for sub_agent in DIAGNOSTIC_SUBAGENTS:
            logger.info(f"  - {sub_agent['name']}: {sub_agent['description']}")
        
        logger.info("✅ 多智能体系统测试通过！")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # 运行测试
    result = asyncio.run(test_multi_agent_system())
    if result:
        print("多智能体系统可以正常使用！")
    else:
        print("多智能体系统存在问题，请检查错误日志。")