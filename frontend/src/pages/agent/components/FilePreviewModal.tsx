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
  const [imageUrl, setImageUrl] = useState<string>('');
  const [pdfUrl, setPdfUrl] = useState<string>('');

  // 支持预览的文本文件类型
  const isTextPreviewable = ['.txt', '.md'].includes(fileType.toLowerCase());
  
  // 支持预览的表格文件类型
  const isTablePreviewable = ['.csv'].includes(fileType.toLowerCase());
  
  // 支持预览的图片文件类型
  const isImagePreviewable = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg'].includes(fileType.toLowerCase());
  
  // 支持预览的PDF文件类型
  const isPdfPreviewable = ['.pdf'].includes(fileType.toLowerCase());
  
  // 是否支持预览
  const isPreviewable = isTextPreviewable || isTablePreviewable || isImagePreviewable || isPdfPreviewable;

  useEffect(() => {
    if (visible && fileId && isPreviewable) {
      fetchFileContent();
    }
    
    // 清理函数
    return () => {
      if (imageUrl) {
        URL.revokeObjectURL(imageUrl);
        setImageUrl('');
      }
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
        setPdfUrl('');
      }
    };
  }, [visible, fileId]);

  const fetchFileContent = async () => {
    setLoading(true);
    setError('');
    setContent('');
    setImageUrl('');
    setPdfUrl('');
    
    try {
      if (isImagePreviewable) {
        // 获取图片文件
        const blob = await fileApi.downloadDocument(fileId);
        const url = URL.createObjectURL(blob);
        setImageUrl(url);
      } else if (isPdfPreviewable) {
        // 获取PDF文件
        const blob = await fileApi.downloadDocument(fileId);
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);
      } else if (isTextPreviewable || isTablePreviewable) {
        // 获取文本或表格内容
        const docContent = await fileApi.getDocumentContent(fileId);
        setContent(docContent.content || '文件内容为空');
      }
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

  // 渲染CSV表格
  const renderCsvTable = (csvContent: string) => {
    try {
      // 解析CSV内容
      const lines = csvContent.split('\n').filter(line => line.trim());
      const rows: string[][] = [];
      let isHeader = true;
      let headerIndex = -1;

      // 查找表头标记
      lines.forEach((line, index) => {
        if (line.includes('[表头]')) {
          headerIndex = index + 1;
          return;
        }
        if (line.includes('[CSV文件]') || line.includes('编码:') || line.includes('行数:') || line === '') {
          return;
        }
        
        // 解析CSV行
        const cells = line.split('|').map(cell => cell.trim());
        if (cells.length > 1) {
          rows.push(cells);
        }
      });

      if (rows.length === 0) {
        return <div className="text-center text-gray-500 py-8">CSV文件为空</div>;
      }

      // 渲染表格
      return (
        <table className={cn(
          "min-w-full border-collapse",
          isDark ? "bg-gray-800" : "bg-white"
        )}>
          <thead>
            {rows[0] && (
              <tr className={cn(
                "border-b",
                isDark ? "border-gray-700" : "border-gray-200"
              )}>
                {rows[0].map((cell, index) => (
                  <th 
                    key={index}
                    className={cn(
                      "px-4 py-2 text-left font-medium",
                      isDark ? "text-gray-200 bg-gray-900" : "text-gray-900 bg-gray-50"
                    )}
                  >
                    {cell}
                  </th>
                ))}
              </tr>
            )}
          </thead>
          <tbody>
            {rows.slice(1).map((row, rowIndex) => (
              <tr 
                key={rowIndex}
                className={cn(
                  "border-b",
                  isDark ? "border-gray-700 hover:bg-gray-700" : "border-gray-200 hover:bg-gray-50"
                )}
              >
                {row.map((cell, cellIndex) => (
                  <td 
                    key={cellIndex}
                    className={cn(
                      "px-4 py-2",
                      isDark ? "text-gray-300" : "text-gray-700"
                    )}
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      );
    } catch (error) {
      console.error('CSV解析错误:', error);
      return <pre className="whitespace-pre-wrap">{csvContent}</pre>;
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
            <p className="text-sm mt-2">支持预览的格式：文本(.txt, .md, .csv) 图片(.png, .jpg, .jpeg, .gif, .bmp, .webp) PDF(.pdf)</p>
          </div>
        ) : isImagePreviewable && imageUrl ? (
          <div className="flex items-center justify-center">
            <img 
              src={imageUrl} 
              alt={fileName}
              className={cn(
                "max-w-full max-h-[600px] object-contain rounded-lg",
                isDark ? "bg-gray-900" : "bg-white"
              )}
              onError={() => {
                setError('图片加载失败');
                setImageUrl('');
              }}
            />
          </div>
        ) : isPdfPreviewable && pdfUrl ? (
          <div className="w-full h-[600px]">
            <iframe
              src={pdfUrl}
              className="w-full h-full border-0 rounded-lg"
              title={`PDF Preview: ${fileName}`}
            />
          </div>
        ) : isTablePreviewable ? (
          <div className={cn(
            "overflow-auto",
            isDark ? "text-gray-100" : "text-gray-800"
          )}>
            {renderCsvTable(content)}
          </div>
        ) : isTextPreviewable ? (
          <pre className={cn(
            "whitespace-pre-wrap break-words font-mono text-sm",
            isDark ? "text-gray-100" : "text-gray-800"
          )}>
            {content}
          </pre>
        ) : null}
      </div>
    </Modal>
  );
};