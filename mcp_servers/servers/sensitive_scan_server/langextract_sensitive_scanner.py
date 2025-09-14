#!/usr/bin/env python3
"""
LangExtract 敏感数据扫描器
使用 Google LangExtract 进行精确的敏感信息提取和可视化
"""

import os
import logging
from typing import List, Optional
from langextract.providers.openai import OpenAILanguageModel
from langextract.core import data
from langextract.core import types as core_types

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
    """使用 LangExtract 的敏感数据扫描器"""
    
    def __init__(self, 
                 model_id: str = "Qwen/Qwen3-30B-A3B-Instruct-2507", 
                 api_key: Optional[str] = None,
                 base_url: str = "https://api.siliconflow.cn/v1"):
        """
        初始化扫描器（专用于SiliconFlow）
        
        Args:
            model_id: 模型ID
            api_key: API密钥，如果为None则从环境变量读取
            base_url: API地址，默认为SiliconFlow
        """
        self.model_id = model_id
        self.base_url = base_url
        
        # 设置API密钥
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("SILICONFLOW_API_KEY")
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
        
        # 文档摘要示例
        examples.append(lx.data.ExampleData(
            text="本公司2023年度财务报告显示，营业收入达到5000万元，同比增长20%。主要增长来自于新产品线的推出和市场拓展。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="文档摘要",
                    extraction_text="公司2023年营收5000万元，同比增长20%，主要得益于新产品和市场拓展"
                )
            ]
        ))
        
        return examples
    
    def scan_text(self, text: str, document_name: str = "document"):
        """
        扫描文本中的敏感信息
        
        Args:
            text: 要扫描的文本
            document_name: 文档名称
            
        Returns:
            langextract的AnnotatedDocument对象
        """
        # 创建SiliconFlow兼容的OpenAI模型
        class SiliconFlowModel(OpenAILanguageModel):
            @property
            def requires_fence_output(self) -> bool:
                return True
            
            def _process_single_prompt(self, prompt: str, config: dict):
                try:
                    normalized_config = self._normalize_reasoning_params(config)
                    system_message = 'You are a helpful assistant that responds in JSON format. Wrap your JSON response in ```json ... ``` code blocks.'
                    messages = [
                        {'role': 'system', 'content': system_message},
                        {'role': 'user', 'content': prompt}
                    ]
                    api_params = {
                        'model': self.model_id,
                        'messages': messages,
                        'n': 1,
                        'temperature': normalized_config.get('temperature', self.temperature)
                    }
                    if (v := normalized_config.get('max_output_tokens')) is not None:
                        api_params['max_tokens'] = v
                    response = self._client.chat.completions.create(**api_params)
                    return core_types.ScoredOutput(
                        output=response.choices[0].message.content,
                        score=1.0
                    )
                except Exception as e:
                    raise Exception(f"API error: {e}") from e
        
        model = SiliconFlowModel(
            model_id=self.model_id,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.1,
            format_type=data.FormatType.JSON
        )
        
        # 提示词
        prompt = """提取文本中的敏感信息，包括：身份证号、护照号、手机号、邮箱、银行卡号、用户名密码、API密钥、内网IP、社保号、车牌号等。
同时生成一句话的文档摘要（限50字）。
注意：单独用户名不算敏感，需要上下文判断。"""
        
        # 执行提取
        result = lx.extract(
            text_or_documents=text,
            prompt_description=prompt,
            examples=self.sensitive_types,
            model=model,
            max_workers=1,
            extraction_passes=1
        )
        
        # 转换为列表，因为 lx.extract 返回的是生成器
        return list(result)
    
    def scan_files(self, file_contents: List[dict]):
        """
        批量扫描文本内容
        
        Args:
            file_contents: 文件内容列表，格式为 [{"file_id": "xxx", "content": "text"}, ...]
            
        Returns:
            langextract的AnnotatedDocument对象列表
        """
        if not file_contents:
            raise ValueError("file_contents 不能为空")
        
        # 将文本转换为 Document 对象
        documents = []
        for item in file_contents:
            if "file_id" not in item or "content" not in item:
                raise ValueError(f"缺少必要字段 file_id 或 content: {item}")
            
            doc = lx.data.Document(
                document_id=item["file_id"],
                text=item["content"]
            )
            documents.append(doc)
        # 创建SiliconFlow模型
        class SiliconFlowModel(OpenAILanguageModel):
            @property
            def requires_fence_output(self) -> bool:
                return True
            
            def _process_single_prompt(self, prompt: str, config: dict):
                try:
                    normalized_config = self._normalize_reasoning_params(config)
                    system_message = 'You are a helpful assistant that responds in JSON format. Wrap your JSON response in ```json ... ``` code blocks.'
                    messages = [
                        {'role': 'system', 'content': system_message},
                        {'role': 'user', 'content': prompt}
                    ]
                    api_params = {
                        'model': self.model_id,
                        'messages': messages,
                        'n': 1,
                        'temperature': normalized_config.get('temperature', self.temperature)
                    }
                    if (v := normalized_config.get('max_output_tokens')) is not None:
                        api_params['max_tokens'] = v
                    response = self._client.chat.completions.create(**api_params)
                    return core_types.ScoredOutput(
                        output=response.choices[0].message.content,
                        score=1.0
                    )
                except Exception as e:
                    raise Exception(f"API error: {e}") from e
        
        model = SiliconFlowModel(
            model_id=self.model_id,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=0.1,
            format_type=data.FormatType.JSON
        )
        
        # 提示词
        prompt = """提取文本中的敏感信息，包括：身份证号、护照号、手机号、邮箱、银行卡号、用户名密码、API密钥、内网IP、社保号、车牌号等。
同时生成一句话的文档摘要（限50字）。
注意：单独用户名不算敏感，需要上下文判断。"""
        
        # 批量提取
        results = lx.extract(
            text_or_documents=documents,  # 传入 Document 对象列表
            prompt_description=prompt,
            examples=self.sensitive_types,
            model=model,
            max_workers=4,  # langextract会自动处理并发
            extraction_passes=1
        )
        
        return list(results)  # 转换为列表返回
    
    def generate_visualization(self, annotated_documents: List, output_path: str = "scan_visualization.html") -> str:
        """
        生成可视化HTML报告
        
        Args:
            annotated_documents: langextract的AnnotatedDocument对象列表
            output_path: 输出HTML文件路径
            
        Returns:
            HTML文件路径
        """
        # 保存为JSONL
        output_dir = os.path.dirname(output_path) or "."
        output_name = os.path.basename(output_path).replace('.html', '.jsonl')
        
        # 保存文档
        lx.io.save_annotated_documents(
            annotated_documents, 
            output_dir=output_dir,
            output_name=output_name,
            show_progress=False
        )
        
        # 生成可视化
        jsonl_path = os.path.join(output_dir, output_name)
        html_content = lx.visualize(jsonl_path)
        
        # 保存HTML
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    


# 测试代码
if __name__ == "__main__":
    # 初始化扫描器
    scanner = LangExtractSensitiveScanner(
        model_id="Qwen/Qwen3-30B-A3B-Instruct-2507",
        api_key="your-api-key"
    )
    
    # 测试文本
    test_text = """
    尊敬的张先生（身份证：110101199001011234），
    您的订单已确认，联系电话：13812345678
    银行卡号：6222021234567890123
    """
    
    # 扫描单个文本
    result = scanner.scan_text(test_text)
    # result 是一个 AnnotatedDocument 对象或列表
    if isinstance(result, list) and len(result) > 0:
        doc = result[0]
        print(f"提取到 {len(doc.extractions)} 个敏感信息")
        for extraction in doc.extractions:
            print(f"- {extraction.extraction_class}: {extraction.extraction_text}")
    else:
        print("未提取到敏感信息")
    
    # 批量扫描文件
    files = ["doc1.txt", "doc2.txt"]
    results = scanner.scan_files(files)
    
    # 生成可视化
    viz_path = scanner.generate_visualization(list(results))
    print(f"可视化报告: {viz_path}")