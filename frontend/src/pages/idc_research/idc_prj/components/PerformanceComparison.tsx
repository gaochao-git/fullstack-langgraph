import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, LineChart, Line } from 'recharts';
import { IDCData } from '../types/idc';

interface PerformanceComparisonProps {
  selectedIDCs: IDCData[];
}

export function PerformanceComparison({ selectedIDCs }: PerformanceComparisonProps) {
  if (selectedIDCs.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>性能比对分析</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground text-center py-8">
            请选择至少一个数据中心进行比对分析
          </p>
        </CardContent>
      </Card>
    );
  }

  // 准备比较数据
  const comparisonData = selectedIDCs.map(idc => ({
    name: idc.name.replace('数据中心', ''),
    CPU: idc.cpuUsage,
    内存: idc.memoryUsage,
    网络: idc.networkLoad,
    稳定性: idc.stabilityScore,
    电力: idc.powerUsage / 10, // 缩放以便显示
  }));

  // 雷达图数据
  const radarData = selectedIDCs.map(idc => ({
    name: idc.name.replace('数据中心', ''),
    CPU: 100 - idc.cpuUsage, // 反转，使用率越低越好
    内存: 100 - idc.memoryUsage,
    网络: 100 - idc.networkLoad,
    稳定性: idc.stabilityScore,
    温控: 100 - (idc.temperature - 15) * 2, // 温度越接近20度越好
  }));

  // 历史趋势数据（取最近6小时）
  const trendData = selectedIDCs[0]?.performanceHistory.slice(-6).map((point, index) => {
    const result: any = {
      time: new Date(point.timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }),
    };
    
    selectedIDCs.forEach(idc => {
      if (idc.performanceHistory[index + (idc.performanceHistory.length - 6)]) {
        result[idc.name.replace('数据中心', '')] = idc.performanceHistory[index + (idc.performanceHistory.length - 6)].cpu;
      }
    });
    
    return result;
  }) || [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 关键指标对比 */}
        <Card>
          <CardHeader>
            <CardTitle>关键指标对比</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="CPU" fill="#8884d8" name="CPU使用率%" />
                <Bar dataKey="内存" fill="#82ca9d" name="内存使用率%" />
                <Bar dataKey="网络" fill="#ffc658" name="网络负载%" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 综合性能雷达图 */}
        <Card>
          <CardHeader>
            <CardTitle>综合性能雷达图</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="name" />
                <PolarRadiusAxis angle={90} domain={[0, 100]} />
                {['CPU', '内存', '网络', '稳定性', '温控'].map((metric, index) => (
                  <Radar
                    key={metric}
                    dataKey={metric}
                    stroke={`hsl(${index * 60}, 70%, 50%)`}
                    fill={`hsl(${index * 60}, 70%, 50%)`}
                    fillOpacity={0.1}
                  />
                ))}
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* CPU使用率趋势 */}
      {trendData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>CPU使用率趋势（最近6小时）</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                {selectedIDCs.map((idc, index) => (
                  <Line
                    key={idc.id}
                    type="monotone"
                    dataKey={idc.name.replace('数据中心', '')}
                    stroke={`hsl(${index * 60}, 70%, 50%)`}
                    strokeWidth={2}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* 比对分析报告 */}
      <Card>
        <CardHeader>
          <CardTitle>比对分析报告</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <h4 className="font-medium mb-2">性能评估</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {selectedIDCs.map(idc => (
                  <div key={idc.id} className="p-4 border rounded-lg">
                    <h5 className="font-medium">{idc.name}</h5>
                    <div className="mt-2 space-y-1 text-sm">
                      <p>平均CPU: {idc.cpuUsage}%</p>
                      <p>平均内存: {idc.memoryUsage}%</p>
                      <p>网络负载: {idc.networkLoad}%</p>
                      <p>稳定性: {idc.stabilityScore}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">优化建议</h4>
              <div className="space-y-2 text-sm">
                {selectedIDCs.map(idc => {
                  const suggestions = [];
                  if (idc.cpuUsage > 80) suggestions.push('CPU使用率较高，建议增加服务器或优化负载分配');
                  if (idc.memoryUsage > 85) suggestions.push('内存使用率偏高，建议扩容内存或优化内存使用');
                  if (idc.networkLoad > 70) suggestions.push('网络负载较重，建议优化网络配置或增加带宽');
                  if (idc.temperature > 25) suggestions.push('机房温度偏高，建议检查制冷系统');
                  if (idc.stabilityScore < 95) suggestions.push('稳定性有待提升，建议检查硬件状况');
                  
                  return suggestions.length > 0 && (
                    <div key={idc.id} className="p-3 bg-muted rounded">
                      <p className="font-medium">{idc.name}:</p>
                      <ul className="list-disc list-inside mt-1 space-y-1">
                        {suggestions.map((suggestion, index) => (
                          <li key={index}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}