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
        # 确保临时目录存在
        self.temp_dir = os.path.join(tempfile.gettempdir(), 'document_exports')
        os.makedirs(self.temp_dir, exist_ok=True)
        
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
            output_file = os.path.join(self.temp_dir, f"{file_id}.docx")
            
            # 准备pandoc参数
            extra_args = []
            
            # 添加元数据
            if title:
                extra_args.extend(['--metadata', f'title={title}'])
            
            # 添加目录
            extra_args.append('--toc')
            
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
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        清理旧的导出文件
        
        Args:
            max_age_hours: 文件保留的最大小时数
        """
        try:
            import time
            current_time = time.time()
            
            for filename in os.listdir(self.temp_dir):
                file_path = os.path.join(self.temp_dir, filename)
                if os.path.isfile(file_path):
                    file_age_hours = (current_time - os.path.getmtime(file_path)) / 3600
                    if file_age_hours > max_age_hours:
                        os.remove(file_path)
                        logger.info(f"删除过期文件: {filename}")
                        
        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")

# 创建服务实例
document_export_service = DocumentExportService()