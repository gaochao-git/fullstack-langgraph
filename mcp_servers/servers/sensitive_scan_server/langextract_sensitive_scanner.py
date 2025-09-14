#!/usr/bin/env python3
"""
LangExtract 敏感数据扫描器
使用 Google LangExtract 进行精确的敏感信息提取和可视化
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

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
                 model_id: str = "Qwen/QwQ-32B", 
                 api_key: Optional[str] = None,
                 base_url: str = "https://api.siliconflow.cn/v1",
                 enable_visualization: bool = False):
        """
        初始化扫描器（专用于SiliconFlow）
        
        Args:
            model_id: 模型ID
            api_key: API密钥，如果为None则从环境变量读取
            base_url: API地址，默认为SiliconFlow
            enable_visualization: 是否启用原生可视化（会保存原文）
        """
        self.model_id = model_id
        self.base_url = base_url
        self.enable_visualization = enable_visualization
        
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
            text="默认管理员账号：admin，密码：Admin@123，请及时修改。",
            extractions=[
                lx.data.Extraction(
                    extraction_class="用户名密码",
                    extraction_text="admin，密码：Admin@123"
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
    
    def scan_text(self, text: str, document_name: str = "document") -> Dict[str, Any]:
        """
        扫描文本中的敏感信息
        
        Args:
            text: 要扫描的文本
            document_name: 文档名称
            
        Returns:
            包含扫描结果的字典
        """
        try:
            # 创建提示词
            prompt = """提取文本中的敏感信息，包括：身份证号、护照号、手机号、邮箱、银行卡号、用户名密码、API密钥、内网IP、社保号、车牌号等。
同时生成一句话的文档摘要（限50字）。
注意：单独用户名不算敏感，需要上下文判断。"""
            
            # 执行提取
            logger.info(f"开始扫描文档: {document_name}")
            
            # 创建文档对象
            doc = lx.data.Document(
                text=text,
                document_id=document_name
            )
            
            # 创建SiliconFlow兼容的OpenAI模型（不使用response_format）
            from langextract.providers.openai import OpenAILanguageModel
            from langextract.core import data
            
            class SiliconFlowModel(OpenAILanguageModel):
                """SiliconFlow模型，不使用response_format"""
                
                @property
                def requires_fence_output(self) -> bool:
                    """强制使用fence输出"""
                    return True
                
                def _process_single_prompt(self, prompt: str, config: dict):
                    """重写以移除response_format"""
                    from langextract.core import types as core_types
                    
                    try:
                        normalized_config = self._normalize_reasoning_params(config)
                        
                        system_message = ''
                        if self.format_type == data.FormatType.JSON:
                            system_message = (
                                'You are a helpful assistant that responds in JSON format. '
                                'Wrap your JSON response in ```json ... ``` code blocks.'
                            )
                        elif self.format_type == data.FormatType.YAML:
                            system_message = (
                                'You are a helpful assistant that responds in YAML format.'
                            )
                        
                        messages = [{'role': 'user', 'content': prompt}]
                        if system_message:
                            messages.insert(0, {'role': 'system', 'content': system_message})
                        
                        api_params = {
                            'model': self.model_id,
                            'messages': messages,
                            'n': 1,
                        }
                        
                        temp = normalized_config.get('temperature', self.temperature)
                        if temp is not None:
                            api_params['temperature'] = temp
                        
                        # 跳过 response_format，SiliconFlow不支持
                        
                        if (v := normalized_config.get('max_output_tokens')) is not None:
                            api_params['max_tokens'] = v
                        if (v := normalized_config.get('top_p')) is not None:
                            api_params['top_p'] = v
                        
                        # 复制其他参数处理逻辑
                        for key in [
                            'frequency_penalty',
                            'presence_penalty', 
                            'seed',
                            'stop',
                            'logprobs',
                            'top_logprobs',
                            'reasoning'
                        ]:
                            if (v := normalized_config.get(key)) is not None:
                                api_params[key] = v
                        
                        # 调用API
                        response = self._client.chat.completions.create(**api_params)
                        
                        return core_types.ScoredOutput(
                            output=response.choices[0].message.content,
                            score=1.0
                        )
                        
                    except Exception as e:
                        raise Exception(f"API error: {e}") from e
            
            # 创建模型实例
            model = SiliconFlowModel(
                model_id=self.model_id,
                api_key=self.api_key,
                base_url=self.base_url,
                temperature=0.1,
                format_type=data.FormatType.JSON
            )
            
            # 准备提取参数
            extract_kwargs = {
                "text_or_documents": [doc],
                "prompt_description": prompt,
                "examples": self.sensitive_types,
                "max_workers": 4,  # 并行处理
                "extraction_passes": 1,  # 单轮提取，提高速度
                "model": model
            }
            
            # 执行提取
            result = lx.extract(**extract_kwargs)
            
            # 处理结果 - 当传入文档列表时，result 是一个可迭代对象
            if result:
                # 将迭代器转换为列表并获取第一个
                try:
                    result_list = list(result)
                    if result_list and hasattr(result_list[0], 'extractions'):
                        extractions = result_list[0].extractions
                    else:
                        extractions = []
                except Exception as e:
                    logger.error(f"处理提取结果时出错: {e}")
                    raise
            else:
                extractions = []
            
            # 统计各类型敏感信息
            sensitive_stats = {}
            sensitive_items = []
            document_summary = None  # 文档摘要
            
            for extraction in extractions:
                # 如果是文档摘要，单独处理
                if extraction.extraction_class == "文档摘要":
                    document_summary = extraction.extraction_text
                    continue
                
                # 统计敏感信息
                if extraction.extraction_class not in sensitive_stats:
                    sensitive_stats[extraction.extraction_class] = 0
                sensitive_stats[extraction.extraction_class] += 1
                
                # 获取位置信息（如果有）
                start_pos = None
                end_pos = None
                if hasattr(extraction, 'char_interval') and extraction.char_interval:
                    interval = extraction.char_interval
                    # 尝试不同的属性名
                    for start_attr, end_attr in [('start', 'end'), ('start_pos', 'end_pos'), ('start_index', 'end_index')]:
                        if hasattr(interval, start_attr):
                            start_pos = getattr(interval, start_attr)
                            end_pos = getattr(interval, end_attr)
                            break
                
                # 获取上下文
                context = ""
                if start_pos is not None and end_pos is not None:
                    context_start = max(0, start_pos - 20)
                    context_end = min(len(text), end_pos + 20)
                    context = text[context_start:context_end]
                else:
                    # 如果没有位置信息，尝试在文本中查找
                    idx = text.find(extraction.extraction_text)
                    if idx >= 0:
                        start_pos = idx
                        end_pos = idx + len(extraction.extraction_text)
                        context_start = max(0, start_pos - 20)
                        context_end = min(len(text), end_pos + 20)
                        context = text[context_start:context_end]
                
                sensitive_items.append({
                    "type": extraction.extraction_class,
                    "value": extraction.extraction_text,  # 直接使用原始值，不脱敏
                    "original_length": len(extraction.extraction_text),
                    "position": {
                        "start": start_pos,
                        "end": end_pos
                    } if start_pos is not None else None,
                    "context": context,
                    "confidence": getattr(extraction, 'confidence', 1.0)
                })
            
            # 构建返回结果
            # 注意：sensitive_count 不包括文档摘要
            sensitive_count = len([e for e in extractions if e.extraction_class != "文档摘要"])
            
            result = {
                "success": True,
                "has_sensitive": sensitive_count > 0,
                "sensitive_count": sensitive_count,
                "sensitive_stats": sensitive_stats,
                "sensitive_items": sensitive_items,
                "document_summary": document_summary,  # 添加文档摘要
                "document_name": document_name,
                "document_length": len(text),
                "model_used": self.model_id
            }
            
            # 如果启用了可视化，保存原文和原始值
            if hasattr(self, 'enable_visualization') and self.enable_visualization:
                result['langextract_result'] = {
                    'original_text': text,
                    'sensitive_items': []
                }
                # 保存敏感值用于可视化
                result['langextract_result']['sensitive_items'] = sensitive_items
            
            return result
            
        except Exception as e:
            logger.error(f"扫描失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document_name": document_name
            }
    
    def scan_files(self, file_paths: List[str], output_dir: str = "./scan_results") -> Dict[str, Any]:
        """
        批量扫描文件
        
        Args:
            file_paths: 文件路径列表
            output_dir: 输出目录
            
        Returns:
            批量扫描结果
        """
        os.makedirs(output_dir, exist_ok=True)
        
        all_results = []
        total_sensitive = 0
        
        for file_path in file_paths:
            try:
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 扫描文件
                file_name = Path(file_path).name
                result = self.scan_text(content, file_name)
                
                if result["success"]:
                    total_sensitive += result.get("sensitive_count", 0)
                
                all_results.append(result)
                
            except Exception as e:
                logger.error(f"处理文件 {file_path} 失败: {str(e)}")
                all_results.append({
                    "success": False,
                    "error": str(e),
                    "document_name": Path(file_path).name
                })
        
        # 保存结果
        output_file = os.path.join(output_dir, "scan_summary.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "total_files": len(file_paths),
                "total_sensitive": total_sensitive,
                "results": all_results
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"扫描完成，结果保存在: {output_file}")
        
        return {
            "total_files": len(file_paths),
            "total_sensitive": total_sensitive,
            "output_file": output_file,
            "results": all_results
        }
    
    def generate_visualization(self, scan_results: List[Dict[str, Any]], output_path: str = "scan_visualization.html") -> str:
        """
        生成可视化HTML报告（使用LangExtract原生可视化）
        
        Args:
            scan_results: 扫描结果列表（需要包含langextract_result字段）
            output_path: 输出HTML文件路径
            
        Returns:
            HTML文件路径或None
        """
        if not self.enable_visualization:
            raise ValueError("必须在初始化时设置 enable_visualization=True 才能生成原生可视化")
            
        try:
            # 准备AnnotatedDocument对象列表
            annotated_documents = []
            
            for result in scan_results:
                if not result.get("success") or not result.get("langextract_result"):
                    continue
                    
                # 获取原始的LangExtract结果
                langextract_result = result["langextract_result"]
                
                # 如果有原文，创建AnnotatedDocument
                if "original_text" in langextract_result:
                    # 从原始结果重建extractions
                    extractions = []
                    for item in langextract_result.get("sensitive_items", []):
                        if item.get("position") and item["position"]["start"] is not None:
                            extraction = lx.data.Extraction(
                                extraction_class=item["type"],
                                extraction_text=item["value"],  # 直接使用value字段
                                char_interval=lx.data.CharInterval(
                                    start_pos=item["position"]["start"],
                                    end_pos=item["position"]["end"]
                                )
                            )
                            extractions.append(extraction)
                    
                    # 创建AnnotatedDocument
                    annotated_doc = lx.data.AnnotatedDocument(
                        document_id=result["document_name"],
                        text=langextract_result["original_text"],
                        extractions=extractions
                    )
                    annotated_documents.append(annotated_doc)
            
            if not annotated_documents:
                raise ValueError("没有可视化的数据。请确保扫描结果包含原文（需要 enable_visualization=True）")
            
            # 保存为JSONL
            jsonl_path = output_path.replace('.html', '.jsonl')
            # 分离目录和文件名
            import os
            output_dir = os.path.dirname(jsonl_path)
            output_name = os.path.basename(jsonl_path)
            
            # 确保目录存在
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # 使用正确的参数调用
            lx.io.save_annotated_documents(
                annotated_documents, 
                output_dir=output_dir if output_dir else ".",
                output_name=output_name,
                show_progress=False  # 避免进度条干扰
            )
            
            # 生成LangExtract原生可视化
            # 确保使用完整路径
            full_jsonl_path = os.path.join(output_dir if output_dir else ".", output_name)
            html_content = lx.visualize(
                full_jsonl_path,
                animation_speed=0.5,  # 动画速度
                show_legend=True,     # 显示图例
                gif_optimized=False   # 标准Web显示
            )
            
            # 保存HTML
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"LangExtract可视化报告生成成功: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"生成LangExtract可视化失败: {str(e)}")
            raise
    


# 测试代码
if __name__ == "__main__":
    # 初始化扫描器（使用SiliconFlow）
    scanner = LangExtractSensitiveScanner(
        model_id="Qwen/QwQ-32B",  # 或其他SiliconFlow支持的模型
        api_key="your-api-key",  # 替换为实际的API密钥
        enable_visualization=True  # 如果需要可视化
    )
    
    # 测试文本
    test_text = """
    尊敬的张先生（身份证：110101199001011234），
    
    您的订单已确认，配送信息如下：
    联系电话：13812345678
    收货地址：北京市朝阳区某某街道123号
    
    支付信息：
    银行卡号：6222021234567890123
    
    如有问题请联系客服邮箱：service@example.com
    
    内部备注：
    服务器IP：192.168.1.100
    数据库连接：mysql://root:Admin@123@192.168.1.100:3306/db
    API密钥：sk-1234567890abcdef
    """
    
    # 执行扫描
    result = scanner.scan_text(test_text, "test_document.txt")
    
    # 打印结果
    print("扫描结果:")
    print(f"- 成功: {result['success']}")
    print(f"- 发现敏感信息: {result.get('sensitive_count', 0)}个")
    
    # 生成原生可视化
    if result['success']:
        try:
            viz_path = scanner.generate_visualization([result], "langextract_viz.html")
            print(f"\n✅ 原生可视化生成成功: {viz_path}")
        except Exception as e:
            print(f"\n❌ 生成可视化失败: {e}")