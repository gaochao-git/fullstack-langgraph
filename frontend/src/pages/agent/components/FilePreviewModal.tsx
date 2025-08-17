import React, { useState, useEffect } from 'react';
import { Modal, Spin, Button, message } from 'antd';
import { FileText, Download, X } from 'lucide-react';
import { fileApi } from '@/services/fileApi';
import { useTheme } from '@/hooks/ThemeContext';
import { cn } from '@/utils/lib-utils';

interface FilePreviewModalProps {
  visible: boolean;
  fileId: string;
  fileName: string;
  fileType: string;
  onClose: () => void;
}

export const FilePreviewModal: React.FC<FilePreviewModalProps> = ({
  visible,
  fileId,
  fileName,
  fileType,
  onClose
}) => {
  const { isDark } = useTheme();
  const [loading, setLoading] = useState(false);
  const [content, setContent] = useState<string>('');
  const [error, setError] = useState<string>('');

  // 支持预览的文件类型
  const isPreviewable = ['.txt', '.md'].includes(fileType.toLowerCase());

  useEffect(() => {
    if (visible && fileId && isPreviewable) {
      fetchFileContent();
    }
  }, [visible, fileId]);

  const fetchFileContent = async () => {
    setLoading(true);
    setError('');
    try {
      const docContent = await fileApi.getDocumentContent(fileId);
      setContent(docContent.content || '文件内容为空');
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '获取文件内容失败';
      setError(errorMsg);
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await fileApi.downloadDocument(fileId);
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success('文件下载成功');
    } catch (error) {
      message.error('文件下载失败');
      console.error('下载失败:', error);
    }
  };

  return (
    <Modal
      title={
        <div className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          <span className="font-medium">{fileName}</span>
        </div>
      }
      open={visible}
      onCancel={onClose}
      width={800}
      footer={[
        <Button key="download" icon={<Download className="h-4 w-4" />} onClick={handleDownload}>
          下载文件
        </Button>,
        <Button key="close" onClick={onClose}>
          关闭
        </Button>
      ]}
      className={isDark ? 'dark-modal' : ''}
    >
      <div className={cn(
        "min-h-[400px] max-h-[600px] overflow-auto rounded-lg p-4",
        isDark ? "bg-gray-800 text-gray-100" : "bg-gray-50 text-gray-900"
      )}>
        {loading ? (
          <div className="flex items-center justify-center h-[400px]">
            <Spin size="large" tip="加载中..." />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-[400px] text-red-500">
            <X className="h-12 w-12 mb-2" />
            <p>{error}</p>
          </div>
        ) : !isPreviewable ? (
          <div className="flex flex-col items-center justify-center h-[400px] text-gray-500">
            <FileText className="h-12 w-12 mb-2" />
            <p>该文件类型暂不支持预览</p>
            <p className="text-sm mt-2">支持预览的格式：.txt, .md</p>
          </div>
        ) : (
          <pre className={cn(
            "whitespace-pre-wrap break-words font-mono text-sm",
            isDark ? "text-gray-100" : "text-gray-800"
          )}>
            {content}
          </pre>
        )}
      </div>
    </Modal>
  );
};