"""敏感数据扫描智能体工具集"""

from typing import List, Dict, Any
from langchain_core.tools import tool
from sqlalchemy import select
from src.shared.db.config import get_sync_db
from src.apps.agent.models import AgentDocumentUpload
from src.shared.core.logging import get_logger

logger = get_logger(__name__)


@tool
def get_file_content(file_id: str) -> Dict[str, Any]:
    """
    根据文件ID获取文档内容
    
    Args:
        file_id: 文档ID
        
    Returns:
        包含文件信息和内容的字典
    """
    try:
        db_gen = get_sync_db()
        db = next(db_gen)
        
        # 查询文档
        result = db.execute(
            select(AgentDocumentUpload).where(
                AgentDocumentUpload.file_id == file_id
            )
        )
        document = result.scalar_one_or_none()
        
        if not document:
            return {
                "success": False,
                "error": f"找不到文件ID为 {file_id} 的文档"
            }
        
        # 检查处理状态
        if document.process_status != 2:  # 2 = READY
            return {
                "success": False,
                "error": f"文档尚未处理完成，当前状态: {document.process_status}"
            }
        
        return {
            "success": True,
            "file_id": file_id,
            "file_name": document.file_name,
            "file_size": document.file_size,
            "content": document.doc_content,  # 使用正确的属性名
            "upload_time": str(document.upload_time)
        }
        
    except Exception as e:
        logger.error(f"获取文件内容失败: {str(e)}")
        return {
            "success": False,
            "error": f"获取文件内容时发生错误: {str(e)}"
        }
    finally:
        try:
            next(db_gen)
        except StopIteration:
            pass


@tool
def analyze_sensitive_data_prompt(text: str, chunk_index: int = 0) -> str:
    """
    生成用于LLM分析敏感数据的提示词
    
    Args:
        text: 要分析的文本片段
        chunk_index: 分片索引
        
    Returns:
        格式化的提示词
    """
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

分析要求：
1. 逐行仔细检查，不要遗漏
2. 相似的敏感数据要准确计数，不要重复
3. 记录准确的行号位置
4. 评估每类数据的风险等级

请严格按照以下JSON格式返回（只返回JSON，不要有其他内容）：
{{
  "found_sensitive_data": true/false,
  "details": {{
    "身份证号": {{
      "count": 数量,
      "locations": ["第X行", "第Y行"],
      "risk": "高"
    }},
    "手机号": {{
      "count": 数量,
      "locations": ["第X行"],
      "risk": "中"
    }}
    // 根据实际发现的类型添加
  }},
  "total_count": 总数量,
  "risk_level": "高/中/低/无",
  "summary": "发现X个身份证号、Y个手机号..."
}}"""
    
    return prompt


@tool
def merge_scan_results(chunk_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    合并多个分片的扫描结果
    
    Args:
        chunk_results: 各分片的扫描结果列表
        
    Returns:
        合并后的扫描结果
    """
    merged = {
        "found_sensitive_data": False,
        "details": {},
        "total_count": 0,
        "risk_level": "无",
        "summaries": []
    }
    
    # 合并各分片的结果
    for idx, chunk_result in enumerate(chunk_results):
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
    
    return merged


@tool
def generate_scan_report(scan_results: Dict[str, Any], file_info: Dict[str, Any]) -> str:
    """
    生成敏感数据扫描报告
    
    Args:
        scan_results: 扫描结果
        file_info: 文件信息
        
    Returns:
        格式化的扫描报告
    """
    report_lines = [
        "# 敏感数据扫描报告",
        "",
        "## 文件信息",
        f"- 文件名: {file_info.get('file_name', '未知')}",
        f"- 文件大小: {file_info.get('file_size', 0)} bytes",
        f"- 扫描时间: {file_info.get('scan_time', '未知')}",
        "",
        "## 扫描结果摘要",
        f"- 风险等级: **{scan_results.get('risk_level', '未知')}**",
        f"- 敏感数据总数: {scan_results.get('total_count', 0)}",
        "",
        "## 详细结果"
    ]
    
    details = scan_results.get('details', {})
    if not details:
        report_lines.append("未发现敏感数据")
    else:
        for data_type, info in details.items():
            count = info.get('count', 0)
            positions = info.get('positions', [])
            
            report_lines.append(f"\n### {data_type}")
            report_lines.append(f"- 发现数量: {count}")
            
            if positions:
                report_lines.append("- 位置信息:")
                for pos in positions[:5]:  # 最多显示5个位置
                    report_lines.append(f"  - {pos}")
                if len(positions) > 5:
                    report_lines.append(f"  - ...还有{len(positions) - 5}处")
    
    # 添加建议
    report_lines.extend([
        "",
        "## 安全建议",
    ])
    
    risk_level = scan_results.get('risk_level', '未知')
    if risk_level == "高":
        report_lines.extend([
            "- 立即检查和处理文档中的敏感数据",
            "- 考虑对敏感信息进行脱敏或加密处理",
            "- 限制文档的访问权限",
            "- 定期进行安全审计"
        ])
    elif risk_level == "中":
        report_lines.extend([
            "- 审查文档中的敏感信息是否必要",
            "- 采取适当的数据保护措施",
            "- 确保符合相关的隐私法规要求"
        ])
    elif risk_level == "低":
        report_lines.extend([
            "- 继续保持良好的数据安全习惯",
            "- 定期检查敏感数据的使用情况"
        ])
    else:
        report_lines.extend([
            "- 文档安全性良好",
            "- 建议定期进行安全扫描"
        ])
    
    return "\n".join(report_lines)


async def get_scanner_tools(agent_id: str) -> List:
    """获取敏感数据扫描工具集"""
    tools = [
        get_file_content,
        analyze_sensitive_data_prompt,
        merge_scan_results,
        generate_scan_report
    ]
    
    logger.info(f"[{agent_id}] 加载了 {len(tools)} 个工具")
    return tools