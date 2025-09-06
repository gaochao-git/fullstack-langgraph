"""敏感数据扫描智能体节点实现"""

import json
import uuid
from typing import Dict, Any, List
from datetime import datetime
from langgraph.prebuilt import ToolNode
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .state import ScannerState, ChunkState
from .tools import get_file_content, generate_scan_report
from .configuration import INIT_AGENT_CONFIG, AGENT_DETAIL_CONFIG
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


async def initialize_scan(state: ScannerState, config: RunnableConfig) -> Dict[str, Any]:
    """初始化扫描任务，从工具消息中提取文件内容"""
    import json
    from langchain_core.messages import ToolMessage, AIMessage
    
    # 获取file_ids
    file_ids = state.get("file_ids", [])
    
    # 从消息中提取文件内容
    file_contents = {}
    messages = state.get("messages", [])
    
    # 遍历消息查找工具返回的文件内容
    for msg in messages:
        if isinstance(msg, ToolMessage):
            try:
                tool_result = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                if isinstance(tool_result, dict) and tool_result.get("success") and "file_id" in tool_result:
                    file_id = tool_result["file_id"]
                    file_contents[file_id] = {
                        "content": tool_result.get("content", ""),
                        "file_name": tool_result.get("file_name", ""),
                        "file_size": tool_result.get("file_size", 0)
                    }
                    logger.info(f"从工具消息中提取文件 {file_id} 的内容")
            except Exception as e:
                logger.warning(f"解析工具消息失败: {e}")
    
    # 生成扫描开始消息
    if file_contents:
        scan_start_msg = f"🔍 开始扫描 {len(file_contents)} 个文件...\n\n"
        for idx, (file_id, file_info) in enumerate(file_contents.items()):
            scan_start_msg += f"✅ 文件 {idx + 1}: {file_info['file_name']} (ID: {file_id})\n"
        
        messages.append(AIMessage(content=scan_start_msg))
        logger.info(f"成功获取 {len(file_contents)} 个文件的内容，准备开始扫描")
    else:
        logger.warning("未能从消息中提取任何文件内容")
        error_msg = "⚠️ 未能获取任何文件内容，扫描终止。"
        messages.append(AIMessage(content=error_msg))
        
        return {
            **state,
            "messages": messages,
            "errors": state.get("errors", []) + ["未能获取任何文件内容"]
        }
    
    # 更新状态
    return {
        **state,
        "file_ids": list(file_contents.keys()),
        "file_contents": file_contents,
        "messages": messages,
        "errors": state.get("errors", []),
        "chunk_size": state.get("chunk_size", AGENT_DETAIL_CONFIG.get("chunk_size", 200)),
        "max_parallel_chunks": state.get("max_parallel_chunks", AGENT_DETAIL_CONFIG.get("max_parallel_chunks", 5)),
        "sensitive_types": state.get("sensitive_types", ["身份证", "手机号", "银行卡", "邮箱", "密码", "API密钥"])
    }


async def create_chunks(state: ScannerState, config: RunnableConfig) -> Dict[str, Any]:
    """将文档内容分片，准备并行处理"""
    from langchain_core.messages import AIMessage
    
    file_contents = state.get("file_contents", {})
    chunk_size = state.get("chunk_size", 200)  # 改为200字符测试
    
    chunks = []
    chunk_info_msg = "📄 开始对文件进行分片处理...\n\n"
    
    for idx, (file_id, file_info) in enumerate(file_contents.items()):
        content = file_info.get("content", "")
        file_name = file_info.get("file_name", "")
        
        chunk_info_msg += f"📁 文件 {idx + 1}: {file_name}\n"
        chunk_info_msg += f"   - 文件大小: {len(content)} 字符\n"
        
        # 如果内容较小，不需要分片
        if len(content) <= chunk_size:
            chunks.append({
                "chunk_id": f"{file_id}_chunk_0",
                "file_id": file_id,
                "file_name": file_name,
                "content": content,
                "chunk_index": 0,
                "total_chunks": 1
            })
        else:
            # 按行分割以避免在单词中间切断
            lines = content.split('\n')
            current_chunk = []
            current_size = 0
            chunk_index = 0
            
            for line in lines:
                line_size = len(line) + 1  # +1 for newline
                
                if current_size + line_size > chunk_size and current_chunk:
                    # 创建新分片
                    chunk_content = '\n'.join(current_chunk)
                    chunks.append({
                        "chunk_id": f"{file_id}_chunk_{chunk_index}",
                        "file_id": file_id,
                        "file_name": file_name,
                        "content": chunk_content,
                        "chunk_index": chunk_index,
                        "total_chunks": -1  # 暂时未知总数
                    })
                    chunk_index += 1
                    current_chunk = [line]
                    current_size = line_size
                else:
                    current_chunk.append(line)
                    current_size += line_size
            
            # 处理最后一个分片
            if current_chunk:
                chunk_content = '\n'.join(current_chunk)
                chunks.append({
                    "chunk_id": f"{file_id}_chunk_{chunk_index}",
                    "file_id": file_id,
                    "file_name": file_name,
                    "content": chunk_content,
                    "chunk_index": chunk_index,
                    "total_chunks": chunk_index + 1
                })
                
            # 更新总分片数
            total_chunks = chunk_index + 1
            for chunk in chunks:
                if chunk["file_id"] == file_id:
                    chunk["total_chunks"] = total_chunks
                    
            chunk_info_msg += f"   - 分片数量: {total_chunks} 个\n"
        
        chunk_info_msg += "\n"
    
    chunk_info_msg += f"📊 总计创建了 {len(chunks)} 个分片，准备进行并行扫描...\n"
    logger.info(f"创建了 {len(chunks)} 个分片")
    
    # 添加分片信息到消息
    messages = state.get("messages", [])
    messages.append(AIMessage(content=chunk_info_msg))
    
    return {
        **state,
        "chunks": chunks,
        "messages": messages
    }


async def scan_chunk_with_llm(chunk: Dict[str, Any], llm, config: RunnableConfig) -> Dict[str, Any]:
    """使用LLM扫描单个分片"""
    try:
        from langchain_core.messages import HumanMessage
        import json
        
        # 直接生成分析提示词（不使用工具）
        text = chunk["content"]
        chunk_index = chunk["chunk_index"]
        
        prompt = f"""作为专业的敏感数据扫描专家，请仔细分析以下文本片段（这是第{chunk_index + 1}个片段），识别其中所有的敏感信息。

===== 待分析文本开始 =====
{text}
===== 待分析文本结束 =====

请系统性地识别以下类型的敏感信息：

【个人身份信息】
- 身份证号：18位数字，格式如 110101199001011234
- 手机号码：11位，如 13812345678、15912345678
- 银行卡号：16-19位连续数字
- 社保卡号、护照号、驾驶证号等

【账户凭证信息】
- 邮箱地址：如 user@example.com
- 用户名密码：password=xxx、pwd:xxx、密码：xxx
- 登录凭证、会话ID等

【技术敏感信息】
- API密钥：api_key=xxx、apikey:xxx、access_key、secret_key
- 访问令牌：token=xxx、bearer xxx、auth_token
- 数据库连接：mysql://user:pass@host、mongodb://xxx
- 私钥证书：BEGIN PRIVATE KEY、BEGIN RSA PRIVATE KEY

【网络信息】
- IP地址：如 192.168.1.1、10.0.0.1
- 内网地址、服务器地址
- URL中包含的敏感参数

【其他敏感数据】
- 任何看起来像密钥、密码、证书的字符串
- Base64编码的可能敏感内容
- 其他你认为敏感的信息

请按照以下格式回复，每一项都必须单独一行，不要遗漏任何标记：

[扫描结果开始]
发现敏感数据: 是/否

[敏感数据详情]
身份证号: X个，位于第Y行、第Z行
手机号: X个，位于第Y行
银行卡号: X个，位于第Y行
邮箱地址: X个，位于第Y行
API密钥: X个，位于第Y行
数据库连接: X个，位于第Y行
IP地址: X个，位于第Y行
（根据实际发现的类型列出，如果某类型未发现则写"0个"）

[统计信息]
敏感数据总数: X个
风险等级: 高/中/低/无

[扫描摘要]
本片段发现X个身份证号、Y个手机号...（简要总结）
[扫描结果结束]"""
        
        # 调用LLM进行分析
        messages = [HumanMessage(content=prompt)]
        response = await llm.ainvoke(messages, config=config)
        
        # 解析LLM返回的结构化文本
        try:
            content = response.content
            import re
            
            # 初始化结果
            scan_result = {
                "found_sensitive_data": False,
                "details": {},
                "total_count": 0,
                "risk_level": "无",
                "summary": ""
            }
            
            # 提取是否发现敏感数据
            found_match = re.search(r'发现敏感数据:\s*(是|否)', content)
            if found_match:
                scan_result["found_sensitive_data"] = found_match.group(1) == "是"
            
            # 提取各类敏感数据
            sensitive_types = [
                "身份证号", "手机号", "银行卡号", "邮箱地址", 
                "API密钥", "数据库连接", "IP地址", "密码信息",
                "访问令牌", "私钥证书"
            ]
            
            for data_type in sensitive_types:
                # 匹配格式：类型: X个，位于第Y行、第Z行
                pattern = rf'{data_type}:\s*(\d+)个[，,]?(.*)(?=\n|$)'
                match = re.search(pattern, content)
                if match:
                    count = int(match.group(1))
                    if count > 0:
                        locations_str = match.group(2)
                        # 提取位置信息
                        locations = re.findall(r'第(\d+)行', locations_str)
                        locations = [f"第{loc}行" for loc in locations]
                        
                        scan_result["details"][data_type] = {
                            "count": count,
                            "locations": locations,
                            "risk": "高" if data_type in ["身份证号", "银行卡号", "API密钥", "私钥证书"] else "中"
                        }
            
            # 提取总数
            total_match = re.search(r'敏感数据总数:\s*(\d+)个', content)
            if total_match:
                scan_result["total_count"] = int(total_match.group(1))
            else:
                # 如果没找到总数，从details计算
                scan_result["total_count"] = sum(
                    info["count"] for info in scan_result["details"].values()
                )
            
            # 提取风险等级
            risk_match = re.search(r'风险等级:\s*(高|中|低|无)', content)
            if risk_match:
                scan_result["risk_level"] = risk_match.group(1)
            
            # 提取摘要
            summary_match = re.search(r'\[扫描摘要\]\n(.+?)(?=\[扫描结果结束\]|$)', content, re.DOTALL)
            if summary_match:
                scan_result["summary"] = summary_match.group(1).strip()
            
        except Exception as e:
            logger.warning(f"解析LLM返回内容失败: {e}")
            scan_result = {
                "found_sensitive_data": False,
                "details": {},
                "total_count": 0,
                "risk_level": "无",
                "summary": "解析结果失败"
            }
        
        return {
            "chunk_id": chunk["chunk_id"],
            "file_id": chunk["file_id"],
            "file_name": chunk["file_name"],
            "chunk_index": chunk["chunk_index"],
            "total_chunks": chunk["total_chunks"],
            "scan_result": scan_result,
            "success": True
        }
    except Exception as e:
        logger.error(f"LLM扫描分片 {chunk['chunk_id']} 时出错: {str(e)}")
        return {
            "chunk_id": chunk["chunk_id"],
            "file_id": chunk["file_id"],
            "file_name": chunk["file_name"],
            "chunk_index": chunk["chunk_index"],
            "total_chunks": chunk["total_chunks"],
            "scan_result": None,
            "success": False,
            "error": str(e)
        }


async def parallel_scan(state: ScannerState, config: RunnableConfig) -> Dict[str, Any]:
    """串行扫描所有分片 - 使用LLM"""
    from langchain_core.messages import AIMessage
    
    chunks = state.get("chunks", [])
    
    # 获取LLM配置
    from .llm import get_llm_config
    from .configuration import INIT_AGENT_CONFIG
    from langchain_openai import ChatOpenAI
    
    agent_id = INIT_AGENT_CONFIG["agent_id"]
    selected_model = config.get("configurable", {}).get("selected_model") if config else None
    llm_config = get_llm_config(agent_id, selected_model)
    llm = ChatOpenAI(**llm_config)
    
    # 输出扫描开始信息
    scan_progress_msg = f"🔎 开始串行扫描 {len(chunks)} 个分片..."
    scan_progress_msg += f"\n   - 使用模型: {llm_config.get('model', '未知')}"
    
    messages = state.get("messages", [])
    messages.append(AIMessage(content=scan_progress_msg))
    
    chunk_results = []
    
    # 按文件分组显示进度
    file_chunks_map = {}
    for chunk in chunks:
        file_name = chunk["file_name"]
        if file_name not in file_chunks_map:
            file_chunks_map[file_name] = []
        file_chunks_map[file_name].append(chunk)
    
    # 串行处理所有分片
    current_file = None
    for i, chunk in enumerate(chunks):
        file_name = chunk["file_name"]
        chunk_index = chunk["chunk_index"]
        total_chunks = chunk["total_chunks"]
        
        # 如果是新文件，输出文件信息
        if file_name != current_file:
            current_file = file_name
            file_msg = f"\n📄 正在扫描文件: {file_name} ({total_chunks} 个分片)"
            messages.append(AIMessage(content=file_msg))
        
        # 扫描单个分片
        chunk_result = await scan_chunk_with_llm(chunk, llm, config)
        chunk_results.append(chunk_result)
        
        # 输出进度（每10个分片或最后一个分片时）
        if (i + 1) % 10 == 0 or i == len(chunks) - 1:
            progress_msg = f"   进度: {i + 1}/{len(chunks)} 分片已完成"
            messages.append(AIMessage(content=progress_msg))
    
    # 输出扫描完成信息
    complete_msg = f"\n✅ 完成所有 {len(chunk_results)} 个分片的扫描，正在汇总结果...\n"
    messages.append(AIMessage(content=complete_msg))
    
    logger.info(f"完成 {len(chunk_results)} 个分片的LLM扫描")
    
    return {
        **state,
        "chunk_results": chunk_results,
        "messages": messages
    }


async def aggregate_results(state: ScannerState, config: RunnableConfig) -> Dict[str, Any]:
    """聚合扫描结果（Reduce阶段）"""
    chunk_results = state.get("chunk_results", [])
    file_contents = state.get("file_contents", {})
    
    # 按文件分组结果
    file_chunks = {}
    for chunk_result in chunk_results:
        if not chunk_result.get("success"):
            continue
            
        file_id = chunk_result["file_id"]
        if file_id not in file_chunks:
            file_chunks[file_id] = {
                "file_name": chunk_result["file_name"],
                "chunks": [],
                "total_chunks": chunk_result["total_chunks"]
            }
        
        file_chunks[file_id]["chunks"].append(chunk_result.get("scan_result", {}))
    
    # 对每个文件合并其分片结果
    file_results = {}
    total_sensitive_count = 0
    
    for file_id, file_data in file_chunks.items():
        # 手动合并该文件的所有分片结果
        merged = {
            "found_sensitive_data": False,
            "details": {},
            "total_count": 0,
            "risk_level": "无",
            "summaries": []
        }
        
        # 合并各分片的结果
        for idx, chunk_result in enumerate(file_data["chunks"]):
            if not chunk_result or not isinstance(chunk_result, dict):
                continue
                
            if chunk_result.get("found_sensitive_data", False):
                merged["found_sensitive_data"] = True
                
            # 合并详细信息
            details = chunk_result.get("details", {})
            for data_type, info in details.items():
                if data_type not in merged["details"]:
                    merged["details"][data_type] = {
                        "count": 0,
                        "locations": [],
                        "risk": "低"
                    }
                
                merged["details"][data_type]["count"] += info.get("count", 0)
                
                # 添加分片标识到位置信息
                locations = info.get("locations", [])
                for loc in locations:
                    merged["details"][data_type]["locations"].append(f"分片{idx+1}-{loc}")
                
                # 更新风险等级（取最高）
                risk_levels = ["低", "中", "高"]
                current_risk = info.get("risk", "低")
                if risk_levels.index(current_risk) > risk_levels.index(merged["details"][data_type]["risk"]):
                    merged["details"][data_type]["risk"] = current_risk
            
            # 收集摘要
            if summary := chunk_result.get("summary"):
                merged["summaries"].append(f"分片{idx+1}: {summary}")
            
            merged["total_count"] += chunk_result.get("total_count", 0)
        
        # 评估总体风险等级
        if merged["total_count"] == 0:
            merged["risk_level"] = "无"
        elif merged["total_count"] < 10:
            merged["risk_level"] = "低"
        elif merged["total_count"] < 50:
            merged["risk_level"] = "中"
        else:
            merged["risk_level"] = "高"
        
        file_results[file_id] = {
            "file_name": file_data["file_name"],
            "chunks_scanned": len(file_data["chunks"]),
            "total_chunks": file_data["total_chunks"],
            "total_count": merged.get("total_count", 0),
            "details": merged.get("details", {}),
            "risk_level": merged.get("risk_level", "无"),
            "summaries": merged.get("summaries", [])
        }
        
        total_sensitive_count += merged.get("total_count", 0)
    
    # 计算总体风险等级
    if total_sensitive_count == 0:
        overall_risk = "无"
    elif total_sensitive_count < 10:
        overall_risk = "低"
    elif total_sensitive_count < 50:
        overall_risk = "中"
    else:
        overall_risk = "高"
    
    scan_results = {
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files_scanned": len(file_results),
        "total_sensitive_items": total_sensitive_count,
        "overall_risk_level": overall_risk,
        "file_results": file_results
    }
    
    logger.info(f"聚合完成：扫描了 {len(file_results)} 个文件，发现 {total_sensitive_count} 个敏感项")
    
    return {
        **state,
        "scan_results": scan_results
    }


async def generate_report(state: ScannerState, config: RunnableConfig) -> Dict[str, Any]:
    """生成最终报告"""
    scan_results = state.get("scan_results", {})
    errors = state.get("errors", [])
    
    # 生成报告内容
    report_lines = [
        "# 敏感数据批量扫描报告",
        "",
        f"## 扫描概览",
        f"- 扫描时间: {scan_results.get('scan_time', '未知')}",
        f"- 扫描文件数: {scan_results.get('files_scanned', 0)}",
        f"- 敏感数据总数: {scan_results.get('total_sensitive_items', 0)}",
        f"- 总体风险等级: **{scan_results.get('overall_risk_level', '未知')}**"
    ]
    
    # 添加各文件的扫描结果
    file_results = scan_results.get("file_results", {})
    if file_results:
        report_lines.extend(["", "## 文件扫描详情"])
        
        for file_id, result in file_results.items():
            report_lines.extend([
                "",
                f"### 📄 {result.get('file_name', file_id)}",
                f"- 扫描分片: {result.get('chunks_scanned', 0)}/{result.get('total_chunks', 0)}",
                f"- 敏感数据: {result.get('total_count', 0)} 项"
            ])
            
            details = result.get("details", {})
            if details:
                report_lines.append("- 详细分类:")
                for data_type, info in details.items():
                    count = info.get("count", 0)
                    if count > 0:
                        report_lines.append(f"  - {data_type}: {count} 个")
                        positions = info.get("positions", [])
                        if positions:
                            for pos in positions[:3]:  # 只显示前3个位置
                                report_lines.append(f"    - {pos}")
                            if len(positions) > 3:
                                report_lines.append(f"    - ...还有 {len(positions) - 3} 处")
    
    # 添加错误信息
    if errors:
        report_lines.extend([
            "",
            "## ⚠️ 处理错误",
        ])
        for error in errors:
            report_lines.append(f"- {error}")
    
    # 添加建议
    report_lines.extend([
        "",
        "## 💡 安全建议",
    ])
    
    risk_level = scan_results.get("overall_risk_level", "未知")
    if risk_level == "高":
        report_lines.extend([
            "1. **立即行动**: 文档包含大量敏感信息，需要立即采取保护措施",
            "2. **数据脱敏**: 对敏感数据进行脱敏处理或使用加密存储",
            "3. **访问控制**: 严格限制文档的访问权限，实施最小权限原则",
            "4. **审计追踪**: 建立完整的数据访问审计机制",
            "5. **合规检查**: 确保符合GDPR、个人信息保护法等相关法规"
        ])
    elif risk_level == "中":
        report_lines.extend([
            "1. **风险评估**: 评估敏感信息的必要性和风险",
            "2. **数据分类**: 对不同敏感级别的数据进行分类管理",
            "3. **定期审查**: 定期审查和更新数据保护策略",
            "4. **员工培训**: 加强数据安全意识培训"
        ])
    elif risk_level == "低":
        report_lines.extend([
            "1. **保持警惕**: 继续保持良好的数据安全习惯",
            "2. **定期扫描**: 建议定期进行敏感数据扫描",
            "3. **预防为主**: 在数据产生源头就做好保护"
        ])
    else:
        report_lines.extend([
            "1. **安全良好**: 未发现敏感数据，文档安全性良好",
            "2. **持续监控**: 建议定期进行安全扫描"
        ])
    
    final_report = "\n".join(report_lines)
    
    # 创建AI响应消息
    response_message = AIMessage(content=final_report)
    
    return {
        **state,
        "final_report": final_report,
        "messages": state.get("messages", []) + [response_message]
    }


# 使用标准的工具节点
from langgraph.prebuilt import ToolNode
from .tools import analyze_sensitive_data_prompt, merge_scan_results, generate_scan_report

# 创建工具节点实例
tool_node = ToolNode([get_file_content, analyze_sensitive_data_prompt, merge_scan_results, generate_scan_report])