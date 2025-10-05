"""
测试Mem0图记忆功能
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_mem0_graph_memory():
    """测试Mem0图记忆添加和搜索"""
    try:
        from src.apps.agent.memory_factory import get_enterprise_memory
        from src.shared.core.logging import get_logger
        from src.shared.core.config import settings

        logger = get_logger(__name__)

        print("=" * 60)
        print("🧪 Mem0图记忆集成测试")
        print("=" * 60)

        # 检查配置
        print("\n0️⃣ 检查Neo4j配置...")
        print(f"   NEO4J_ENABLED: {getattr(settings, 'NEO4J_ENABLED', 'NOT_SET')}")
        print(f"   NEO4J_URL: {getattr(settings, 'NEO4J_URL', 'NOT_SET')}")
        print(f"   NEO4J_USERNAME: {getattr(settings, 'NEO4J_USERNAME', 'NOT_SET')}")

        # 获取记忆实例
        print("\n1️⃣ 初始化Mem0记忆系统（启用Neo4j图存储）...")
        memory = await get_enterprise_memory()
        print("✅ 记忆系统初始化成功")

        # 检查是否启用了图存储
        enable_graph = getattr(memory.memory, 'enable_graph', False)
        has_graph = hasattr(memory.memory, 'graph') and memory.memory.graph is not None

        if has_graph:
            graph_type = type(memory.memory.graph).__name__
            print(f"✅ 图存储已启用: {graph_type}")
            print(f"   enable_graph标志: {enable_graph}")
        else:
            print(f"⚠️  图存储未启用（enable_graph={enable_graph}）")

        # 测试数据
        test_messages = [
            {"role": "user", "content": "我是张三，负责公司的数据库运维工作"},
            {"role": "assistant", "content": "你好张三，了解到你负责数据库运维。请问有什么我可以帮助你的？"}
        ]

        # 添加记忆
        print("\n2️⃣ 添加测试记忆...")
        memory_id = await memory.add_user_memory(
            messages=test_messages,
            user_id="test_user_graph",
            metadata={"source": "neo4j_test", "test_type": "graph_integration"}
        )
        print(f"✅ 记忆添加成功: {memory_id}")

        # 搜索记忆
        print("\n3️⃣ 搜索相关记忆...")
        search_results = await memory.search_memories(
            query="张三的工作职责",
            user_id="test_user_graph",
            limit=5
        )

        # 处理搜索结果格式
        if isinstance(search_results, dict):
            memories = search_results.get("results", [])
        else:
            memories = search_results

        print(f"✅ 搜索完成，找到 {len(memories)} 条相关记忆:")
        for i, mem in enumerate(memories, 1):
            content = mem.get('memory', mem.get('content', ''))
            score = mem.get('score', 'N/A')
            print(f"   {i}. [{score}] {content[:100]}")

        # 测试图记忆特性
        if has_graph:
            print("\n4️⃣ 测试图存储特性...")
            # 添加关系记忆
            graph_messages = [
                {"role": "user", "content": "我和李四一起负责MySQL数据库，他主要负责备份工作"},
                {"role": "assistant", "content": "明白了，你和李四都负责MySQL，但分工不同"}
            ]
            graph_memory_id = await memory.add_user_memory(
                messages=graph_messages,
                user_id="test_user_graph",
                metadata={"source": "neo4j_test", "test_type": "relationship"}
            )
            print(f"✅ 关系记忆添加成功: {graph_memory_id}")

            # 搜索关系
            relation_results = await memory.search_memories(
                query="李四负责什么工作",
                user_id="test_user_graph",
                limit=5
            )
            if isinstance(relation_results, dict):
                relation_memories = relation_results.get("results", [])
            else:
                relation_memories = relation_results

            print(f"✅ 关系搜索完成，找到 {len(relation_memories)} 条相关记忆:")
            for i, mem in enumerate(relation_memories[:3], 1):
                content = mem.get('memory', mem.get('content', ''))
                score = mem.get('score', 'N/A')
                print(f"   {i}. [{score}] {content[:100]}")

        print("\n" + "=" * 60)
        print("✅ Mem0图记忆集成测试完成")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_mem0_graph_memory())
    sys.exit(0 if success else 1)
