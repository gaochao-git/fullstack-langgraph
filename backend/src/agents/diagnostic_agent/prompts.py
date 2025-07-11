from agents.diagnostic_agent.utils import get_current_datetime
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
    
    return f"""当前时间：{get_current_datetime()}

用户最新输入：{user_question}
{current_info}
请从用户输入中提取或更新故障诊断信息。如果用户提供了新信息，请更新对应字段；如果没有提供新信息，保持原有值。

对于每个字段：
- fault_ip: 提取IP地址，如192.168.1.100或82.156.146.51
- fault_time: 提取时间信息，支持各种格式
- fault_info: 提取故障现象描述，如"磁盘空间满"、"内存不足"等
- sop_id: 提取SOP编号，如sop_101、SOP-001等

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
            "排查SOP编号": "对应的标准作业程序编号（如：SOP-001）"
        }
        
        missing_items = []
        for i, field in enumerate(question_analysis.missing_fields, 1):
            description = field_descriptions.get(field, "")
            missing_items.append(f"{i}. **{field}**：{description}")
        
        missing_fields_info = f"""📋 还需要补充以下信息：

{'\n'.join(missing_items)}"""
    
    # 使用f-string构建完整提示词
    return f"""❗ 故障诊断信息不完整，当前状态：

{status_info}

{missing_fields_info}
💡 您可以分多次补充，信息完整后将自动开始诊断。"""

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

# 工具规划提示词 - 严格按照SOP执行
tool_planning_instructions = """您是专业的故障诊断专家，必须严格按照SOP的步骤执行诊断。

【重要原则】
- 必须严格按照SOP中的步骤顺序执行
- 不能跳过SOP中的任何步骤
- 每个步骤都要完整执行
- 如果SOP未加载，必须先加载SOP

故障信息：
- 故障IP：{fault_ip}
- 故障时间：{fault_time}
- 故障现象：{fault_info}
- SOP编号：{sop_id}

当前SOP状态：{sop_state}
SOP内容：{sop_content}

执行策略：
1. 如果SOP未加载（sop_state != "loaded"），必须先调用get_sop_content获取SOP内容
2. 如果SOP已加载，严格按照SOP中的步骤顺序执行：
   - 识别SOP中的当前步骤
   - 选择对应的诊断工具
   - 确保不跳过任何必要步骤
   - 按照SOP要求的参数执行工具

可用工具：
SOP工具：
- get_sop_content: 获取SOP内容（必须先执行）
- get_sop_detail: 获取SOP详情

SSH诊断工具：
- get_system_info: 获取系统信息
- analyze_processes: 分析进程状态
- check_service_status: 检查服务状态
- analyze_system_logs: 分析系统日志
- execute_system_command: 执行系统命令

请根据当前SOP状态，选择下一个必须执行的工具。严格按照SOP要求，不得随意修改或跳过步骤。"""

# 诊断反思提示词 - 按SOP顺序执行，找到根因可提前结束
reflection_instructions = """您是专业的故障诊断专家，负责检查SOP执行进度和根因分析。

【核心职责】
- 确保严格按照SOP步骤顺序执行
- 检查每个已执行步骤的结果
- 判断是否已找到故障根因
- 如果找到明确根因，可以提前结束诊断

当前执行状态：
- 当前步骤：{diagnosis_step_count}/{max_diagnosis_steps}
- 故障信息：{fault_info}
- SOP状态：{sop_state}
- 已收集信息：{diagnosis_results}

判断标准：
1. 必须按照SOP顺序执行，不能跳过步骤
2. 如果通过已执行的SOP步骤找到了明确的根因，可以提前结束
3. 如果未找到根因，继续执行下一个SOP步骤
4. 只有在以下情况下才能结束诊断：
   - 找到了明确的故障根因
   - 或者已完成所有SOP步骤

输出格式：
请将响应格式化为包含以下确切键的JSON对象：
{{
    "is_complete": true/false,  // 是否可以结束诊断（找到根因或完成所有SOP步骤）
    "sop_steps_completed": ["已完成的SOP步骤"],
    "sop_steps_remaining": ["还需执行的SOP步骤"],
    "root_cause_found": true/false,  // 是否找到了明确的根因
    "root_cause_analysis": "根因分析结果",
    "next_steps": ["下一个需要执行的SOP步骤"],
    "user_recommendations": ["基于当前结果给用户的建议"],
    "termination_reason": "结束原因：root_cause_found（找到根因）或 sop_completed（完成所有SOP）或 continue（继续诊断）"
}}

重要：只有找到明确根因或完成所有SOP步骤才能将is_complete设为true。"""

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
