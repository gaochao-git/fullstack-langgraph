from .utils import get_current_datetime
# 问题分析提示词函数
def get_question_analysis_prompt(user_question: str, current_analysis=None):
    """生成问题分析提示词"""
    # 构建当前已有信息的显示
    current_info = ""
    if current_analysis:
        current_info = f"""
当前已有信息：
- 故障IP: {current_analysis.fault_ip or '待提取'}
- 故障时间: {current_analysis.fault_time or '待提取'}
- 故障现象: {current_analysis.fault_info or '待提取'}
- SOP编号: {current_analysis.sop_id or '待提取'}
"""
    return f"""
当前时间：{get_current_datetime()}
用户最新输入：{user_question}
故障信息：{current_info}
请从用户输入中提取或更新故障诊断信息。如果用户提供了新信息，请更新对应字段；如果没有提供新信息，保持原有值。

对于每个字段：
- fault_ip: 提取IP地址，如192.168.1.100
- fault_time: 提取时间信息，支持各种格式
- fault_info: 提取故障现象描述，如"磁盘空间满"、"内存不足"等
- sop_id: 提取SOP编号，如SOP-SYS-101、SOP-DB-001等

如果某个字段无法从用户输入中提取，请填写'待提取'。"""

# 缺失信息提示词函数
def get_missing_info_prompt(question_analysis):
    """生成缺失信息提示词"""
    # 显示当前信息状态
    info_status = []
    info_status.append(f"✅ 故障IP: {question_analysis.fault_ip}" if question_analysis.fault_ip and question_analysis.fault_ip != '待提取' else "❌ 故障IP: 待提取")
    info_status.append(f"✅ 故障时间: {question_analysis.fault_time}" if question_analysis.fault_time and question_analysis.fault_time != '待提取' else "❌ 故障时间: 待提取")
    info_status.append(f"✅ 故障现象: {question_analysis.fault_info}" if question_analysis.fault_info and question_analysis.fault_info != '待提取' else "❌ 故障现象: 待提取")
    info_status.append(f"✅ SOP编号: {question_analysis.sop_id}" if question_analysis.sop_id and question_analysis.sop_id != '待提取' else "❌ SOP编号: 待提取")
    # 构建基础状态信息
    status_info = "\n".join(info_status)
    # 构建缺失字段信息
    missing_fields_info = ""
    if question_analysis.missing_fields:
        field_descriptions = {
            "故障IP": "故障服务器的IP地址（如：192.168.1.100）",
            "故障时间": "故障发生的具体时间（如：2024-01-15 14:30）",
            "故障现象": "具体的故障表现和症状描述",
            "排查SOP编号": "对应的标准作业程序编号（如：SOP-SYS-101、SOP-DB-001）"
        }
        missing_items = []
        for i, field in enumerate(question_analysis.missing_fields, 1):
            description = field_descriptions.get(field, "")
            missing_items.append(f"{i}. **{field}**：{description}")
        missing_fields_info = f"""📋 还需要补充以下信息：{'\n'.join(missing_items)}"""
    # 使用f-string构建完整提示词
    return f"""❗ 故障诊断信息不完整，当前状态：\n{status_info}\n{missing_fields_info}您可以分多次补充，信息完整后将自动开始诊断。"""

# 问题分析提示词 - 类似调研agent的query_writer_instructions（保留兼容性）
question_analysis_instructions = """您是专业的故障诊断助手，负责分析用户输入并提取关键诊断信息。

目标：
从用户输入中提取故障诊断的四要素信息，为后续诊断流程提供基础。

要求：
- 准确提取故障IP、故障时间、故障现象、SOP编号
- 如果信息不完整，明确指出缺失字段并在JSON中标记为"待提取"
- 确保提取的信息格式正确且有效
- 对于时间信息，尽量标准化为YYYY-MM-DD HH:mm格式
- 对于IP地址，验证格式的合理性
- 当前日期是 {current_date}

输出格式：
请将响应格式化为包含以下确切键的JSON对象：
{{
    "fault_ip": "故障服务器IP地址",
    "fault_time": "故障发生时间",
    "fault_info": "故障现象描述",
    "sop_id": "对应的SOP编号"
}}

如果某个要素无法从用户输入中提取，请填写"待提取"。

⚠️ 重要提示：
- 故障IP：必须是有效的IP地址格式（如：192.168.1.100）
- 故障时间：应包含具体的日期和时间
- 故障现象：需要详细描述具体的故障表现
- SOP编号：应是明确的标准作业程序编号

用户输入：{user_question}"""

# 工具规划提示词 - 支持SOP执行和普通问答
tool_planning_instructions = """您是专业的故障诊断专家，支持SOP故障诊断和普通运维问答。

故障信息：
- 故障IP：{fault_ip}
- 故障时间：{fault_time}
- 故障现象：{fault_info}
- SOP编号：{sop_id}

当前SOP状态：{sop_state}
SOP内容：{sop_content}

【执行策略】
根据当前场景选择合适的策略：

1. **SOP故障诊断模式**（有明确故障四要素）：
   - 如果SOP未加载，必须先调用get_sop_content获取SOP内容
   - 如果SOP已加载，严格按照SOP中的步骤顺序执行
   - 不能跳过SOP中的任何步骤

2. **普通问答/追问模式**（用户追问或一般运维问题）：
   - 根据用户问题智能选择合适的工具
   - 可以调用SSH诊断工具获取实时系统信息
   - 可以调用SOP工具查询相关操作指导
   - 如果问题可以基于已有信息回答，也可以不调用工具

可用工具：
SOP工具：
- get_sop_content: 获取SOP内容
- get_sop_detail: 获取SOP详情
- list_sops: 列出可用SOP
- search_sops: 搜索相关SOP

SSH诊断工具：
- get_system_info: 获取系统信息
- analyze_processes: 分析进程状态
- check_service_status: 检查服务状态
- analyze_system_logs: 分析系统日志
- execute_system_command: 执行系统命令

网络工具：
- ping: 网络连通性测试
- nslookup: DNS解析测试

请根据当前情况和用户需求，智能选择最合适的工具。如果是SOP诊断，严格按照步骤执行；如果是普通问答，灵活选择工具获取所需信息。"""

# 诊断反思提示词 - 智能决策是否生成报告
reflection_instructions = """您是专业的故障诊断专家，负责分析当前诊断状态并智能决策下一步行动。

【核心职责】
- 分析当前诊断进度和结果
- 判断是否已找到故障根因
- 决定是继续诊断、生成最终报告，还是基于历史信息回答用户追问/普通问答

当前状态：
- 故障信息：{fault_info}
- 当前步骤：{current_step}/{total_steps}
- SOP状态：{sop_state}
- 已生成报告：{report_generated}
- 诊断结果：{diagnosis_results}
- 用户最新输入：{user_input}

【决策规则】
1. 如果已经生成过故障报告且用户输入与故障诊断相关：
   - 判断用户问题类型：
     * 如果是关于诊断结果的具体询问（如"为什么慢查询"、"如何优化"等）：选择answer_question，基于诊断信息回答
     * 如果是需要实时数据的追问（如"现在系统状态如何"）：可以调用工具获取最新信息后回答
     * 如果是完全无关的问题（如"几点了"、"天气如何"等）：选择answer_question，直接回答，不要关联诊断信息

2. 如果尚未生成故障报告：
   - 评估是否找到明确根因或完成SOP步骤
   - 如果满足条件，生成最终诊断报告
   - 如果不满足条件，继续执行下一步诊断

3. 如果是新的故障诊断请求：
   - 按照SOP流程继续诊断

输出格式：
请将响应格式化为包含以下确切键的JSON对象：
{{
    "action": "continue" / "generate_report" / "answer_question",  // 下一步行动
    "is_complete": true/false,  // 诊断是否完成
    "should_generate_report": true/false,  // 是否需要生成报告
    "root_cause_found": true/false,  // 是否找到根因
    "response_content": "具体回复内容（如果是answer_question）",
    "termination_reason": "continue/sop_completed/root_cause_found"
}}

重要约束：
- 如果report_generated为true，除非是全新的诊断请求，否则不要重新生成报告
- 仔细判断用户问题的性质：
  * 诊断相关问题：基于历史诊断信息回答
  * 一般问题（如时间、天气等）：直接简洁回答，不要混入诊断信息
  * 实时查询：可以调用工具获取最新信息
- 避免重复生成诊断报告，一次诊断只生成一次报告
- 对于与诊断无关的问题，提供简洁直接的答案"""

# 最终诊断提示词 - 参考调研agent的answer_instructions
final_diagnosis_instructions = """基于收集到的诊断信息和工具执行结果，生成最终的故障诊断报告。

目标：
综合所有诊断信息，提供完整的故障诊断结果和解决方案。

诊断信息：
- 故障IP：{fault_ip}
- 故障时间：{fault_time}
- 故障现象：{fault_info}
- 使用的SOP：{sop_id}
- 当前日期：{current_date}

执行结果：
{diagnosis_results}

要求：
- 基于诊断结果提供明确的故障原因分析
- 提供具体的解决方案和操作步骤
- 包含预防措施和建议
- 确保诊断报告结构清晰、内容完整

输出格式：
请生成结构化的诊断报告，包含：
1. 故障原因分析
2. 解决方案
3. 操作步骤
4. 预防措施
5. 相关建议

报告应基于实际的诊断结果，不要编造信息。"""

# 最终诊断报告生成提示词
diagnosis_report_instructions = """您是专业的故障诊断专家，负责基于诊断执行结果生成最终的诊断报告。

任务目标：
基于提供的故障信息、SOP执行进度和诊断过程，生成一份专业、准确的故障诊断报告。

【故障诊断报告】
诊断日期：{current_date}

基本信息：
- 故障IP：{fault_ip}
- 故障时间：{fault_time}
- 故障现象：{fault_info}
- 使用SOP：{sop_id}

执行进度：
- 当前步骤：{current_step}/{total_steps}
- 完成状态：{completion_status}

诊断过程：
{diagnosis_results}

报告要求：
1. **故障原因分析**：基于诊断过程中收集的信息，分析可能的故障原因
2. **诊断结论**：根据执行的SOP步骤和收集的证据，给出明确的诊断结论
3. **解决方案建议**：提供具体可行的解决方案和操作步骤
4. **风险评估**：评估修复操作的风险和注意事项
5. **预防措施**：提供避免类似故障的预防建议

注意事项：
- 所有分析必须基于实际的诊断数据，不得编造信息
- 如果诊断不完整，应明确说明需要进一步执行的步骤
- 提供的解决方案应考虑系统安全性和业务连续性
- 使用专业术语，但确保清晰易懂

请生成结构化的诊断报告。"""

# 保留原有的兼容性接口
default_info_insufficient_prompt = question_analysis_instructions
default_diagnosis_plan_prompt = final_diagnosis_instructions

# 普通问答相关提示词

def get_qa_tool_planning_prompt(user_question: str, qa_context: str) -> str:
    """生成普通问答工具规划提示词"""
    return f"""你是一个专业的运维助手。请分析用户问题，自主决定是否需要使用工具来获取信息。

用户问题：{user_question}

对话上下文：
{qa_context}

请分析用户问题：
1. 如果需要获取实时信息（如当前时间、SOP文档内容等），请调用相应工具
2. 如果是概念性问题、技术解释或不需要实时数据，请直接回答，不要调用工具
3. 如果不确定，优先尝试调用工具获取准确信息

注意：只调用安全的查询工具，不要执行任何可能影响系统的操作。"""


def get_qa_answer_with_tools_prompt(user_question: str, qa_context: str, tool_info: str) -> str:
    """生成带工具结果的问答回答提示词"""
    return f"""你是一个专业的运维技术助手，擅长回答各种运维相关问题。

用户问题：{user_question}

对话历史上下文：
{qa_context}

工具执行结果：
{tool_info}

请根据用户问题、上下文信息和工具执行结果，提供专业、准确的回答。

重要：
1. 必须使用工具返回的实际结果来回答用户问题
2. 不要说"无法获取"或"建议通过其他方式"，直接使用工具结果
3. 保持专业和友好的语调
4. 如果工具返回的是JSON格式，请解析并使用其中的有效信息

请直接回答用户的问题。"""


def get_qa_answer_without_tools_prompt(user_question: str, qa_context: str) -> str:
    """生成不带工具结果的问答回答提示词"""
    return f"""你是一个专业的运维技术助手，擅长回答各种运维相关问题。

用户问题：{user_question}

对话历史上下文：
{qa_context}

请根据用户问题和上下文信息，提供专业、准确的回答。

回答要求：
1. 保持专业和友好的语调
2. 提供具体、实用的建议
3. 如果涉及操作步骤，请详细说明
4. 如果需要注意事项，请提醒用户

请直接回答用户的问题。"""


def get_qa_type_classification_prompt(user_question: str, qa_context: str) -> str:
    """生成问答类型分类提示词"""
    return f"""你是一个专业的问答类型分类器。请分析用户问题，判断属于以下哪种类型：

1. **technical_qa** - 技术问答：
   - 询问技术知识、操作方法、概念解释
   - 询问如何配置、安装、部署、监控等
   - 询问命令用法、脚本编写、架构设计等
   - 例如："如何配置nginx"、"什么是docker"、"怎么优化数据库性能"

2. **system_query** - 系统查询：
   - 需要查询实时信息、系统状态、配置信息
   - 需要搜索文档、SOP、历史记录
   - 需要获取当前时间、版本信息、统计数据
   - 例如："现在几点了"、"查询SOP文档"、"显示系统状态"、"搜索相关文档"

3. **follow_up** - 后续问题：
   - 对之前回答的追问和补充
   - 要求更详细解释或相关延伸
   - 基于历史对话的继续讨论
   - 例如："详细说明一下"、"还有其他方法吗"、"为什么会这样"

4. **casual_chat** - 日常聊天：
   - 问候、感谢、闲聊
   - 不涉及技术内容的对话
   - 例如："你好"、"谢谢"、"再见"

用户问题：{user_question}

对话历史：{qa_context}

请分析用户问题，只返回类型名称：technical_qa、system_query、follow_up、casual_chat"""


def get_technical_qa_prompt(user_question: str, qa_context: str) -> str:
    """生成技术问答提示词"""
    return f"""您是专业的运维技术专家，请回答用户的技术问题。

用户问题：{user_question}

对话上下文：
{qa_context}

请提供：
1. 直接回答用户问题
2. 如果涉及操作，提供具体步骤
3. 如果有风险，提醒注意事项
4. 如果需要更多信息，主动询问

回答要求：
- 专业准确，简洁明了
- 提供实用的解决方案
- 包含具体的命令或配置示例（如适用）
- 避免过于复杂的术语解释"""


def get_system_query_prompt(user_question: str, qa_context: str) -> str:
    """生成系统查询提示词"""
    return f"""您是运维系统助手，用户想要查询系统信息。

用户问题：{user_question}

对话上下文：
{qa_context}

请根据用户需求：
1. 如果有相关历史信息，提供摘要
2. 如果需要实时查询，说明查询方法
3. 如果信息不足，询问更多细节

回答要求：
- 直接回答用户查询
- 提供具体的查询命令或方法
- 如果涉及历史诊断，引用相关结果"""


def get_follow_up_prompt(user_question: str, qa_context: str) -> str:
    """生成后续问题提示词"""
    return f"""用户对之前的对话有后续问题，请基于上下文提供详细回答。

用户问题：{user_question}

对话上下文：
{qa_context}

请：
1. 结合之前的对话内容回答
2. 提供更详细的解释或补充信息
3. 如果用户问题不够清楚，主动澄清

回答要求：
- 连贯性强，与之前对话呼应
- 提供具体的补充信息
- 保持专业和友好的语调"""


def get_casual_chat_prompt(user_question: str, qa_context: str) -> str:
    """生成日常聊天提示词"""
    return f"""您是友好的运维助手，用户在进行日常对话。

用户问题：{user_question}

对话上下文：
{qa_context}

请：
1. 自然友好地回应用户
2. 如果涉及运维相关内容，提供简单说明
3. 保持专业但轻松的语调

回答要求：
- 简洁自然
- 友好亲切
- 如果合适，可以询问是否需要技术帮助"""
