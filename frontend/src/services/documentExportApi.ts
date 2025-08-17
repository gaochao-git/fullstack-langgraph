import { message } from 'antd';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * 导出内容为Word文档
 */
export const exportToWord = async (content: string, title?: string): Promise<void> => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/v1/agents/export/word`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      },
      body: JSON.stringify({
        content,
        title,
        format: 'markdown'
      }),
    });

    if (!response.ok) {
      throw new Error(`导出失败: ${response.statusText}`);
    }

    // 获取文件名
    const contentDisposition = response.headers.get('content-disposition');
    let fileName = 'document.docx';
    if (contentDisposition) {
      const fileNameMatch = contentDisposition.match(/filename="(.+)"/);
      if (fileNameMatch) {
        fileName = fileNameMatch[1];
      }
    }

    // 下载文件
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    message.success('文档导出成功');
  } catch (error) {
    console.error('导出Word文档失败:', error);
    message.error(`导出失败: ${error.message || '未知错误'}`);
    throw error;
  }
};