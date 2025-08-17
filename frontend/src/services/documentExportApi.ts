import { message } from 'antd';
import { extractAndConvertMermaidDiagrams } from '@/utils/mermaidExtractor';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * 下载文件的通用函数
 */
function downloadFile(blob: Blob, fileName: string): void {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

/**
 * 从响应头中提取文件名
 */
function extractFileName(response: Response, defaultName: string = 'document.docx'): string {
  const contentDisposition = response.headers.get('content-disposition');
  if (contentDisposition) {
    const fileNameMatch = contentDisposition.match(/filename="(.+)"/);
    if (fileNameMatch) {
      return fileNameMatch[1];
    }
  }
  return defaultName;
}

/**
 * 导出内容为Word文档的核心函数
 */
async function exportToWordCore(
  content: string,
  title?: string,
  mermaidImages?: Array<{ index: number; image_data: string }>
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/agents/export/word`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
    },
    body: JSON.stringify({
      content,
      title,
      format: 'markdown',
      mermaid_images: mermaidImages,
    }),
  });

  if (!response.ok) {
    throw new Error(`导出失败: ${response.statusText}`);
  }

  const blob = await response.blob();
  const fileName = extractFileName(response);
  downloadFile(blob, fileName);
}

/**
 * 导出内容为Word文档（支持Mermaid图表）
 * @param content Markdown内容
 * @param title 文档标题
 * @param isDark 是否为暗色主题
 */
export const exportToWordWithImages = async (
  content: string, 
  title?: string,
  isDark: boolean = false
): Promise<void> => {
  try {
    // 提取并转换Mermaid图表
    const { images } = await extractAndConvertMermaidDiagrams(content, isDark);
    
    // 准备图片数据
    const mermaidImages = images.map((img, index) => ({
      index,
      image_data: img.imageData,
    }));
    
    await exportToWordCore(content, title, mermaidImages);
    message.success('文档导出成功');
  } catch (error) {
    console.error('导出Word文档失败:', error);
    message.error(`导出失败: ${error instanceof Error ? error.message : '未知错误'}`);
    throw error;
  }
};

/**
 * 导出内容为Word文档（不处理Mermaid图表）
 * @param content Markdown内容
 * @param title 文档标题
 * @deprecated 建议使用 exportToWordWithImages
 */
export const exportToWord = async (content: string, title?: string): Promise<void> => {
  try {
    await exportToWordCore(content, title);
    message.success('文档导出成功');
  } catch (error) {
    console.error('导出Word文档失败:', error);
    message.error(`导出失败: ${error instanceof Error ? error.message : '未知错误'}`);
    throw error;
  }
};