import React, { useRef, useEffect, useState } from 'react';
import { Paperclip, X, Eye, Image, FileText, FileSpreadsheet } from 'lucide-react';
import { cn } from '@/utils/lib-utils';
import { configService, UploadConfig } from '@/services/configApi';
import { FilePreviewModal } from './FilePreviewModal';

interface FileUploadManagerProps {
  selectedFiles: File[];
  onFilesSelect: (files: File[]) => void;
  onFileRemove: (index: number) => void;
  onError?: (message: string) => void;
  isDark: boolean;
  disabled?: boolean;
}

export const FileUploadManager: React.FC<FileUploadManagerProps> = ({
  selectedFiles,
  onFilesSelect,
  onFileRemove,
  onError,
  isDark,
  disabled = false
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadConfig, setUploadConfig] = useState<UploadConfig | null>(null);
  
  useEffect(() => {
    // 获取上传配置
    configService.getUploadConfig().then(config => {
      setUploadConfig(config);
    }).catch(err => {
      console.error('获取上传配置失败:', err);
      // 使用默认配置
      setUploadConfig({
        max_upload_size_mb: 10,
        allowed_extensions: ['.pdf', '.docx', '.txt', '.md', '.xlsx']
      });
    });
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0 && uploadConfig) {
      // 前端预检查文件大小
      const MAX_SIZE = uploadConfig.max_upload_size_mb * 1024 * 1024;
      const oversizedFiles: string[] = [];
      const validFiles = files.filter(file => {
        if (file.size > MAX_SIZE) {
          oversizedFiles.push(`${file.name} (${(file.size / 1024 / 1024).toFixed(2)}MB)`);
          return false;
        }
        return true;
      });
      
      if (validFiles.length > 0) {
        onFilesSelect(validFiles);
      }
      
      if (oversizedFiles.length > 0) {
        const errorMsg = `以下文件超过 ${uploadConfig.max_upload_size_mb}MB 限制：${oversizedFiles.join(', ')}`;
        onError?.(errorMsg);
      }
      
      // 清空 input 的值，以便可以再次选择相同的文件
      e.target.value = '';
    }
  };

  return (
    <>
      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        onChange={handleFileSelect}
        className="hidden"
        accept={uploadConfig?.allowed_extensions.join(',') || '.pdf,.docx,.txt,.md,.xlsx'}
        disabled={disabled}
      />
      
      {/* 上传按钮 */}
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
        className={cn(
          "p-2 rounded transition-colors duration-200",
          disabled
            ? "cursor-not-allowed opacity-50"
            : isDark
              ? "text-gray-400 hover:text-gray-200 hover:bg-gray-700"
              : "text-gray-500 hover:text-gray-700 hover:bg-gray-100"
        )}
        title={uploadConfig ? `上传文件（最大 ${uploadConfig.max_upload_size_mb}MB）` : '上传文件'}
      >
        <Paperclip className="h-4 w-4" />
      </button>
    </>
  );
};

interface FileListDisplayProps {
  files: Array<{ 
    file: File; 
    fileId: string; 
    status: 'uploading' | 'processing' | 'success' | 'failed'; 
    progress?: number;
    processingMessage?: string;
  }>;
  onRemove: (index: number) => void;
  isDark: boolean;
}

export const FileListDisplay: React.FC<FileListDisplayProps> = ({
  files,
  onRemove,
  isDark
}) => {
  const [previewFile, setPreviewFile] = useState<{fileId: string; fileName: string; fileType: string} | null>(null);
  
  if (files.length === 0) return null;
  

  return (
    <>
      <div className={cn(
        "px-4 py-2 border-b",
        isDark ? "border-gray-700" : "border-gray-200"
      )}>
        <div className="flex flex-wrap gap-2">
          {files.map((item, index) => (
            <div
              key={index}
              className={cn(
                "flex items-center gap-2 px-3 py-1 rounded-full text-sm",
                item.status === 'uploading' 
                  ? (isDark ? "bg-blue-900 text-blue-200" : "bg-blue-100 text-blue-700")
                  : item.status === 'processing'
                    ? (isDark ? "bg-yellow-900 text-yellow-200" : "bg-yellow-100 text-yellow-700")
                  : item.status === 'success'
                    ? (isDark ? "bg-green-900 text-green-200" : "bg-green-100 text-green-700")
                    : (isDark ? "bg-red-900 text-red-200" : "bg-red-100 text-red-700")
              )}
            >
              {item.status === 'uploading' ? (
                <div className="flex items-center gap-1">
                  <div className="w-16 h-1.5 bg-gray-300 dark:bg-gray-600 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-blue-500 transition-all duration-300"
                      style={{ width: `${item.progress || 0}%` }}
                    />
                  </div>
                  <span className="text-xs opacity-70">{item.progress || 0}%</span>
                </div>
              ) : item.status === 'processing' ? (
                <div className="flex items-center gap-1">
                  <div className="animate-spin h-3 w-3 border-2 border-yellow-500 border-t-transparent rounded-full" />
                  <span className="text-xs">解析中...</span>
                </div>
              ) : item.status === 'success' ? (
                isImageFile(item.file.name) ? (
                  <Image className="h-3 w-3" />
                ) : isExcelFile(item.file.name) ? (
                  <FileSpreadsheet className="h-3 w-3" />
                ) : (
                  <FileText className="h-3 w-3" />
                )
              ) : (
                <X className="h-3 w-3" />
              )}
              <span className="flex items-center gap-1">
                <span 
                  className="max-w-[200px] truncate" 
                  title={item.status === 'processing' ? `正在解析: ${item.file.name}` : item.file.name}
                >
                  {item.file.name}
                </span>
                <span className="text-xs opacity-70">
                  ({formatFileSize(item.file.size)})
                </span>
              </span>
              <div className="flex items-center gap-1">
                {item.status === 'success' && isFilePreviewable(item.file.name) && (
                  <button
                    type="button"
                    onClick={() => setPreviewFile({
                      fileId: item.fileId,
                      fileName: item.file.name,
                      fileType: '.' + getFileExtension(item.file.name)
                    })}
                    className={cn(
                      "hover:opacity-80 transition-opacity",
                      isDark ? "text-gray-400 hover:text-gray-200" : "text-gray-500 hover:text-gray-700"
                    )}
                    title="预览"
                  >
                    <Eye className="h-3 w-3" />
                  </button>
                )}
                {item.status !== 'uploading' && (
                  <button
                    type="button"
                    onClick={() => onRemove(index)}
                    className={cn(
                      "hover:text-red-500 transition-colors",
                      isDark ? "text-gray-400" : "text-gray-500"
                    )}
                    title="删除"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {previewFile && (
        <FilePreviewModal
          visible={!!previewFile}
          fileId={previewFile.fileId}
          fileName={previewFile.fileName}
          fileType={previewFile.fileType}
          onClose={() => setPreviewFile(null)}
        />
      )}
    </>
  );
};

// 文件类型常量定义
const FILE_EXTENSIONS = {
  TEXT: ['txt', 'md'],
  IMAGE: ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg'],
  DOCUMENT: ['pdf', 'docx', 'doc'],
  SPREADSHEET: ['xlsx', 'xls'],
} as const;

// 可预览的文件扩展名
const PREVIEWABLE_EXTENSIONS = [
  ...FILE_EXTENSIONS.TEXT,
  ...FILE_EXTENSIONS.IMAGE,
  'pdf', // 添加PDF支持
];

// 获取文件扩展名的辅助函数（统一使用这一个）
function getFileExtension(filename: string): string {
  const lastDot = filename.lastIndexOf('.');
  return lastDot > -1 ? filename.substring(lastDot + 1).toLowerCase() : '';
}

// 格式化文件大小（统一使用这一个）
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 判断是否是图片文件
function isImageFile(filename: string): boolean {
  const ext = getFileExtension(filename);
  return FILE_EXTENSIONS.IMAGE.includes(ext as any);
}

// 判断是否是Excel文件
function isExcelFile(filename: string): boolean {
  const ext = getFileExtension(filename);
  return FILE_EXTENSIONS.SPREADSHEET.includes(ext as any);
}

// 判断文件是否可预览
function isFilePreviewable(filename: string): boolean {
  const ext = getFileExtension(filename);
  return PREVIEWABLE_EXTENSIONS.includes(ext as any);
}

// 文件上传相关的工具函数（导出供其他组件使用）
export const fileUploadUtils = {
  formatFileSize,
  getFileExtension,
  isImageFile,
  isExcelFile,
  isFilePreviewable,
  
  // 验证文件类型
  isValidFileType: (file: File): boolean => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain',
      'text/markdown',
      'image/png',
      'image/jpeg',
      'image/jpg',
      'image/gif',
      'image/bmp',
      'image/webp',
      'image/svg+xml'
    ];
    const ext = getFileExtension(file.name);
    const allExtensions = Object.values(FILE_EXTENSIONS).flat();
    
    return validTypes.includes(file.type) || allExtensions.includes(ext as any);
  },

  // 验证文件大小（默认最大 10MB）
  isValidFileSize: (file: File, maxSizeInMB: number = 10): boolean => {
    return file.size <= maxSizeInMB * 1024 * 1024;
  }
};