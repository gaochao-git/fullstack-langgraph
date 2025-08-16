import React, { useRef, useEffect, useState } from 'react';
import { Paperclip, X, Eye } from 'lucide-react';
import { cn } from '@/utils/lib-utils';
import { configService, UploadConfig } from '@/services/configApi';
import { FilePreviewModal } from './FilePreviewModal';

interface FileUploadManagerProps {
  selectedFiles: File[];
  onFilesSelect: (files: File[]) => void;
  onFileRemove: (index: number) => void;
  isDark: boolean;
  disabled?: boolean;
}

export const FileUploadManager: React.FC<FileUploadManagerProps> = ({
  selectedFiles,
  onFilesSelect,
  onFileRemove,
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
        allowed_extensions: ['.pdf', '.docx', '.txt', '.md']
      });
    });
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length > 0 && uploadConfig) {
      // 前端预检查文件大小
      const MAX_SIZE = uploadConfig.max_upload_size_mb * 1024 * 1024;
      const validFiles = files.filter(file => {
        if (file.size > MAX_SIZE) {
          console.warn(`文件 ${file.name} 超过 ${uploadConfig.max_upload_size_mb}MB 限制，大小为 ${(file.size / 1024 / 1024).toFixed(2)}MB`);
          // TODO: 可以通过props传递错误处理回调
          return false;
        }
        return true;
      });
      
      if (validFiles.length > 0) {
        onFilesSelect(validFiles);
      }
      
      if (validFiles.length < files.length) {
        // 有文件被过滤，可以显示提示
        const filtered = files.length - validFiles.length;
        console.error(`${filtered} 个文件因超过大小限制被过滤`);
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
        accept={uploadConfig?.allowed_extensions.join(',') || '.pdf,.docx,.txt,.md'}
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
  files: Array<{ file: File; fileId: string; status: 'uploading' | 'success' | 'failed' }>;
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
  
  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };
  
  // 获取文件扩展名
  const getFileExtension = (fileName: string): string => {
    const lastDot = fileName.lastIndexOf('.');
    return lastDot > -1 ? fileName.substring(lastDot) : '';
  };
  
  // 判断是否可预览
  const isPreviewable = (fileName: string): boolean => {
    const ext = getFileExtension(fileName).toLowerCase();
    return ['.txt', '.md'].includes(ext);
  };

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
                  : item.status === 'success'
                    ? (isDark ? "bg-green-900 text-green-200" : "bg-green-100 text-green-700")
                    : (isDark ? "bg-red-900 text-red-200" : "bg-red-100 text-red-700")
              )}
            >
              {item.status === 'uploading' ? (
                <div className="animate-spin h-3 w-3 border-2 border-current border-t-transparent rounded-full" />
              ) : item.status === 'success' ? (
                <Paperclip className="h-3 w-3" />
              ) : (
                <X className="h-3 w-3" />
              )}
              <span className="flex items-center gap-1">
                <span className="max-w-[200px] truncate" title={item.file.name}>
                  {item.file.name}
                </span>
                <span className="text-xs opacity-70">
                  ({formatFileSize(item.file.size)})
                </span>
              </span>
              <div className="flex items-center gap-1">
                {item.status === 'success' && isPreviewable(item.file.name) && (
                  <button
                    type="button"
                    onClick={() => setPreviewFile({
                      fileId: item.fileId,
                      fileName: item.file.name,
                      fileType: getFileExtension(item.file.name)
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

// 文件上传相关的工具函数
export const fileUploadUtils = {
  // 格式化文件大小
  formatFileSize: (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  },

  // 获取文件扩展名
  getFileExtension: (filename: string): string => {
    return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2);
  },

  // 验证文件类型
  isValidFileType: (file: File): boolean => {
    const validTypes = [
      'application/pdf',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'text/plain',
      'text/markdown'
    ];
    return validTypes.includes(file.type) || 
           ['pdf', 'docx', 'txt', 'md']
             .includes(getFileExtension(file.name).toLowerCase());
  },

  // 验证文件大小（默认最大 10MB）
  isValidFileSize: (file: File, maxSizeInMB: number = 10): boolean => {
    return file.size <= maxSizeInMB * 1024 * 1024;
  }
};

// 获取文件扩展名的辅助函数
function getFileExtension(filename: string): string {
  return filename.slice((filename.lastIndexOf(".") - 1 >>> 0) + 2);
}