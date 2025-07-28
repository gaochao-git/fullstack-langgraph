"""
提示词管理模块
专门管理智能运维助手的提示词
"""

from ....agent.service.agent_config_service import AgentConfigService

# 默认智能运维助手的系统提示词 - 作为后备方案
DEFAULT_SYSTEM_PROMPT = """你是一个专业的智能运维助手，具备以下核心能力：

🔧 **技术支持**：
- 回答各种运维、开发、系统管理相关问题
- 提供技术解决方案和最佳实践建议
- 协助进行故障诊断和问题排查

🛠️ **工具能力**：
- SSH工具：系统信息查询、进程分析、服务状态检查、日志分析、命令执行
- SOP工具：查找和参考标准操作程序
- MySQL工具：数据库连接、查询执行、性能监控
- Elasticsearch工具：集群状态查询、索引管理、数据分析
- Zabbix工具：监控数据获取、告警信息查询
- 通用工具：时间获取等实用功能

📋 **工作原则**：
1. 理解用户问题的核心需求
2. 选择合适的工具来获取必要信息
3. 基于获取的信息提供准确、实用的建议
4. 对于复杂问题，提供分步骤的解决方案
5. 始终考虑安全性和最佳实践
6. 如果是SOP故障排查请排查一步分析一步，如果找到根因可以提前退出，不需要问用户是否需要执行，直接按照sop一步步排查即可

⚠️ **注意事项**：
- 优先提供安全可靠的解决方案
- 对于复杂操作，建议用户先在测试环境验证
- 如果涉及数据安全，提醒用户注意备份
- 提供具体可执行的操作步骤
- 如果需要更多信息才能准确回答，主动询问

请以友好、专业的态度协助用户解决技术问题，灵活使用工具来提供准确的帮助。"""

def get_system_prompt(agent_name: str = "diagnostic_agent") -> str:
    """
    获取智能体的系统提示词，优先从数据库获取，否则使用默认提示词。
    
    Args:
        agent_name: 智能体名称
        
    Returns:
        系统提示词字符串
    """
    try:
        prompt_config = AgentConfigService.get_prompt_config_from_agent(agent_name)
        system_prompt = prompt_config.get('system_prompt', '').strip()
        
        # 如果数据库中有有效的系统提示词，使用它
        if system_prompt:
            return system_prompt
            
    except Exception as e:
        print(f"Warning: Failed to load system prompt from database for {agent_name}: {e}")
    
    # 后备方案：使用默认提示词
    return DEFAULT_SYSTEM_PROMPT

# 保持向后兼容性
SYSTEM_PROMPT = get_system_prompt()

# 导出提示词
__all__ = ["get_system_prompt", "SYSTEM_PROMPT", "DEFAULT_SYSTEM_PROMPT"]