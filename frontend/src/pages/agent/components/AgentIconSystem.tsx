import React from 'react';
import { 
  Bot, 
  Settings, 
  User, 
  Database, 
  Lightbulb, 
  Heart, 
  Book, 
  Code, 
  Headphones,
  Brain,
  Sparkles,
  Shield,
  Search,
  MessageCircle,
  Zap,
  Target,
  TrendingUp,
  FileText,
  Globe,
  Music,
  Gamepad2,
  Camera,
  Palette,
  Calculator,
  Star,
  Home,
  AppWindow,
  // 基础功能类
  Cpu,
  Monitor,
  Smartphone,
  Laptop,
  Server,
  HardDrive,
  Wifi,
  Router,
  Activity,
  BarChart,
  PieChart,
  LineChart,
  // 专业技术类
  Terminal,
  GitBranch,
  Package,
  Wrench,
  Cog,
  Bug,
  TestTube,
  Microscope,
  FlaskConical,
  Binary,
  Hash,
  Key,
  Lock,
  Unlock,
  Eye,
  EyeOff,
  Scan,
  Fingerprint,
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  // 服务类型
  Phone,
  Mail,
  MessageSquare,
  Users,
  UserCheck,
  UserPlus,
  UserMinus,
  Crown,
  Award,
  Gift,
  Handshake,
  ThumbsUp,
  ThumbsDown,
  Smile,
  Frown,
  // 教育知识类
  GraduationCap,
  School,
  Library,
  Bookmark,
  BookOpen,
  PenTool,
  Edit,
  FileEdit,
  FilePlus,
  FolderOpen,
  Archive,
  Clipboard,
  ClipboardCheck,
  // 娱乐休闲类
  Video,
  Play,
  Pause,
  Radio,
  Tv,
  Film,
  Image,
  ImagePlus,
  Brush,
  Scissors,
  PartyPopper,
  Coffee,
  Pizza,
  // 工具类型
  Compass,
  Map,
  MapPin,
  Navigation,
  Calendar,
  Clock,
  Timer,
  AlarmClock,
  Bell,
  BellRing,
  Download,
  Upload,
  Share,
  Link,
  Copy,
  Folder,
  FolderPlus,
  Trash,
  RefreshCw
} from 'lucide-react';

// 定义分类颜色
export const categoryColors = {
  '基础': '#1677ff',    // 蓝色 - 基础功能
  '专业': '#722ed1',    // 紫色 - 专业技术
  '服务': '#13c2c2',    // 青色 - 服务类型
  '教育': '#52c41a',    // 绿色 - 教育知识
  '娱乐': '#fa8c16',    // 橙色 - 娱乐休闲
  '工具': '#eb2f96'     // 粉色 - 工具类型
};

// 图标分类映射
export const iconCategoryMap: { [key: string]: string } = {
  // 基础功能
  'Bot': '基础', 'Brain': '基础', 'Sparkles': '基础', 'Cpu': '基础', 'Monitor': '基础', 'Smartphone': '基础', 'Laptop': '基础', 'Server': '基础', 'HardDrive': '基础', 'Wifi': '基础', 'Router': '基础', 'Activity': '基础', 'BarChart': '基础', 'PieChart': '基础', 'LineChart': '基础', 'Star': '基础', 'Home': '基础', 'AppWindow': '基础',
  // 专业技术
  'Settings': '专业', 'Database': '专业', 'Code': '专业', 'Shield': '专业', 'Search': '专业', 'TrendingUp': '专业', 'Terminal': '专业', 'GitBranch': '专业', 'Package': '专业', 'Wrench': '专业', 'Cog': '专业', 'Bug': '专业', 'TestTube': '专业', 'Microscope': '专业', 'FlaskConical': '专业', 'Binary': '专业', 'Hash': '专业', 'Key': '专业', 'Lock': '专业', 'Unlock': '专业', 'Eye': '专业', 'EyeOff': '专业', 'Scan': '专业', 'Fingerprint': '专业', 'AlertTriangle': '专业', 'AlertCircle': '专业', 'CheckCircle': '专业', 'XCircle': '专业', 'Info': '专业',
  // 服务类型
  'User': '服务', 'Headphones': '服务', 'MessageCircle': '服务', 'Heart': '服务', 'Phone': '服务', 'Mail': '服务', 'MessageSquare': '服务', 'Users': '服务', 'UserCheck': '服务', 'UserPlus': '服务', 'UserMinus': '服务', 'Crown': '服务', 'Award': '服务', 'Gift': '服务', 'Handshake': '服务', 'ThumbsUp': '服务', 'ThumbsDown': '服务', 'Smile': '服务', 'Frown': '服务',
  // 教育知识
  'Book': '教育', 'FileText': '教育', 'Lightbulb': '教育', 'Target': '教育', 'GraduationCap': '教育', 'School': '教育', 'Library': '教育', 'Bookmark': '教育', 'BookOpen': '教育', 'PenTool': '教育', 'Edit': '教育', 'FileEdit': '教育', 'FilePlus': '教育', 'FolderOpen': '教育', 'Archive': '教育', 'Clipboard': '教育', 'ClipboardCheck': '教育',
  // 娱乐休闲
  'Music': '娱乐', 'Gamepad2': '娱乐', 'Camera': '娱乐', 'Palette': '娱乐', 'Video': '娱乐', 'Play': '娱乐', 'Pause': '娱乐', 'Radio': '娱乐', 'Tv': '娱乐', 'Film': '娱乐', 'Image': '娱乐', 'ImagePlus': '娱乐', 'Brush': '娱乐', 'Scissors': '娱乐', 'Zap': '娱乐', 'PartyPopper': '娱乐', 'Coffee': '娱乐', 'Pizza': '娱乐',
  // 工具类型
  'Calculator': '工具', 'Globe': '工具', 'Compass': '工具', 'Map': '工具', 'MapPin': '工具', 'Navigation': '工具', 'Calendar': '工具', 'Clock': '工具', 'Timer': '工具', 'AlarmClock': '工具', 'Bell': '工具', 'BellRing': '工具', 'Download': '工具', 'Upload': '工具', 'Share': '工具', 'Link': '工具', 'Copy': '工具', 'Folder': '工具', 'FolderPlus': '工具', 'Trash': '工具', 'RefreshCw': '工具'
};

// 图标配置数据 (94个图标)
export const iconConfig = [
  // 基础功能 (16个)
  { name: 'Bot', label: '机器人', category: '基础' },
  { name: 'Brain', label: '大脑', category: '基础' },
  { name: 'Sparkles', label: '星光', category: '基础' },
  { name: 'Cpu', label: 'CPU', category: '基础' },
  { name: 'Monitor', label: '显示器', category: '基础' },
  { name: 'Smartphone', label: '手机', category: '基础' },
  { name: 'Laptop', label: '笔记本', category: '基础' },
  { name: 'Server', label: '服务器', category: '基础' },
  { name: 'HardDrive', label: '硬盘', category: '基础' },
  { name: 'Wifi', label: 'WiFi', category: '基础' },
  { name: 'Router', label: '路由器', category: '基础' },
  { name: 'Activity', label: '活动', category: '基础' },
  { name: 'BarChart', label: '柱状图', category: '基础' },
  { name: 'PieChart', label: '饼图', category: '基础' },
  { name: 'LineChart', label: '折线图', category: '基础' },
  { name: 'Star', label: '星星', category: '基础' },
  { name: 'Home', label: '首页', category: '基础' },
  { name: 'AppWindow', label: '应用商店', category: '基础' },
  
  // 专业技术 (24个)
  { name: 'Settings', label: '设置', category: '专业' },
  { name: 'Database', label: '数据库', category: '专业' },
  { name: 'Code', label: '代码', category: '专业' },
  { name: 'Shield', label: '盾牌', category: '专业' },
  { name: 'Search', label: '搜索', category: '专业' },
  { name: 'TrendingUp', label: '趋势', category: '专业' },
  { name: 'Terminal', label: '终端', category: '专业' },
  { name: 'GitBranch', label: 'Git分支', category: '专业' },
  { name: 'Package', label: '包', category: '专业' },
  { name: 'Wrench', label: '扳手', category: '专业' },
  { name: 'Cog', label: '齿轮', category: '专业' },
  { name: 'Bug', label: '错误', category: '专业' },
  { name: 'TestTube', label: '试管', category: '专业' },
  { name: 'Microscope', label: '显微镜', category: '专业' },
  { name: 'FlaskConical', label: '锥形瓶', category: '专业' },
  { name: 'Binary', label: '二进制', category: '专业' },
  { name: 'Hash', label: '哈希', category: '专业' },
  { name: 'Key', label: '钥匙', category: '专业' },
  { name: 'Lock', label: '锁', category: '专业' },
  { name: 'Unlock', label: '解锁', category: '专业' },
  { name: 'Eye', label: '眼睛', category: '专业' },
  { name: 'EyeOff', label: '隐藏', category: '专业' },
  { name: 'Scan', label: '扫描', category: '专业' },
  { name: 'Fingerprint', label: '指纹', category: '专业' },
  { name: 'AlertTriangle', label: '警告', category: '专业' },
  { name: 'AlertCircle', label: '提醒', category: '专业' },
  { name: 'CheckCircle', label: '成功', category: '专业' },
  { name: 'XCircle', label: '错误', category: '专业' },
  { name: 'Info', label: '信息', category: '专业' },
  
  // 服务类型 (19个)
  { name: 'User', label: '用户', category: '服务' },
  { name: 'Headphones', label: '客服', category: '服务' },
  { name: 'MessageCircle', label: '消息', category: '服务' },
  { name: 'Heart', label: '心形', category: '服务' },
  { name: 'Phone', label: '电话', category: '服务' },
  { name: 'Mail', label: '邮件', category: '服务' },
  { name: 'MessageSquare', label: '对话', category: '服务' },
  { name: 'Users', label: '用户组', category: '服务' },
  { name: 'UserCheck', label: '用户确认', category: '服务' },
  { name: 'UserPlus', label: '添加用户', category: '服务' },
  { name: 'UserMinus', label: '删除用户', category: '服务' },
  { name: 'Crown', label: '皇冠', category: '服务' },
  { name: 'Award', label: '奖励', category: '服务' },
  { name: 'Gift', label: '礼物', category: '服务' },
  { name: 'Handshake', label: '握手', category: '服务' },
  { name: 'ThumbsUp', label: '点赞', category: '服务' },
  { name: 'ThumbsDown', label: '点踩', category: '服务' },
  { name: 'Smile', label: '微笑', category: '服务' },
  { name: 'Frown', label: '皱眉', category: '服务' },
  
  // 教育知识 (17个)
  { name: 'Book', label: '书籍', category: '教育' },
  { name: 'FileText', label: '文档', category: '教育' },
  { name: 'Lightbulb', label: '灯泡', category: '教育' },
  { name: 'Target', label: '目标', category: '教育' },
  { name: 'GraduationCap', label: '学士帽', category: '教育' },
  { name: 'School', label: '学校', category: '教育' },
  { name: 'Library', label: '图书馆', category: '教育' },
  { name: 'Bookmark', label: '书签', category: '教育' },
  { name: 'BookOpen', label: '翻开的书', category: '教育' },
  { name: 'PenTool', label: '钢笔工具', category: '教育' },
  { name: 'Edit', label: '编辑', category: '教育' },
  { name: 'FileEdit', label: '文件编辑', category: '教育' },
  { name: 'FilePlus', label: '新建文件', category: '教育' },
  { name: 'FolderOpen', label: '打开文件夹', category: '教育' },
  { name: 'Archive', label: '归档', category: '教育' },
  { name: 'Clipboard', label: '剪贴板', category: '教育' },
  { name: 'ClipboardCheck', label: '剪贴板确认', category: '教育' },
  
  // 娱乐休闲 (18个)
  { name: 'Music', label: '音乐', category: '娱乐' },
  { name: 'Gamepad2', label: '游戏手柄', category: '娱乐' },
  { name: 'Camera', label: '相机', category: '娱乐' },
  { name: 'Palette', label: '调色板', category: '娱乐' },
  { name: 'Video', label: '视频', category: '娱乐' },
  { name: 'Play', label: '播放', category: '娱乐' },
  { name: 'Pause', label: '暂停', category: '娱乐' },
  { name: 'Radio', label: '收音机', category: '娱乐' },
  { name: 'Tv', label: '电视', category: '娱乐' },
  { name: 'Film', label: '电影', category: '娱乐' },
  { name: 'Image', label: '图片', category: '娱乐' },
  { name: 'ImagePlus', label: '添加图片', category: '娱乐' },
  { name: 'Brush', label: '画笔', category: '娱乐' },
  { name: 'Scissors', label: '剪刀', category: '娱乐' },
  { name: 'Zap', label: '闪电', category: '娱乐' },
  { name: 'PartyPopper', label: '派对', category: '娱乐' },
  { name: 'Coffee', label: '咖啡', category: '娱乐' },
  { name: 'Pizza', label: '披萨', category: '娱乐' },
  
  // 工具类型 (20个)
  { name: 'Calculator', label: '计算器', category: '工具' },
  { name: 'Globe', label: '地球', category: '工具' },
  { name: 'Compass', label: '指南针', category: '工具' },
  { name: 'Map', label: '地图', category: '工具' },
  { name: 'MapPin', label: '地图标记', category: '工具' },
  { name: 'Navigation', label: '导航', category: '工具' },
  { name: 'Calendar', label: '日历', category: '工具' },
  { name: 'Clock', label: '时钟', category: '工具' },
  { name: 'Timer', label: '计时器', category: '工具' },
  { name: 'AlarmClock', label: '闹钟', category: '工具' },
  { name: 'Bell', label: '铃铛', category: '工具' },
  { name: 'BellRing', label: '响铃', category: '工具' },
  { name: 'Download', label: '下载', category: '工具' },
  { name: 'Upload', label: '上传', category: '工具' },
  { name: 'Share', label: '分享', category: '工具' },
  { name: 'Link', label: '链接', category: '工具' },
  { name: 'Copy', label: '复制', category: '工具' },
  { name: 'Folder', label: '文件夹', category: '工具' },
  { name: 'FolderPlus', label: '新建文件夹', category: '工具' },
  { name: 'Trash', label: '垃圾桶', category: '工具' },
  { name: 'RefreshCw', label: '刷新', category: '工具' }
];

// 根据图标名称渲染图标组件
export const renderIcon = (iconName: string, size: number = 18, color?: string) => {
  // 如果没有指定颜色，则根据分类获取颜色
  if (!color) {
    const category = iconCategoryMap[iconName];
    color = category ? categoryColors[category as keyof typeof categoryColors] : '#666666';
  }
  
  const iconMap: { [key: string]: React.ReactNode } = {
    // 基础功能
    'Bot': <Bot size={size} color={color} />,
    'Brain': <Brain size={size} color={color} />,
    'Sparkles': <Sparkles size={size} color={color} />,
    'Cpu': <Cpu size={size} color={color} />,
    'Monitor': <Monitor size={size} color={color} />,
    'Smartphone': <Smartphone size={size} color={color} />,
    'Laptop': <Laptop size={size} color={color} />,
    'Server': <Server size={size} color={color} />,
    'HardDrive': <HardDrive size={size} color={color} />,
    'Wifi': <Wifi size={size} color={color} />,
    'Router': <Router size={size} color={color} />,
    'Activity': <Activity size={size} color={color} />,
    'BarChart': <BarChart size={size} color={color} />,
    'PieChart': <PieChart size={size} color={color} />,
    'LineChart': <LineChart size={size} color={color} />,
    'Star': <Star size={size} color={color} />,
    'Home': <Home size={size} color={color} />,
    'AppWindow': <AppWindow size={size} color={color} />,
    
    // 专业技术
    'Settings': <Settings size={size} color={color} />,
    'Database': <Database size={size} color={color} />,
    'Code': <Code size={size} color={color} />,
    'Shield': <Shield size={size} color={color} />,
    'Search': <Search size={size} color={color} />,
    'TrendingUp': <TrendingUp size={size} color={color} />,
    'Terminal': <Terminal size={size} color={color} />,
    'GitBranch': <GitBranch size={size} color={color} />,
    'Package': <Package size={size} color={color} />,
    'Wrench': <Wrench size={size} color={color} />,
    'Cog': <Cog size={size} color={color} />,
    'Bug': <Bug size={size} color={color} />,
    'TestTube': <TestTube size={size} color={color} />,
    'Microscope': <Microscope size={size} color={color} />,
    'FlaskConical': <FlaskConical size={size} color={color} />,
    'Binary': <Binary size={size} color={color} />,
    'Hash': <Hash size={size} color={color} />,
    'Key': <Key size={size} color={color} />,
    'Lock': <Lock size={size} color={color} />,
    'Unlock': <Unlock size={size} color={color} />,
    'Eye': <Eye size={size} color={color} />,
    'EyeOff': <EyeOff size={size} color={color} />,
    'Scan': <Scan size={size} color={color} />,
    'Fingerprint': <Fingerprint size={size} color={color} />,
    'AlertTriangle': <AlertTriangle size={size} color={color} />,
    'AlertCircle': <AlertCircle size={size} color={color} />,
    'CheckCircle': <CheckCircle size={size} color={color} />,
    'XCircle': <XCircle size={size} color={color} />,
    'Info': <Info size={size} color={color} />,
    
    // 服务类型
    'User': <User size={size} color={color} />,
    'Headphones': <Headphones size={size} color={color} />,
    'MessageCircle': <MessageCircle size={size} color={color} />,
    'Heart': <Heart size={size} color={color} />,
    'Phone': <Phone size={size} color={color} />,
    'Mail': <Mail size={size} color={color} />,
    'MessageSquare': <MessageSquare size={size} color={color} />,
    'Users': <Users size={size} color={color} />,
    'UserCheck': <UserCheck size={size} color={color} />,
    'UserPlus': <UserPlus size={size} color={color} />,
    'UserMinus': <UserMinus size={size} color={color} />,
    'Crown': <Crown size={size} color={color} />,
    'Award': <Award size={size} color={color} />,
    'Gift': <Gift size={size} color={color} />,
    'Handshake': <Handshake size={size} color={color} />,
    'ThumbsUp': <ThumbsUp size={size} color={color} />,
    'ThumbsDown': <ThumbsDown size={size} color={color} />,
    'Smile': <Smile size={size} color={color} />,
    'Frown': <Frown size={size} color={color} />,
    
    // 教育知识
    'Book': <Book size={size} color={color} />,
    'FileText': <FileText size={size} color={color} />,
    'Lightbulb': <Lightbulb size={size} color={color} />,
    'Target': <Target size={size} color={color} />,
    'GraduationCap': <GraduationCap size={size} color={color} />,
    'School': <School size={size} color={color} />,
    'Library': <Library size={size} color={color} />,
    'Bookmark': <Bookmark size={size} color={color} />,
    'BookOpen': <BookOpen size={size} color={color} />,
    'PenTool': <PenTool size={size} color={color} />,
    'Edit': <Edit size={size} color={color} />,
    'FileEdit': <FileEdit size={size} color={color} />,
    'FilePlus': <FilePlus size={size} color={color} />,
    'FolderOpen': <FolderOpen size={size} color={color} />,
    'Archive': <Archive size={size} color={color} />,
    'Clipboard': <Clipboard size={size} color={color} />,
    'ClipboardCheck': <ClipboardCheck size={size} color={color} />,
    
    // 娱乐休闲
    'Music': <Music size={size} color={color} />,
    'Gamepad2': <Gamepad2 size={size} color={color} />,
    'Camera': <Camera size={size} color={color} />,
    'Palette': <Palette size={size} color={color} />,
    'Video': <Video size={size} color={color} />,
    'Play': <Play size={size} color={color} />,
    'Pause': <Pause size={size} color={color} />,
    'Radio': <Radio size={size} color={color} />,
    'Tv': <Tv size={size} color={color} />,
    'Film': <Film size={size} color={color} />,
    'Image': <Image size={size} color={color} />,
    'ImagePlus': <ImagePlus size={size} color={color} />,
    'Brush': <Brush size={size} color={color} />,
    'Scissors': <Scissors size={size} color={color} />,
    'Zap': <Zap size={size} color={color} />,
    'PartyPopper': <PartyPopper size={size} color={color} />,
    'Coffee': <Coffee size={size} color={color} />,
    'Pizza': <Pizza size={size} color={color} />,
    
    // 工具类型
    'Calculator': <Calculator size={size} color={color} />,
    'Globe': <Globe size={size} color={color} />,
    'Compass': <Compass size={size} color={color} />,
    'Map': <Map size={size} color={color} />,
    'MapPin': <MapPin size={size} color={color} />,
    'Navigation': <Navigation size={size} color={color} />,
    'Calendar': <Calendar size={size} color={color} />,
    'Clock': <Clock size={size} color={color} />,
    'Timer': <Timer size={size} color={color} />,
    'AlarmClock': <AlarmClock size={size} color={color} />,
    'Bell': <Bell size={size} color={color} />,
    'BellRing': <BellRing size={size} color={color} />,
    'Download': <Download size={size} color={color} />,
    'Upload': <Upload size={size} color={color} />,
    'Share': <Share size={size} color={color} />,
    'Link': <Link size={size} color={color} />,
    'Copy': <Copy size={size} color={color} />,
    'Folder': <Folder size={size} color={color} />,
    'FolderPlus': <FolderPlus size={size} color={color} />,
    'Trash': <Trash size={size} color={color} />,
    'RefreshCw': <RefreshCw size={size} color={color} />
  };
  
  return iconMap[iconName] || <Bot size={size} color={color} />;
};

// 获取图标背景色（根据分类）
export const getIconBackgroundColor = (iconName: string, opacity: string = '20'): string => {
  const category = iconCategoryMap[iconName];
  if (category) {
    const categoryColor = categoryColors[category as keyof typeof categoryColors];
    return categoryColor + opacity; // 添加透明度
  }
  return categoryColors['基础'] + opacity; // 默认蓝色背景
};

// 按分类分组图标
export const getIconsByCategory = () => {
  const grouped: { [category: string]: typeof iconConfig } = {};
  
  iconConfig.forEach(icon => {
    if (!grouped[icon.category]) {
      grouped[icon.category] = [];
    }
    grouped[icon.category].push(icon);
  });
  
  return grouped;
};

// 获取所有可用的图标名称
export const getAllIconNames = (): string[] => {
  return iconConfig.map(icon => icon.name);
};

// 获取图标标签
export const getIconLabel = (iconName: string): string => {
  const icon = iconConfig.find(icon => icon.name === iconName);
  return icon?.label || iconName;
};

// 获取图标分类
export const getIconCategory = (iconName: string): string => {
  return iconCategoryMap[iconName] || '基础';
};