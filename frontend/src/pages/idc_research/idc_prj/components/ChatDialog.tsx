import React, { useState, useRef, useEffect } from 'react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { ScrollArea } from './ui/scroll-area';
import { Send, MessageCircle, X } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';

interface ChatMessage {
  id: string;
  type: 'user' | 'system';
  content: string;
  timestamp: string;
}

interface ChatDialogProps {
  onQuerySubmit: (query: string) => void;
}

export function ChatDialog({ onQuerySubmit }: ChatDialogProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      type: 'system',
      content: '您好！我是IDC监控分析助手。您可以询问关于数据中心运行状况、性能分析、机房比对等问题。',
      timestamp: new Date().toISOString(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    
    // 触发查询分析
    onQuerySubmit(inputValue);
    
    // 模拟AI响应
    setTimeout(() => {
      const aiResponse = generateAIResponse(inputValue);
      const systemMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        type: 'system',
        content: aiResponse,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, systemMessage]);
    }, 1000);

    setInputValue('');
  };

  const generateAIResponse = (query: string): string => {
    const lowerQuery = query.toLowerCase();
    
    if (lowerQuery.includes('比对') || lowerQuery.includes('对比')) {
      return '我将为您生成多机房性能比对分析报告。请在下方选择需要比对的数据中心，系统将自动生成详细的比对图表和分析建议。';
    } else if (lowerQuery.includes('应用') || lowerQuery.includes('业务') || lowerQuery.includes('服务')) {
      return '我将为您展示应用程序监控页面，包括不同数据中心中的业务应用运行情况、跨数据中心业务比较以及独有业务的性能分析。';
    } else if (lowerQuery.includes('替换') || lowerQuery.includes('替代') || lowerQuery.includes('国产')) {
      return '我将为您展示国产替代监控页面，包括服务器、网络、存储、操作系统、数据库等各类产品的国产替代率、品牌分布和故障率分析。';
    } else if (lowerQuery.includes('性能') || lowerQuery.includes('负载')) {
      return '我将为您展示各数据中心的实时性能监控数据，包括CPU使用率、内存占用、网络负载等关键指标。';
    } else if (lowerQuery.includes('稳定性') || lowerQuery.includes('故障')) {
      return '我将为您分析各数据中心的稳定性指标，包括正常运行时间、故障频率和稳定性评分。';
    } else if (lowerQuery.includes('温度') || lowerQuery.includes('环境')) {
      return '我将为您展示各数据中心的环境监控数据，包括温度、湿度和电力使用情况。';
    } else {
      return '我已收到您的查询请求。系统将在下方展示相关的监控数据和分析结果。您可以进一步选择特定的数据中心进行详细分析。';
    }
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button size="lg" className="gap-2">
          <MessageCircle className="h-5 w-5" />
          发起对话分析
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>IDC监控分析助手</DialogTitle>
        </DialogHeader>
        
        <ScrollArea className="flex-1 pr-4" ref={scrollAreaRef}>
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg px-4 py-2 ${
                    message.type === 'user'
                      ? 'bg-primary text-primary-foreground'
                      : 'bg-muted text-muted-foreground'
                  }`}
                >
                  <p className="mb-1">{message.content}</p>
                  <p className="text-xs opacity-70">{formatTime(message.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>

        <div className="flex gap-2 pt-4 border-t">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="请输入您的查询需求..."
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            className="flex-1"
          />
          <Button onClick={handleSendMessage} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}