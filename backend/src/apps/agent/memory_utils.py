"""
记忆系统辅助函数

提供记忆系统的辅助功能，包括：
1. 多层记忆并行检索
2. 记忆上下文构建
3. 记忆分析与过滤
"""

import asyncio
from typing import List, Dict, Any, Optional
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


async def search_combined_memory(
    memory,
    query: str,
    user_id: str,
    agent_id: str,
    limit_per_level: int = 3,
    threshold: Optional[float] = None
) -> Dict[str, List[Dict[str, Any]]]:
    """
    并行检索多层记忆

    Args:
        memory: EnterpriseMemory实例
        query: 搜索查询
        user_id: 用户ID
        agent_id: 智能体ID
        limit_per_level: 每层返回的记忆数量
        threshold: 相似度阈值

    Returns:
        包含各层记忆的字典
    """
    try:
        # 并行执行三层检索
        user_memories, agent_memories, interaction_memories = await asyncio.gather(
            # 用户级记忆
            memory.search_memories(
                query=query,
                user_id=user_id,
                limit=limit_per_level
            ),
            # 智能体级记忆
            memory.search_memories(
                query=query,
                agent_id=agent_id,
                limit=limit_per_level
            ),
            # 用户-智能体交互记忆
            memory.search_memories(
                query=query,
                user_id=user_id,
                agent_id=agent_id,
                limit=limit_per_level
            )
        )

        # 格式化记忆内容
        def format_memories(memories: List[Dict]) -> List[Dict]:
            """格式化记忆，确保有content字段"""
            formatted = []
            for mem in memories:
                formatted_mem = {
                    'id': mem.get('id', ''),
                    'content': mem.get('memory', mem.get('content', '')),
                    'score': mem.get('score', 0),
                    'metadata': mem.get('metadata', {})
                }
                formatted.append(formatted_mem)
            return formatted

        # 过滤低相关度的记忆（如果设置了阈值）
        if threshold is not None:
            user_memories = [m for m in user_memories if m.get('score', 0) > threshold]
            agent_memories = [m for m in agent_memories if m.get('score', 0) > threshold]
            interaction_memories = [m for m in interaction_memories if m.get('score', 0) > threshold]

        combined_memories = {
            "user_global": format_memories(user_memories),
            "agent_global": format_memories(agent_memories),
            "user_agent": format_memories(interaction_memories)
        }

        # 统计记忆数量
        total_count = sum(len(v) for v in combined_memories.values())
        logger.info(f"✅ 组合检索完成: 共找到 {total_count} 条记忆 "
                   f"(用户: {len(user_memories)}, 智能体: {len(agent_memories)}, 交互: {len(interaction_memories)})")

        return combined_memories

    except Exception as e:
        logger.error(f"组合记忆检索失败: {e}")
        # 返回空结果而不是抛出异常，保证系统继续运行
        return {
            "user_global": [],
            "agent_global": [],
            "user_agent": []
        }


def build_layered_context(memories: Dict[str, List[Dict]], max_per_layer: int = 3) -> str:
    """
    构建分层记忆上下文提示

    Args:
        memories: 各层记忆字典
        max_per_layer: 每层最多包含的记忆数

    Returns:
        格式化的上下文提示字符串
    """
    parts = ["# 📚 相关记忆上下文\n"]

    # 用户档案（最高优先级）
    if memories.get("user_global"):
        parts.append("\n## 👤 用户档案（高度相关）")
        for i, mem in enumerate(memories["user_global"][:max_per_layer], 1):
            content = mem.get('content', mem.get('memory', ''))
            if content:
                parts.append(f"{i}. {content}")

    # 智能体专业知识（中等优先级）
    if memories.get("agent_global"):
        parts.append("\n## 🤖 专业知识库")
        for i, mem in enumerate(memories["agent_global"][:max_per_layer], 1):
            content = mem.get('content', mem.get('memory', ''))
            if content:
                parts.append(f"{i}. {content}")

    # 交互历史（低优先级）
    if memories.get("user_agent"):
        parts.append("\n## 💬 历史交互")
        for i, mem in enumerate(memories["user_agent"][:max_per_layer], 1):
            content = mem.get('content', mem.get('memory', ''))
            if content:
                parts.append(f"{i}. {content}")

    # 添加使用说明
    if any(memories.values()):
        parts.append("\n---")
        parts.append("请基于以上记忆提供个性化、专业的诊断建议。")

    return "\n".join(parts)


def analyze_conversation_for_memory(
    messages: List[Dict[str, str]]
) -> Dict[str, Any]:
    """
    分析对话内容，识别值得保存的记忆类型

    Args:
        messages: 对话消息列表

    Returns:
        分析结果字典
    """
    analysis = {
        "has_user_profile": False,
        "has_expertise": False,
        "has_preferences": False,
        "has_problem_solution": False,
        "problem_type": None,
        "solution_type": None
    }

    # 合并所有消息文本
    full_text = " ".join([msg.get("content", "") for msg in messages]).lower()

    # 用户档案关键词
    profile_keywords = ["我是", "我叫", "我负责", "我的职责", "我在", "工作年限", "经验"]
    if any(kw in full_text for kw in profile_keywords):
        analysis["has_user_profile"] = True

    # 专业技能关键词
    expertise_keywords = ["擅长", "熟悉", "精通", "专业", "技能", "掌握", "了解"]
    if any(kw in full_text for kw in expertise_keywords):
        analysis["has_expertise"] = True

    # 偏好设置关键词
    preference_keywords = ["喜欢", "偏好", "习惯", "通常", "一般", "倾向"]
    if any(kw in full_text for kw in preference_keywords):
        analysis["has_preferences"] = True

    # 问题解决关键词
    problem_keywords = ["问题", "故障", "错误", "异常", "失败", "报错"]
    solution_keywords = ["解决", "修复", "处理", "方案", "建议", "步骤"]

    if any(kw in full_text for kw in problem_keywords):
        analysis["has_problem_solution"] = True

        # 识别问题类型
        if "数据库" in full_text or "mysql" in full_text or "postgres" in full_text:
            analysis["problem_type"] = "database"
        elif "网络" in full_text or "连接" in full_text or "timeout" in full_text:
            analysis["problem_type"] = "network"
        elif "性能" in full_text or "cpu" in full_text or "内存" in full_text:
            analysis["problem_type"] = "performance"
        elif "安全" in full_text or "权限" in full_text or "认证" in full_text:
            analysis["problem_type"] = "security"
        else:
            analysis["problem_type"] = "general"

    if any(kw in full_text for kw in solution_keywords):
        analysis["solution_type"] = "provided"

    return analysis


async def save_layered_memories(
    memory,
    messages: List[Dict[str, str]],
    user_id: str,
    agent_id: str,
    analysis: Optional[Dict[str, Any]] = None
) -> Dict[str, List[str]]:
    """
    根据对话内容分层保存记忆

    Args:
        memory: EnterpriseMemory实例
        messages: 对话消息列表
        user_id: 用户ID
        agent_id: 智能体ID
        analysis: 对话分析结果（可选）

    Returns:
        保存的记忆ID字典
    """
    if analysis is None:
        analysis = analyze_conversation_for_memory(messages)

    saved_memories = {
        "user": [],
        "agent": [],
        "interaction": []
    }

    try:
        tasks = []

        # 1. 保存用户档案记忆
        if analysis.get("has_user_profile") or analysis.get("has_preferences"):
            task = memory.add_user_memory(
                messages=messages,
                user_id=user_id,
                memory_type="profile",
                metadata={"source": "diagnostic_conversation"}
            )
            tasks.append(("user", task))

        # 2. 保存智能体经验记忆
        if analysis.get("has_problem_solution"):
            task = memory.add_agent_memory(
                messages=messages,
                agent_id=agent_id,
                memory_type="experience",
                metadata={
                    "problem_type": analysis.get("problem_type"),
                    "solution_type": analysis.get("solution_type")
                }
            )
            tasks.append(("agent", task))

        # 3. 总是保存用户-智能体交互记忆
        interaction_task = memory.add_user_agent_memory(
            messages=messages,
            user_id=user_id,
            agent_id=agent_id,
            memory_type="interaction",
            metadata={"conversation_type": "diagnostic"}
        )
        tasks.append(("interaction", interaction_task))

        # 并行执行保存任务
        for memory_type, task in tasks:
            try:
                memory_id = await task
                saved_memories[memory_type].append(memory_id)
                logger.info(f"✅ 保存{memory_type}记忆: {memory_id}")
            except Exception as e:
                logger.error(f"保存{memory_type}记忆失败: {e}")

    except Exception as e:
        logger.error(f"分层保存记忆失败: {e}")

    return saved_memories


def filter_relevant_memories(
    memories: List[Dict[str, Any]],
    min_score: float = 0.7,
    max_age_days: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    过滤相关记忆

    Args:
        memories: 记忆列表
        min_score: 最小相似度分数
        max_age_days: 最大年龄（天数）

    Returns:
        过滤后的记忆列表
    """
    filtered = []

    for mem in memories:
        # 过滤相似度
        if mem.get('score', 0) < min_score:
            continue

        # 过滤年龄（如果设置）
        if max_age_days is not None:
            from datetime import datetime, timedelta
            created_at = mem.get('created_at')
            if created_at:
                try:
                    mem_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if datetime.now().astimezone() - mem_date > timedelta(days=max_age_days):
                        continue
                except:
                    pass

        filtered.append(mem)

    return filtered


def merge_duplicate_memories(memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    合并重复或相似的记忆

    Args:
        memories: 记忆列表

    Returns:
        去重后的记忆列表
    """
    # 简单的基于内容的去重
    seen_contents = set()
    unique_memories = []

    for mem in memories:
        content = mem.get('content', mem.get('memory', ''))
        if content and content not in seen_contents:
            seen_contents.add(content)
            unique_memories.append(mem)

    return unique_memories