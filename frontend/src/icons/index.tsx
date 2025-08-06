/**
 * 全局图标定义
 * 只使用 Lucide 图标，保持统一的视觉风格
 */

import React from 'react';
import {
  // 基础
  Home,
  User,
  Users,
  Settings,
  Menu,
  AppWindow,
  Grid3x3,
  
  // 数据与文件
  Database,
  FileText,
  File,
  FolderOpen,
  Book,
  BookOpen,
  Library,
  Bookmark,
  Upload,
  Share,
  Link,
  Copy,
  Folder,
  FolderPlus,
  RefreshCw,
  
  // 智能体与AI
  Bot,
  Brain,
  Sparkles,
  Cpu,
  Monitor,
  MessageSquare,
  Zap,
  Crown,
  
  // 安全与权限
  Shield,
  Lock,
  Key,
  Target,
  UserCheck,
  ShieldCheck,
  
  // 时间
  Clock,
  Calendar,
  Timer,
  
  // 状态
  CheckCircle,
  AlertCircle,
  Info,
  HelpCircle,
  
  // 其他
  Globe,
  Headphones,
  List,
  LayoutGrid,
  Briefcase,
  Package,
  
  // 操作图标
  Plus,
  Edit,
  Trash2,
  Trash,
  Eye,
  EyeOff,
  GripVertical,
} from 'lucide-react';

// 导出所有图标，使用时可以直接 Icons.Bot
export const Icons = {
  // 基础
  Home,
  User,
  Users,
  Settings,
  Setting: Settings,  // 别名兼容
  Menu,
  Appstore: Grid3x3,  // 用 Grid3x3 替代 AppstoreOutlined
  AppWindow,
  
  // 数据与文件
  Database,
  FileText,
  File,
  FolderOpen,
  Book,
  BookOpen,
  Library,
  Bookmark,
  Upload,
  Share,
  Link,
  Copy,
  Folder,
  FolderPlus,
  RefreshCw,
  
  // 智能体与AI
  Bot,
  Brain,
  Sparkles,
  Cpu,
  Monitor,
  MessageSquare,
  Zap,
  Crown,
  Robot: Bot,  // 别名兼容
  
  // 安全与权限
  Shield,
  Lock,
  Key,
  Target,
  UserCheck,
  ShieldCheck,
  Safety: ShieldCheck,  // 别名兼容
  
  // 时间
  Clock,
  ClockCircle: Clock,  // 别名兼容
  Calendar,
  Timer,
  
  // 状态
  CheckCircle,
  AlertCircle,
  Info,
  HelpCircle,
  
  // 其他
  Globe,
  Headphones,
  List,
  UnorderedList: List,  // 别名兼容
  LayoutGrid,
  Team: Users,  // 别名兼容
  Briefcase,
  Package,
  Api: Package,  // 用 Package 替代 ApiOutlined
  
  // 操作图标
  Plus,
  Edit,
  Trash2,
  Trash,
  Eye,
  EyeOff,
  GripVertical,
} as const;

// 图标类型
export type IconName = keyof typeof Icons;

// 图标分类（可选，用于图标选择器）
export const IconCategories = {
  基础: ['Home', 'User', 'Setting', 'Menu'],
  智能体: ['Bot', 'Brain', 'Robot', 'Sparkles', 'Cpu'],
  数据: ['Database', 'Api', 'Book', 'FileText'],
  状态: ['CheckCircle', 'AlertCircle', 'Info', 'HelpCircle'],
  时间: ['Clock', 'ClockCircle', 'Calendar'],
  其他: ['Globe', 'Shield', 'Zap', 'MessageSquare'],
} as const;

// 获取图标组件的辅助函数（保持向后兼容）
export function getIcon(name: IconName) {
  return Icons[name] || Icons.Appstore;
}

// 简单的图标渲染组件
interface IconProps {
  name?: string;
  className?: string;
  style?: React.CSSProperties;
  size?: number;
}

export const Icon: React.FC<IconProps> = ({ name, className, style, size = 16 }) => {
  if (!name) return null;
  
  // 直接使用图标名称
  if (name in Icons) {
    const IconComponent = Icons[name as IconName];
    return <IconComponent className={className} style={style} size={size} />;
  }
  
  // 默认图标
  return <Icons.Appstore className={className} style={style} size={size} />;
};