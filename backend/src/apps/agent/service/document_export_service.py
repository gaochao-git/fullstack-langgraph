"""
文档导出服务
"""
import os
import tempfile
import uuid
from typing import Optional
import pypandoc
from src.shared.core.logging import get_logger
from src.shared.core.config import settings

logger = get_logger(__name__)
# settings已经从config模块导入

class DocumentExportService:
    """文档导出服务"""
    
    def __init__(self):
        # 文档基础目录
        self.doc_dir = settings.DOCUMENT_DIR
        
        # 模板目录
        self.template_dir = os.path.join(self.doc_dir, 'templates')
        
        # 生成文档目录
        self.generated_dir = os.path.join(self.doc_dir, 'generated')
        os.makedirs(self.generated_dir, exist_ok=True)
        
        # 检查pandoc是否安装
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
    
    async def export_to_word(
        self, 
        content: str, 
        title: Optional[str] = None,
        format: str = 'markdown'
    ) -> str:
        """
        将内容导出为Word文档
        
        Args:
            content: 要导出的内容
            title: 文档标题
            format: 内容格式 (markdown/html/plain)
            
        Returns:
            生成的文档路径
        """
        try:
            # 生成唯一的文件名
            file_id = str(uuid.uuid4())
            output_file = os.path.join(self.generated_dir, f"{file_id}.docx")
            
            # 准备pandoc参数
            extra_args = []
            
            # 添加元数据
            if title:
                extra_args.extend(['--metadata', f'title={title}'])
            
            # 不生成目录
            # 如果需要目录功能，可以取消下面的注释
            # extra_args.append('--toc')
            
            # 使用公文写作规范模板
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
                else:
                    logger.info("未找到模板文件，使用pandoc默认格式")
            
            # 执行转换
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
    

# 创建服务实例
document_export_service = DocumentExportService()