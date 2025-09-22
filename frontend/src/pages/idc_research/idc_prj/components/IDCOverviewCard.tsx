import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { IDCData } from '../types/idc';
import { Server, Thermometer, Zap, Clock } from 'lucide-react';

interface IDCOverviewCardProps {
  idc: IDCData;
  isSelected?: boolean;
  onSelect?: () => void;
}

export function IDCOverviewCard({ idc, isSelected, onSelect }: IDCOverviewCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'bg-green-500';
      case 'warning':
        return 'bg-yellow-500';
      case 'critical':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'healthy':
        return '正常';
      case 'warning':
        return '警告';
      case 'critical':
        return '严重';
      default:
        return '未知';
    }
  };

  return (
    <Card 
      className={`cursor-pointer transition-all hover:shadow-lg ${
        isSelected ? 'ring-2 ring-primary' : ''
      }`}
      onClick={onSelect}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{idc.name}</CardTitle>
          <Badge 
            className={`${getStatusColor(idc.status)} text-white`}
          >
            {getStatusText(idc.status)}
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground">{idc.location}</p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Server className="h-4 w-4 text-muted-foreground" />
            <span>{idc.serverCount} 台服务器</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span>{idc.uptime}% 可用性</span>
          </div>
          <div className="flex items-center gap-2">
            <Thermometer className="h-4 w-4 text-muted-foreground" />
            <span>{idc.temperature}°C</span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-muted-foreground" />
            <span>{idc.powerUsage}kW</span>
          </div>
        </div>

        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>CPU使用率</span>
              <span>{idc.cpuUsage}%</span>
            </div>
            <Progress value={idc.cpuUsage} className="h-2" />
          </div>
          
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>内存使用率</span>
              <span>{idc.memoryUsage}%</span>
            </div>
            <Progress value={idc.memoryUsage} className="h-2" />
          </div>
          
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>网络负载</span>
              <span>{idc.networkLoad}%</span>
            </div>
            <Progress value={idc.networkLoad} className="h-2" />
          </div>
        </div>

        <div className="pt-2 border-t">
          <div className="flex justify-between items-center">
            <span className="text-sm">稳定性评分</span>
            <span className="font-medium">{idc.stabilityScore}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}