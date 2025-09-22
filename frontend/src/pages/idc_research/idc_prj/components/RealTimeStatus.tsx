import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { AlertTriangle, CheckCircle, XCircle, Clock } from 'lucide-react';

interface SystemAlert {
  id: string;
  level: 'info' | 'warning' | 'critical';
  message: string;
  timestamp: string;
  idcName: string;
}

export function RealTimeStatus() {
  const [alerts, setAlerts] = useState<SystemAlert[]>([
    {
      id: '1',
      level: 'critical',
      message: '成都数据中心CPU使用率超过85%阈值',
      timestamp: new Date().toISOString(),
      idcName: '成都数据中心',
    },
    {
      id: '2',
      level: 'warning',
      message: '广州数据中心温度偏高，当前26°C',
      timestamp: new Date(Date.now() - 300000).toISOString(),
      idcName: '广州数据中心',
    },
    {
      id: '3',
      level: 'info',
      message: '北京数据中心完成定期维护，所有服务恢复正常',
      timestamp: new Date(Date.now() - 600000).toISOString(),
      idcName: '北京数据中心',
    },
  ]);

  const [currentTime, setCurrentTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const getAlertIcon = (level: string) => {
    switch (level) {
      case 'critical':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'info':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const getAlertVariant = (level: string) => {
    switch (level) {
      case 'critical':
        return 'destructive';
      case 'warning':
        return 'default';
      case 'info':
        return 'default';
      default:
        return 'default';
    }
  };

  const formatRelativeTime = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diffMs = now.getTime() - time.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return '刚刚';
    if (diffMins < 60) return `${diffMins}分钟前`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}小时前`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}天前`;
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>实时状态监控</CardTitle>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Clock className="h-4 w-4" />
            <span>
              {currentTime.toLocaleString('zh-CN', {
                year: 'numeric',
                month: '2-digit',
                day: '2-digit',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
            </span>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-900/20">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm font-medium">正常运行</p>
                <p className="text-lg">3 个数据中心</p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-lg bg-yellow-50 dark:bg-yellow-900/20">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              <div>
                <p className="text-sm font-medium">警告状态</p>
                <p className="text-lg">1 个数据中心</p>
              </div>
            </div>
            <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 dark:bg-red-900/20">
              <XCircle className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm font-medium">严重警告</p>
                <p className="text-lg">1 个数据中心</p>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-3">最新告警</h4>
            <div className="space-y-3">
              {alerts.map((alert) => (
                <Alert key={alert.id} variant={getAlertVariant(alert.level) as any}>
                  <div className="flex items-start gap-3">
                    {getAlertIcon(alert.level)}
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center justify-between">
                        <Badge variant="outline" className="text-xs">
                          {alert.idcName}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {formatRelativeTime(alert.timestamp)}
                        </span>
                      </div>
                      <AlertDescription className="text-sm leading-relaxed">
                        {alert.message}
                      </AlertDescription>
                    </div>
                  </div>
                </Alert>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}