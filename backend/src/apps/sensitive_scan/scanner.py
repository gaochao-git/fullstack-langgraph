"""
LangExtract 敏感数据扫描器
提供敏感信息扫描功能
"""

import os
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from langextract.providers.openai import OpenAILanguageModel
from langextract.core import data

try:
    import langextract as lx
except ImportError:
    raise ImportError("请先安装 langextract: pip install langextract")

from src.shared.core.logging import get_logger
from src.shared.core.config import settings

logger = get_logger(__name__)


class LangExtractSensitiveScanner:
    """LangExtract 敏感信息扫描配置类"""
    
    def __init__(self, 
                 model_id: Optional[str] = None, 
                 api_key: Optional[str] = None,
                 base_url: Optional[str] = None,
                 max_workers: Optional[int] = None,
                 max_char_buffer: Optional[int] = None):
        """
        初始化扫描器配置
        
        Args:
            model_id: 模型ID，默认从配置读取
            api_key: API密钥，默认从配置读取
            base_url: API地址，默认从配置读取
            max_workers: 并发扫描的最大工作线程数，默认从配置读取
            max_char_buffer: 单次推理的最大字符数，默认从配置读取
        """
        # 从配置或环境变量读取默认值
        self.model_id = model_id or getattr(settings, 'LANGEXTRACT_MODEL', 'Qwen/Qwen3-30B-A3B-Instruct-2507')
        self.base_url = base_url or getattr(settings, 'LANGEXTRACT_BASE_URL', 'https://api.siliconflow.cn/v1')
        self.max_workers = max_workers or getattr(settings, 'LANGEXTRACT_MAX_WORKERS', 1)
        self.max_char_buffer = max_char_buffer or getattr(settings, 'LANGEXTRACT_MAX_CHAR_BUFFER', 50000)
        
        # 设置API密钥
        self.api_key = api_key or getattr(settings, 'LANGEXTRACT_API_KEY', None) or os.environ.get("SILICONFLOW_API_KEY")
        if self.api_key:
            os.environ["OPENAI_API_KEY"] = self.api_key
        
        # 定义敏感信息类型和示例
        self.sensitive_types = self._create_sensitive_examples()
        
    def _create_sensitive_examples(self) -> List[lx.data.ExampleData]:
        """创建敏感信息的 few-shot examples"""
        examples = []
        
        # 身份证号示例
        examples.append(lx.data.ExampleData(
            text="张三的身份证号码是110101199001011234，请妥善保管。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="身份证号",
                    extraction_text="110101199001011234"
                )
            ]
        ))
        
        # 身份证号示例2 - 不同上下文
        examples.append(lx.data.ExampleData(
            text="按照152822198810154515标准进行身份验证。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="身份证号",
                    extraction_text="152822198810154515"
                )
            ]
        ))
        
        # 手机号示例
        examples.append(lx.data.ExampleData(
            text="请联系客服：13812345678，工作时间9:00-18:00。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="手机号",
                    extraction_text="13812345678"
                )
            ]
        ))
        
        # 银行卡号示例
        examples.append(lx.data.ExampleData(
            text="请将款项转入银行账户：6222021234567890123，开户行：工商银行。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="银行卡号",
                    extraction_text="6222021234567890123"
                )
            ]
        ))
        
        # 邮箱地址示例
        examples.append(lx.data.ExampleData(
            text="如有问题，请发送邮件至support@example.com咨询。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="邮箱地址",
                    extraction_text="support@example.com"
                )
            ]
        ))
        
        # API密钥示例
        examples.append(lx.data.ExampleData(
            text="配置文件中的API_KEY=sk-1234567890abcdef，请勿泄露。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="API密钥",
                    extraction_text="sk-1234567890abcdef"
                )
            ]
        ))
        
        # 密码示例
        examples.append(lx.data.ExampleData(
            text="用户名：admin，密码：Admin@123，请及时修改。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="用户名密码",
                    extraction_text="用户名：admin，密码：Admin@123"
                )
            ]
        ))
        
        # IP地址示例
        examples.append(lx.data.ExampleData(
            text="内网服务器地址：192.168.1.100:8080，仅限内部访问。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="内网IP",
                    extraction_text="192.168.1.100:8080"
                )
            ]
        ))
        
        # IP地址示例2 - 确保提取完整IP
        examples.append(lx.data.ExampleData(
            text="请登陆10.100.21.121进行系统配置。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="内网IP",
                    extraction_text="10.100.21.121"
                )
            ]
        ))
        
        # 车牌号示例
        examples.append(lx.data.ExampleData(
            text="车辆信息：京A12345，停放在B2层。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="车牌号",
                    extraction_text="京A12345"
                )
            ]
        ))
        
        # 社保号示例
        examples.append(lx.data.ExampleData(
            text="社保卡号：110101198001010001，请到人事部门领取。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="社保号",
                    extraction_text="110101198001010001"
                )
            ]
        ))
        
        # 护照号示例
        examples.append(lx.data.ExampleData(
            text="护照号码：E12345678，有效期至2030年。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="护照号",
                    extraction_text="E12345678"
                )
            ]
        ))
        
        return examples
    
    def scan_document(self, file_id: str, text: str, output_dir: str = "/tmp/scan_results", 
                      task_id: str = None, max_workers: Optional[int] = None, 
                      max_char_buffer: Optional[int] = None) -> dict:
        """
        扫描单个文档并生成结果文件
        
        Args:
            file_id: 文件ID
            text: 文件文本内容
            output_dir: 输出目录路径
            task_id: 任务ID（可选，用于生成文件名前缀）
            max_workers: 覆盖默认的并发工作线程数（可选）
            max_char_buffer: 覆盖默认的最大字符缓冲区大小（可选）
            
        Returns:
            {"status": "ok/error", "jsonl_path": xxx, "html_path": xxx}
        """
        try:
            # 使用传入的参数或默认值
            workers = max_workers if max_workers is not None else self.max_workers
            char_buffer = max_char_buffer if max_char_buffer is not None else self.max_char_buffer
            
            # 确保输出目录存在
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            
            # 使用 task_id_file_id 作为输出文件名前缀
            if task_id:
                file_prefix = f"{task_id}_{file_id}"
            else:
                file_prefix = file_id
                
            jsonl_path = Path(output_dir) / f"{file_prefix}.jsonl"
            html_path = Path(output_dir) / f"{file_prefix}.html"
            
            # 创建 LangExtract Document 对象
            lx_doc = lx.data.Document(
                document_id=file_id,
                text=text
            )
            
            # 创建模型实例
            model = OpenAILanguageModel(
                model_id=self.model_id,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=0.1,
                format_type=data.FormatType.JSON
            )
            
            # 提示词
            prompt = """提取文本中的敏感信息，包括：身份证号、护照号、手机号、邮箱、银行卡号、用户名密码、API密钥、内网IP、社保号、车牌号等。
注意：
1. 身份证号是15位或18位数字（18位最后一位可能是X），不要拆分
2. 手机号是11位数字，以13/14/15/16/17/18/19开头
3. IP地址格式为x.x.x.x（如192.168.1.100或10.100.21.121），可能带端口号，要提取完整
4. 单独用户名不算敏感，需要上下文判断
5. 确保提取完整的敏感信息，不要截断"""
            
            logger.info(f"开始扫描文档: {file_id}，文本长度: {len(text)} 字符，使用 {workers} 个工作线程，字符缓冲区: {char_buffer}")
            
            # 执行提取 - LangExtract 会自动处理分块和合并
            result = lx.extract(
                text_or_documents=[lx_doc],
                prompt_description=prompt,
                examples=self.sensitive_types,
                model=model,
                max_workers=workers,
                max_char_buffer=char_buffer,
                extraction_passes=1
            )
            
            # 收集结果
            annotated_documents = list(result)
            
            # 保存结果
            self.save_results(annotated_documents, str(jsonl_path))
            
            # 生成可视化
            self.generate_visualization(str(jsonl_path), str(html_path))
            
            return {
                "status": "ok",
                "jsonl_path": str(jsonl_path),
                "html_path": str(html_path)
            }
            
        except Exception as e:
            logger.error(f"扫描文档时出错: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "jsonl_path": None,
                "html_path": None
            }
    
    def save_results(self, annotated_documents: List[Any], output_path: str):
        """
        保存扫描结果到JSONL文件
        
        Args:
            annotated_documents: LangExtract的AnnotatedDocument对象列表
            output_path: 输出文件路径
        """
        import os
        output_dir = os.path.dirname(output_path)
        output_name = os.path.basename(output_path)
        
        lx.io.save_annotated_documents(
            annotated_documents,
            output_dir=output_dir,
            output_name=output_name,
            show_progress=False
        )
        logger.info(f"结果已保存到: {output_path}")
    
    def generate_visualization(self, jsonl_path: str, html_path: str) -> str:
        """
        生成可视化HTML
        
        Args:
            jsonl_path: JSONL文件路径
            html_path: 输出HTML文件路径
            
        Returns:
            HTML文件路径
        """
        html_content = lx.visualize(jsonl_path)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"可视化已生成: {html_path}")
        return html_path


# 创建全局扫描器实例
sensitive_scanner = LangExtractSensitiveScanner()