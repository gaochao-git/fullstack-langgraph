#!/usr/bin/env python3
"""
LangExtract 敏感数据扫描器配置
提供敏感信息类型定义和模型配置
"""

import os
import logging
from typing import List, Optional, Dict, Any
from langextract.providers.openai import OpenAILanguageModel
from langextract.core import data

try:
    import langextract as lx
except ImportError:
    raise ImportError("请先安装 langextract: pip install langextract")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LangExtractSensitiveScanner:
    """LangExtract 敏感信息扫描配置类"""
    
    def __init__(self):
        """
        初始化扫描器配置，所有配置从settings获取
        """
        from src.shared.core.config import settings
        
        # 从settings获取所有配置
        self.model_id = settings.LLM_MODEL
        self.base_url = settings.LLM_BASE_URL
        self.api_key = settings.LLM_API_KEY
        
        # 定义敏感信息类型和示例
        self.sensitive_types = self._create_sensitive_examples()
        
    def _create_sensitive_examples(self) -> List[lx.data.ExampleData]:
        """创建敏感信息的 few-shot examples"""
        examples = []
        
        # 四要素示例 - 标准格式
        examples.append(lx.data.ExampleData(
            text="客户信息：姓名：李明，身份证：320106198808156789，手机：13912345678，银行卡：6222021234567890123。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="姓名",
                    extraction_text="李明"
                ),
                lx.data.Extraction(
                    extraction_class="身份证号",
                    extraction_text="320106198808156789"
                ),
                lx.data.Extraction(
                    extraction_class="手机号",
                    extraction_text="13912345678"
                ),
                lx.data.Extraction(
                    extraction_class="银行卡号",
                    extraction_text="6222021234567890123"
                )
            ]
        ))
        
        # 非标准格式示例 - 包含空格、中文数字等
        examples.append(lx.data.ExampleData(
            text="联系人王 小 明，身份证 3301 0619 9012 3456 78，电话：一三九 八八八八 九九九九，银行账号6228 4800 1234 5678 901",
            extractions=[
                lx.data.Extraction(
                    extraction_class="姓名",
                    extraction_text="王 小 明"
                ),
                lx.data.Extraction(
                    extraction_class="身份证号",
                    extraction_text="3301 0619 9012 3456 78"
                ),
                lx.data.Extraction(
                    extraction_class="手机号",
                    extraction_text="一三九 八八八八 九九九九"
                ),
                lx.data.Extraction(
                    extraction_class="银行卡号",
                    extraction_text="6228 4800 1234 5678 901"
                )
            ]
        ))
        
        return examples
    
    def scan_document(self, file_id: str, text: str) -> dict:
        """
        扫描单个文档的敏感信息
        
        Args:
            file_id: 文件ID
            text: 文件文本内容
            
        Returns:
            扫描结果，包含提取的敏感信息
        """
        try:
            # 创建 LangExtract Document 对象
            doc = lx.data.Document(document_id=file_id, text=text)
            # 创建模型实例
            model = OpenAILanguageModel(
                model_id=self.model_id,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=0,
                format_type=data.FormatType.JSON
            )
            
            # 提示词
            prompt = """识别并提取文本中的敏感信息。

敏感信息类型包括：
- 身份证号（18位数字，可能包含X）
- 手机号（11位数字，可能用中文表示）
- 银行卡号（16-19位数字）
- 邮箱地址
- 密码（通常跟在"密码"、"password"等词后面）
- API密钥/Token（以sk-、ak-等开头的字符串）
- 内网IP地址（10.x.x.x、192.168.x.x、172.16-31.x.x）
- 护照号、社保号、车牌号等

提取时请保持原文格式，包括空格、标点等。"""
            
            # 执行提取
            result = lx.extract(
                text_or_documents=[doc],
                prompt_description=prompt,
                examples=self.sensitive_types,
                model=model,
                max_workers=1,
                extraction_passes=1
            )
            
            # 处理结果
            result_list = list(result)
            if result_list and len(result_list) > 0:
                annotated_doc = result_list[0]
                return {
                    "success": True,
                    "file_id": file_id,
                    "extractions": len(annotated_doc.extractions),
                    "document": annotated_doc,
                    "sensitive_items": [
                        {
                            "type": ext.extraction_class,
                            "text": ext.extraction_text,
                            "position": (ext.char_interval.start_pos, ext.char_interval.end_pos) if ext.char_interval and ext.char_interval.start_pos is not None else None
                        }
                        for ext in annotated_doc.extractions
                    ]
                }
            else:
                return {
                    "success": True,
                    "file_id": file_id,
                    "extractions": 0,
                    "document": None,
                    "sensitive_items": []
                }
                
        except Exception as e:
            logger.error(f"扫描文件 {file_id} 时出错: {e}")
            return {
                "success": False,
                "file_id": file_id,
                "error": str(e)
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