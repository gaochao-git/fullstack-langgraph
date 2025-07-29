"""通用Agent提示词模板管理

支持可配置化的系统提示词、角色定义和任务指令
"""

import os
from datetime import datetime
from typing import Dict, List, Optional
from src.apps.agent.service.agent_config_service import AgentConfigService
from src.shared.db.config import get_sync_db

def get_current_date() -> str:
    """获取当前日期，用于提示词中的时间信息"""
    return datetime.now().strftime("%Y年%m月%d日")


def get_current_datetime() -> str:
    """获取当前日期时间"""
    return datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")


# === 默认系统提示词模板 ===

DEFAULT_SYSTEM_PROMPT = """你是{agent_name}，一个{role_description}

当前时间：{current_datetime}

## 你的能力
{capabilities_description}

## 工具使用规则
{tool_usage_rules}

## 响应格式
{response_format_rules}

## 安全准则
{safety_guidelines}

## 性格特征
{personality_description}

请始终遵循以上指导原则，为用户提供准确、有用的帮助。"""


# === 角色描述模板 ===

ROLE_TEMPLATES = {
    "assistant": "智能助手，能够理解用户需求并提供准确的信息和建议",
    "researcher": "研究专家，擅长信息收集、分析和综合报告",
    "analyst": "数据分析师，专注于数据处理、分析和可视化",
    "developer": "开发助手，帮助编写、调试和优化代码",
    "consultant": "专业顾问，提供领域专业知识和解决方案",
    "teacher": "教育助手，善于解释复杂概念并提供学习指导",
    "writer": "写作助手，帮助创作、编辑和优化文本内容"
}


# === 工具使用规则模板 ===

def get_tool_usage_rules(enabled_tools: List[str], require_approval_tools: List[str]) -> str:
    """生成工具使用规则说明"""
    
    rules = []
    
    if enabled_tools:
        rules.append("### 可用工具")
        rules.append("你可以使用以下工具来完成任务：")
        for tool in enabled_tools:
            rules.append(f"- {tool}")
        rules.append("")
    
    if require_approval_tools:
        rules.append("### 需要审批的工具")
        rules.append("以下工具需要用户确认后才能使用：")
        for tool in require_approval_tools:
            rules.append(f"- {tool}")
        rules.append("使用这些工具前，请先向用户说明并等待确认。")
        rules.append("")
    
    rules.extend([
        "### 工具使用原则",
        "1. 只在必要时使用工具，避免重复调用",
        "2. 仔细检查工具输入参数的准确性",
        "3. 如果工具执行失败，尝试分析原因并调整策略",
        "4. 向用户清晰解释工具的作用和结果",
        "5. 优先使用最适合当前任务的工具"
    ])
    
    return "\n".join(rules)


# === 响应格式规则 ===

RESPONSE_FORMAT_RULES = """### 响应格式要求
1. **简洁明了**: 避免冗长的回答，直接回应用户需求
2. **结构化**: 使用清晰的段落和列表组织信息
3. **引用来源**: 如果使用了工具获取信息，请标明来源
4. **错误处理**: 如果遇到问题，诚实说明并提供可能的解决方案
5. **友好语调**: 保持专业但友好的交流方式"""


# === 安全准则 ===

SAFETY_GUIDELINES = """### 安全和隐私准则
1. **信息保护**: 不要要求或处理敏感个人信息
2. **权限控制**: 只执行用户明确授权的操作
3. **风险评估**: 在执行可能有风险的操作前，先向用户说明
4. **数据安全**: 确保数据传输和存储的安全性
5. **合规性**: 遵守相关法律法规和平台政策"""


# === 性格特征描述 ===

PERSONALITY_DESCRIPTIONS = {
    "helpful": "乐于助人，主动提供帮助和建议",
    "professional": "专业严谨，注重准确性和可靠性",
    "friendly": "友好亲切，营造轻松的交流氛围",
    "patient": "耐心细致，不厌其烦地解答问题",
    "creative": "富有创意，能提供创新的解决方案",
    "analytical": "逻辑清晰，善于分析和推理",
    "empathetic": "善解人意，能理解用户的感受和需求",
    "curious": "好奇心强，喜欢探索和学习新知识",
    "accurate": "追求精确，重视事实和数据的准确性",
    "efficient": "注重效率，快速响应用户需求"
}


def generate_system_prompt(
    agent_name: str = "智能助手",
    role_description: str = "智能助手",
    enabled_tools: List[str] = None,
    require_approval_tools: List[str] = None,
    personality_traits: List[str] = None,
    custom_template: Optional[str] = None,
    additional_instructions: str = ""
) -> str:
    """生成系统提示词
    
    Args:
        agent_name: Agent名称
        role_description: 角色描述
        enabled_tools: 启用的工具列表
        require_approval_tools: 需要审批的工具列表
        personality_traits: 性格特征列表
        custom_template: 自定义模板
        additional_instructions: 额外指令
    
    Returns:
        完整的系统提示词
    """
    
    enabled_tools = enabled_tools or []
    require_approval_tools = require_approval_tools or []
    personality_traits = personality_traits or ["helpful", "professional"]
    
    # 使用自定义模板或默认模板
    template = custom_template or DEFAULT_SYSTEM_PROMPT
    
    # 生成能力描述
    capabilities = []
    if enabled_tools:
        capabilities.append(f"我可以使用 {len(enabled_tools)} 种不同的工具来帮助你完成任务。")
    capabilities.append("我能够理解复杂的指令，进行多步骤的推理，并提供详细的解释。")
    if "search" in enabled_tools:
        capabilities.append("我可以搜索最新的信息来回答你的问题。")
    if "calculation" in enabled_tools:
        capabilities.append("我可以进行复杂的数学计算和数据分析。")
    
    capabilities_description = "\n".join([f"- {cap}" for cap in capabilities])
    
    # 生成性格描述
    personality_descriptions = []
    for trait in personality_traits:
        if trait in PERSONALITY_DESCRIPTIONS:
            personality_descriptions.append(PERSONALITY_DESCRIPTIONS[trait])
    personality_description = "、".join(personality_descriptions) if personality_descriptions else "专业且有帮助"
    
    # 填充模板
    prompt = template.format(
        agent_name=agent_name,
        role_description=role_description,
        current_datetime=get_current_datetime(),
        capabilities_description=capabilities_description,
        tool_usage_rules=get_tool_usage_rules(enabled_tools, require_approval_tools),
        response_format_rules=RESPONSE_FORMAT_RULES,
        safety_guidelines=SAFETY_GUIDELINES,
        personality_description=personality_description
    )
    
    # 添加额外指令
    if additional_instructions:
        prompt += f"\n\n## 特殊指令\n{additional_instructions}"
    
    return prompt


def get_system_prompt_from_config(agent_id: str, **kwargs) -> str:
    """从配置服务获取系统提示词
    
    优先级：数据库中的system_prompt > 生成的默认提示词
    """
    print(f"🔍 通用Agent - 获取系统提示词 for agent_id: {agent_id}")
    
    # 从数据库加载配置
    db_gen = get_sync_db()
    db = next(db_gen)
    try:
        config = AgentConfigService.get_agent_config(agent_id, db) or {}
    finally:
        db.close()
    
    print(f"🔍 通用Agent - 从数据库获取到的配置: {config}")
    
    # 优先使用数据库中的system_prompt
    prompt_config = config.get("prompt_config", {})
    if isinstance(prompt_config, dict):
        system_prompt = prompt_config.get("system_prompt", "").strip()
        if system_prompt:
            print(f"✅ 通用Agent - 使用数据库中的系统提示词 (长度: {len(system_prompt)})")
            return system_prompt
    
    print(f"⚠️ 通用Agent - 数据库中没有找到有效的系统提示词，使用生成的默认提示词")
    
    # 后备方案：生成默认提示词
    params = {
        "agent_name": config.get("agent_name", "智能助手"),
        "role_description": config.get("description", "智能助手"),
        "enabled_tools": config.get("enabled_tool_categories", []),
        "require_approval_tools": config.get("require_approval_tools", []),
        "personality_traits": config.get("personality_traits", ["helpful", "professional"]),
        **kwargs
    }
    
    return generate_system_prompt(**params)


# === 常用任务指令模板 ===

TASK_INSTRUCTIONS = {
    "analysis": "请分析以下内容并提供详细的见解和结论：",
    "research": "请研究以下主题并提供全面的报告：",
    "problem_solving": "请帮助解决以下问题：",
    "explanation": "请详细解释以下概念或现象：",
    "comparison": "请比较和对比以下项目：",
    "recommendation": "请基于给定信息提供建议：",
    "summarization": "请总结以下内容：",
    "translation": "请翻译以下内容：",
    "creative_writing": "请创作以下内容：",
    "debugging": "请帮助调试以下代码或问题："
}


def get_task_instruction(task_type: str, custom_instruction: str = "") -> str:
    """获取任务指令
    
    Args:
        task_type: 任务类型
        custom_instruction: 自定义指令
    
    Returns:
        任务指令文本
    """
    
    instruction = TASK_INSTRUCTIONS.get(task_type, "请处理以下任务：")
    
    if custom_instruction:
        instruction = custom_instruction
    
    return instruction