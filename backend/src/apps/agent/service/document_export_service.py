"""
文档导出服务
支持将Markdown内容导出为Word文档，包括Mermaid图表的处理
"""
import os
import tempfile
import uuid
import re
import base64
import shutil
from typing import Optional, List, Dict
import pypandoc
from src.shared.core.logging import get_logger
from src.shared.core.config import settings

logger = get_logger(__name__)


class DocumentExportService:
    """文档导出服务"""
    
    def __init__(self):
        # 文档基础目录
        self.doc_dir = settings.DOCUMENT_DIR
        
        # 确保所有子目录存在
        self.upload_dir = os.path.join(self.doc_dir, 'uploads')
        self.template_dir = os.path.join(self.doc_dir, 'templates')
        self.generated_dir = os.path.join(self.doc_dir, 'generated')
        
        # 创建必要的目录
        for directory in [self.upload_dir, self.template_dir, self.generated_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # 检查Pandoc安装
        self._setup_pandoc()
    
    def _setup_pandoc(self):
        """检查并设置Pandoc"""
        try:
            pypandoc.get_pandoc_version()
            logger.info("Pandoc已安装")
        except:
            logger.warning("Pandoc未安装，尝试下载...")
            try:
                pypandoc.download_pandoc()
                logger.info("Pandoc下载成功")
            except Exception as e:
                logger.error(f"Pandoc下载失败: {e}")
                raise RuntimeError("Pandoc未安装且下载失败，请手动安装: https://pandoc.org/installing.html")
    
    def _use_frontend_mermaid_images(self, content: str, mermaid_images: List[Dict]) -> tuple[str, Optional[str]]:
        """
        使用前端提供的Mermaid图片
        
        Args:
            content: Markdown内容
            mermaid_images: 前端提供的图片列表，每个包含 index 和 image_data
            
        Returns:
            (处理后的内容, 临时目录路径)
        """
        if not mermaid_images:
            return content, None
            
        # 创建临时目录
        temp_dir = tempfile.mkdtemp()
        processed_content = content
        
        try:
            # 保存前端提供的图片
            image_files = []
            for img_data in mermaid_images:
                # 处理MermaidImage对象或字典
                if hasattr(img_data, 'index'):
                    # Pydantic模型对象
                    index = img_data.index
                    base64_data = img_data.image_data
                else:
                    # 字典格式（向后兼容）
                    index = img_data.get('index', 0)
                    base64_data = img_data.get('image_data', '')
                
                if base64_data:
                    # 解码base64图片
                    image_bytes = base64.b64decode(base64_data)
                    
                    # 保存图片文件
                    image_path = os.path.join(temp_dir, f"mermaid_{index}.png")
                    with open(image_path, 'wb') as f:
                        f.write(image_bytes)
                    
                    image_files.append((index, f"mermaid_{index}.png"))
                    logger.info(f"保存前端提供的Mermaid图片 {index}: {image_path}")
            
            # 查找并替换Mermaid代码块
            pattern = r'```\s*mermaid\s*\n([\s\S]*?)```'
            matches = list(re.finditer(pattern, content, re.IGNORECASE))
            
            # 从后往前替换，避免位置偏移
            for i in range(len(matches)-1, -1, -1):
                match = matches[i]
                if i < len(image_files):
                    # 替换为图片引用，使用Pandoc的图片属性语法来控制显示大小
                    _, image_filename = image_files[i]
                    # 使用 Pandoc 的属性语法限制图片宽度为50%
                    replacement = f"![Mermaid Diagram {i+1}]({image_filename}){{width=50%}}"
                    
                    processed_content = (
                        processed_content[:match.start()] + 
                        replacement + 
                        processed_content[match.end():]
                    )
                    logger.info(f"替换Mermaid代码块 {i} 为图片引用")
            
            return processed_content, temp_dir
            
        except Exception as e:
            logger.error(f"处理前端Mermaid图片失败: {e}")
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            # 返回原始内容
            return content, None
    
    async def export_to_word(
        self, 
        content: str, 
        title: Optional[str] = None,
        format: str = 'markdown',
        mermaid_images: Optional[List[Dict]] = None
    ) -> str:
        """
        将内容导出为Word文档
        
        Args:
            content: 要导出的内容
            title: 文档标题
            format: 内容格式 (markdown/html/plain)
            mermaid_images: 前端提供的Mermaid图片列表
            
        Returns:
            生成的文档路径
        """
        temp_dir = None
        try:
            # 处理Mermaid图表
            if format == 'markdown' and mermaid_images and len(mermaid_images) > 0:
                logger.info(f"使用前端提供的 {len(mermaid_images)} 个Mermaid图片")
                content, temp_dir = self._use_frontend_mermaid_images(content, mermaid_images)
            
            # 生成唯一的文件名
            file_id = str(uuid.uuid4())
            output_file = os.path.join(self.generated_dir, f"{file_id}.docx")
            
            # 准备pandoc参数
            extra_args = []
            
            # 添加元数据
            if title:
                extra_args.extend(['--metadata', f'title={title}'])
            
            # 使用模板（如果存在）
            template_path = os.path.join(self.template_dir, '公文写作规范模板.docx')
            if os.path.exists(template_path):
                extra_args.extend(['--reference-doc', template_path])
                logger.info(f"使用模板: {template_path}")
            else:
                # 尝试使用默认模板
                default_template_path = os.path.join(self.template_dir, 'template.docx')
                if os.path.exists(default_template_path):
                    extra_args.extend(['--reference-doc', default_template_path])
                    logger.info(f"使用默认模板: {default_template_path}")
            
            # 如果有临时目录（包含图片），需要特殊处理
            if temp_dir and os.path.exists(temp_dir):
                # 创建临时markdown文件
                temp_md_file = os.path.join(temp_dir, 'content.md')
                with open(temp_md_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 添加资源路径参数，让pandoc知道在哪里找图片
                extra_args.extend(['--resource-path', temp_dir])
                
                # 从临时文件转换
                logger.info(f"从临时文件转换: {temp_md_file} -> docx (资源路径: {temp_dir})")
                pypandoc.convert_file(
                    temp_md_file,
                    'docx',
                    outputfile=output_file,
                    extra_args=extra_args
                )
            else:
                # 直接转换文本
                logger.info(f"开始转换: {format} -> docx")
                pypandoc.convert_text(
                    content,
                    'docx',
                    format=format,
                    outputfile=output_file,
                    extra_args=extra_args
                )
            
            logger.info(f"文档生成成功: {output_file}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"导出Word文档失败: {e}")
            raise
        finally:
            # 清理临时目录
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)
                logger.info(f"已清理临时目录: {temp_dir}")


# 创建服务实例
document_export_service = DocumentExportService()