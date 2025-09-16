/**
 * 敏感数据扫描任务相关类型定义
 */

// 任务状态
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed';

// 文件状态
export type FileStatus = 'pending' | 'reading' | 'scanning' | 'completed' | 'failed';

// 扫描任务
export interface ScanTask {
  task_id: string;
  status: TaskStatus;
  total_files: number;
  processed_files?: number;
  failed_files?: number;
  create_by: string;
  create_time: string;
  start_time?: string;
  end_time?: string;
  completed_files?: number;
  sensitive_items?: number;
}

// 扫描文件
export interface ScanFile {
  file_id: string;
  file_name?: string;
  status: FileStatus;
  jsonl_path?: string;
  html_path?: string;
  error?: string;
  start_time?: string;
  end_time?: string;
}

// 任务进度
export interface TaskProgress {
  phase: TaskStatus;
  current: number;
  total: number;
  message: string;
}

// 任务详情
export interface TaskDetail {
  task_id: string;
  status: TaskStatus;
  total_files: number;
  processed_files: number;
  failed_files: number;
  progress: TaskProgress;
  statistics: {
    processed_files: number;
    sensitive_items: number;
  };
  file_status_summary: Record<FileStatus, number>;
  errors: string[];
  create_time: string;
  start_time?: string;
  end_time?: string;
}

// 任务结果
export interface TaskResult {
  task_id: string;
  status: TaskStatus;
  summary: {
    total_files: number;
    completed_files: number;
    failed_files: number;
  };
  files: ScanFile[];
  completed_time?: string;
}

// 敏感数据项
export interface SensitiveItem {
  type: string;
  text: string;
  position?: {
    start: number;
    end: number;
  };
}

// 扫描结果
export interface ScanResult {
  document_id: string;
  text: string;
  extractions: SensitiveItem[];
}