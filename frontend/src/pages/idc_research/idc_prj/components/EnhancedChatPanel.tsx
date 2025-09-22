import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { ScrollArea } from './ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { 
  Send, 
  Mic, 
  MicOff, 
  Paperclip, 
  X, 
  Bot, 
  User, 
  Upload,
  FileText,
  Image,
  Settings,
  Sparkles,
  Brain,
  Minimize2,
  Maximize2
} from 'lucide-react';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: string;
  attachments?: Array<{
    name: string;
    type: string;
    size: number;
  }>;
}

interface EnhancedChatPanelProps {
  onQuerySubmit: (query: string) => void;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
}

const AI_MODELS = [
  { id: 'gpt4', name: 'GPT-4', description: '最强大的分析模型' },
  { id: 'claude', name: 'Claude-3', description: '专业分析助手' },
  { id: 'gemini', name: 'Gemini Pro', description: '快速响应模型' },
  { id: 'local', name: '本地模型', description: '私有化部署' }
];

const SUGGESTED_QUERIES = [
  "分析北京和上海数据中心的性能差异",
  "查看支付业务在各机房的运行状况",
  "检查服务器国产替代率情况",
  "对比各数据中心的稳定性指标",
  "分析最近的系统故障趋势"
];

const INITIAL_MESSAGES: ChatMessage[] = [
  {
    id: '1',
    type: 'assistant',
    content: `👋 您好！我是您的IDC智能分析助手。

🔍 **我的主要功能：**
• 数据中心性能监控与分析
• 多机房运行状况比对
• 应用程序运行状态监控  
• 国产替代率分析统计
• 故障预警与趋势分析
• 智能运维建议生成

💡 **使用提示：**
• 可以通过语音或文字与我交流
• 支持上传文档、图片等文件进行分析
• 选择不同的AI模型获得专业建议
• 点击下方建议问题快速开始

请告诉我您需要了解什么？我将为您提供专业的数据中心分析服务！`,
    timestamp: new Date().toISOString(),
  }
];

export function EnhancedChatPanel({ onQuerySubmit, isMinimized = false, onToggleMinimize }: EnhancedChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>(INITIAL_MESSAGES);
  const [inputValue, setInputValue] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt4');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [attachments, setAttachments] = useState<File[]>([]);
  const [inputMode, setInputMode] = useState<'text' | 'textarea'>('text');
  
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim() && attachments.length === 0) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim() || '上传了文件',
      timestamp: new Date().toISOString(),
      attachments: attachments.map(file => ({
        name: file.name,
        type: file.type,
        size: file.size
      }))
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    
    // 触发查询分析
    if (inputValue.trim()) {
      onQuerySubmit(inputValue);
    }
    
    // 模拟AI响应
    setTimeout(() => {
      const aiResponse = generateAIResponse(inputValue, attachments);
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: aiResponse,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);

    setInputValue('');
    setAttachments([]);
  };

  const generateAIResponse = (query: string, files: File[]): string => {
    const lowerQuery = query.toLowerCase();
    const model = AI_MODELS.find(m => m.id === selectedModel);
    
    let response = `🤖 使用 ${model?.name} 分析中...\n\n`;
    
    if (files.length > 0) {
      response += `📎 已收到 ${files.length} 个文件，正在分析...\n\n`;
    }
    
    if (lowerQuery.includes('比对') || lowerQuery.includes('对比')) {
      response += '📊 **多机房性能比对分析**\n\n已为您切换到性能比对页面。请在下方选择需要比对的数据中心，我将生成：\n• CPU、内存、网络负载对比\n• 稳定性评分分析\n• 综合性能排名\n• 优化建议方案';
    } else if (lowerQuery.includes('应用') || lowerQuery.includes('业务') || lowerQuery.includes('服务')) {
      response += '📱 **应用程序监控分析**\n\n已为您切换到应用监控页面，包含：\n• 支付业务运行状态\n• 备付金业务监控\n• 跨数据中心业务比较\n• 服务响应时间分析\n• 业务可用性报告';
    } else if (lowerQuery.includes('替换') || lowerQuery.includes('替代') || lowerQuery.includes('国产')) {
      response += '🏭 **国产替代率分析**\n\n已为您切换到国产替代监控页面：\n• 服务器、网络、存储设备替代率\n• 操作系统、数据库软件国产化进度\n• 品牌分布统计\n• 故障率对比分析\n• 替代规划时间线';
    } else if (lowerQuery.includes('性能') || lowerQuery.includes('负载')) {
      response += '⚡ **实时性能监控**\n\n当前系统性能概览：\n• CPU平均使用率: 68%\n• 内存占用率: 72%\n• 网络负载: 正常\n• 存储IO: 良好\n\n建议关注北京数据中心CPU使用率偏高的情况。';
    } else if (lowerQuery.includes('稳定性') || lowerQuery.includes('故障')) {
      response += '🛡️ **稳定性分析报告**\n\n系统稳定性评估：\n• 整体稳定性评分: 8.7/10\n• 正常运行时间: 99.8%\n• 近30天故障次数: 2次\n• 平均修复时间: 15分钟\n\n建议加强网络设备维护。';
    } else if (lowerQuery.includes('温度') || lowerQuery.includes('环境')) {
      response += '🌡️ **环境监控数据**\n\n各机房环境状态：\n• 平均温度: 22.5°C\n• 湿度范围: 45-55%\n• 电力使用效率: 1.3 PUE\n• 空调系统运行正常\n\n所有环境指标均在正常范围内。';
    } else {
      response += '📋 **智能分析结果**\n\n我已收到您的查询请求，正在为您准备相关的监控数据和分析结果。\n\n💡 **快速操作建议：**\n• 选择下方数据中心卡片进行详细分析\n• 使用语音输入获得更自然的交互体验\n• 上传相关文档我可以帮您深度分析\n\n如需更多帮助，请告诉我具体需求！';
    }
    
    return response;
  };

  const handleVoiceToggle = () => {
    setIsRecording(!isRecording);
    // 这里可以集成语音识别API
    if (!isRecording) {
      // 开始录音
      console.log('开始语音输入...');
    } else {
      // 停止录音
      console.log('结束语音输入...');
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setAttachments(prev => [...prev, ...files]);
  };

  const removeAttachment = (index: number) => {
    setAttachments(prev => prev.filter((_, i) => i !== index));
  };

  const handleSuggestedQuery = (query: string) => {
    setInputValue(query);
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (isMinimized) {
    return (
      <Card className="fixed bottom-4 right-4 w-80 shadow-lg border-primary/20 z-50">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Bot className="h-5 w-5 text-primary" />
              <CardTitle className="text-sm">AI分析助手</CardTitle>
              <Badge variant="secondary" className="text-xs">在线</Badge>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={onToggleMinimize}
              className="h-6 w-6 p-0"
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          <p className="text-sm text-muted-foreground mb-3">
            点击展开与AI助手对话
          </p>
          <div className="flex gap-1 flex-wrap">
            {SUGGESTED_QUERIES.slice(0, 2).map((query, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                className="text-xs h-6"
                onClick={() => {
                  handleSuggestedQuery(query);
                  onToggleMinimize?.();
                }}
              >
                {query.slice(0, 8)}...
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-full flex flex-col">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <Sparkles className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="flex items-center gap-2">
                AI智能分析助手
                <Badge variant="secondary" className="text-xs">
                  <Brain className="h-3 w-3 mr-1" />
                  在线
                </Badge>
              </CardTitle>
              <p className="text-sm text-muted-foreground">
                IDC数据中心专业分析服务
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Select value={selectedModel} onValueChange={setSelectedModel}>
              <SelectTrigger className="w-32 h-8">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {AI_MODELS.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    <div className="flex flex-col">
                      <span className="text-xs font-medium">{model.name}</span>
                      <span className="text-xs text-muted-foreground">{model.description}</span>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {onToggleMinimize && (
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={onToggleMinimize}
                className="h-8 w-8 p-0"
              >
                <Minimize2 className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        {/* 聊天消息区域 */}
        <ScrollArea className="flex-1 px-4" ref={scrollAreaRef}>
          <div className="space-y-4 pb-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${message.type === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
              >
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                  message.type === 'user' 
                    ? 'bg-primary text-primary-foreground' 
                    : 'bg-muted'
                }`}>
                  {message.type === 'user' ? 
                    <User className="h-4 w-4" /> : 
                    <Bot className="h-4 w-4" />
                  }
                </div>
                <div className={`flex-1 max-w-[80%] space-y-2`}>
                  <div className={`rounded-lg px-4 py-3 ${
                    message.type === 'user'
                      ? 'bg-primary text-primary-foreground ml-auto'
                      : 'bg-muted'
                  }`}>
                    <div className="whitespace-pre-wrap text-sm">
                      {message.content}
                    </div>
                    {message.attachments && message.attachments.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {message.attachments.map((file, index) => (
                          <div key={index} className="flex items-center gap-2 text-xs opacity-80">
                            <FileText className="h-3 w-3" />
                            <span>{file.name}</span>
                            <span>({formatFileSize(file.size)})</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  <div className={`text-xs text-muted-foreground ${
                    message.type === 'user' ? 'text-right' : 'text-left'
                  }`}>
                    {formatTime(message.timestamp)}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex gap-3">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="bg-muted rounded-lg px-4 py-3">
                  <div className="flex items-center gap-2 text-sm">
                    <div className="animate-spin w-4 h-4 border-2 border-current border-t-transparent rounded-full"></div>
                    AI正在思考...
                  </div>
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <Separator />

        {/* 建议问题 */}
        {messages.length === 1 && (
          <div className="p-4 border-b">
            <p className="text-sm font-medium mb-2">🚀 快速开始：</p>
            <div className="flex flex-wrap gap-2">
              {SUGGESTED_QUERIES.slice(0, 3).map((query, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  className="text-xs h-7"
                  onClick={() => handleSuggestedQuery(query)}
                >
                  {query}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* 附件预览 */}
        {attachments.length > 0 && (
          <div className="p-4 border-b">
            <p className="text-sm font-medium mb-2">📎 已选择文件：</p>
            <div className="space-y-2">
              {attachments.map((file, index) => (
                <div key={index} className="flex items-center gap-2 text-sm bg-muted rounded p-2">
                  <FileText className="h-4 w-4" />
                  <span className="flex-1">{file.name}</span>
                  <span className="text-muted-foreground">({formatFileSize(file.size)})</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => removeAttachment(index)}
                    className="h-6 w-6 p-0"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 输入区域 */}
        <div className="p-4 space-y-3">
          <div className="flex items-center gap-2">
            {inputMode === 'text' ? (
              <Input
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="询问数据中心相关问题..."
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSendMessage()}
                className="flex-1"
              />
            ) : (
              <Textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder="输入详细问题或需求..."
                rows={3}
                className="flex-1 resize-none"
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && e.ctrlKey && handleSendMessage()}
              />
            )}
            <div className="flex flex-col gap-1">
              <Button
                variant={isRecording ? "destructive" : "outline"}
                size="sm"
                onClick={handleVoiceToggle}
                className="w-10 h-10 p-0"
              >
                {isRecording ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => fileInputRef.current?.click()}
                className="w-10 h-10 p-0"
              >
                <Paperclip className="h-4 w-4" />
              </Button>
            </div>
            <Button onClick={handleSendMessage} size="sm" className="h-10">
              <Send className="h-4 w-4" />
            </Button>
          </div>
          
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-4">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInputMode(inputMode === 'text' ? 'textarea' : 'text')}
                className="h-6 text-xs px-2"
              >
                {inputMode === 'text' ? '多行输入' : '单行输入'}
              </Button>
              <span>使用 {AI_MODELS.find(m => m.id === selectedModel)?.name}</span>
            </div>
            <span>
              {inputMode === 'textarea' ? 'Ctrl + Enter 发送' : 'Enter 发送'}
            </span>
          </div>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          className="hidden"
          onChange={handleFileUpload}
          accept=".pdf,.doc,.docx,.txt,.csv,.xlsx,.png,.jpg,.jpeg"
        />
      </CardContent>
    </Card>
  );
}