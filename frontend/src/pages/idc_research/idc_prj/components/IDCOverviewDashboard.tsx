import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { mockIDCData } from '../data/mockData';
import { mockApplications, businessTypes, idcNameMap } from '../data/applicationData';
import { MapPin, Server, Zap, Target, TrendingUp, DollarSign, Activity, Globe } from 'lucide-react';

export function IDCOverviewDashboard() {
  // IDC地理位置数据
  const locationData = mockIDCData.map(idc => ({
    name: idc.name,
    location: idc.location,
    status: idc.status,
    serverCount: idc.serverCount,
    coordinates: getCoordinates(idc.location),
  }));

  function getCoordinates(location: string): [number, number] {
    const coords: Record<string, [number, number]> = {
      '北京': [116.4074, 39.9042],
      '上海': [121.4737, 31.2304],
      '广州': [113.2644, 23.1291],
      '深圳': [114.0579, 22.5431],
      '成都': [104.0668, 30.5728],
    };
    return coords[location] || [116.4074, 39.9042];
  }

  // 整体容量概览数据
  const capacityData = {
    totalServers: mockIDCData.reduce((sum, idc) => sum + idc.serverCount, 0),
    totalCpuUsage: Math.round(mockIDCData.reduce((sum, idc) => sum + (idc.cpuUsage * idc.serverCount), 0) / mockIDCData.reduce((sum, idc) => sum + idc.serverCount, 0)),
    totalMemoryUsage: Math.round(mockIDCData.reduce((sum, idc) => sum + (idc.memoryUsage * idc.serverCount), 0) / mockIDCData.reduce((sum, idc) => sum + idc.serverCount, 0)),
    avgNetworkLoad: Math.round(mockIDCData.reduce((sum, idc) => sum + idc.networkLoad, 0) / mockIDCData.length),
    avgPowerUsage: Math.round(mockIDCData.reduce((sum, idc) => sum + idc.powerUsage, 0) / mockIDCData.length),
  };

  // SLA达成情况数据
  const slaData = mockIDCData.map(idc => ({
    name: idc.name.replace('数据中心', ''),
    sla: idc.uptime,
    target: 99.9,
    status: idc.uptime >= 99.9 ? 'achieved' : idc.uptime >= 99.5 ? 'warning' : 'critical',
  }));

  // 成本效率分析数据
  const costEfficiencyData = mockIDCData.map(idc => ({
    name: idc.name.replace('数据中心', ''),
    powerCost: Math.round(idc.powerUsage * 0.8 * 24 * 30), // 模拟月电费
    costPerServer: Math.round((idc.powerUsage * 0.8 * 24 * 30) / idc.serverCount),
    efficiency: Math.round((idc.serverCount * (100 - idc.cpuUsage)) / idc.powerUsage),
  }));

  // 历史趋势数据（模拟过去7天）
  const trendData = Array.from({ length: 7 }, (_, i) => {
    const date = new Date();
    date.setDate(date.getDate() - (6 - i));
    return {
      date: date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }),
      avgCpuUsage: 45 + Math.random() * 20,
      avgMemoryUsage: 60 + Math.random() * 15,
      networkLoad: 30 + Math.random() * 25,
      incidents: Math.floor(Math.random() * 3),
    };
  });

  // 业务分布数据
  const businessDistribution = businessTypes.map(businessType => {
    const apps = mockApplications.filter(app => app.businessType === businessType);
    const totalInstances = apps.reduce((sum, app) => 
      sum + app.services.reduce((serviceSum, service) => serviceSum + service.instances, 0), 0
    );
    const idcCount = new Set(apps.flatMap(app => app.deployedIDCs)).size;
    
    return {
      name: businessType,
      instances: totalInstances,
      idcCount,
      color: getBusinessColor(businessType),
    };
  });

  function getBusinessColor(businessType: string): string {
    const colors: Record<string, string> = {
      '支付业务': '#8884d8',
      '备付金业务': '#82ca9d',
      '风险控制': '#ffc658',
      '数据分析': '#ff7300',
      '基础设施': '#00ff88',
    };
    return colors[businessType] || '#8884d8';
  }

  return (
    <div className="space-y-6">
      {/* IDC地理分布 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="h-5 w-5" />
            IDC地理分布
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 简化的地图视图 */}
            <div className="relative bg-muted rounded-lg p-6 h-64">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <Globe className="h-12 w-12 mx-auto text-muted-foreground mb-2" />
                  <p className="text-sm text-muted-foreground">中国数据中心分布图</p>
                </div>
              </div>
              {locationData.map((location, index) => (
                <div
                  key={location.name}
                  className={`absolute w-3 h-3 rounded-full border-2 border-white shadow-lg ${
                    location.status === 'healthy' ? 'bg-green-500' :
                    location.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                  }`}
                  style={{
                    left: `${20 + index * 15}%`,
                    top: `${30 + (index % 2) * 20}%`,
                  }}
                  title={`${location.name} - ${location.serverCount}台服务器`}
                />
              ))}
            </div>
            
            {/* 位置详情 */}
            <div className="space-y-3">
              {locationData.map(location => (
                <div key={location.name} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      location.status === 'healthy' ? 'bg-green-500' :
                      location.status === 'warning' ? 'bg-yellow-500' : 'bg-red-500'
                    }`} />
                    <span className="font-medium">{location.name}</span>
                    <Badge variant="outline">{location.location}</Badge>
                  </div>
                  <span className="text-sm text-muted-foreground">{location.serverCount}台服务器</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 整体容量概览 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              整体容量概览
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold">{capacityData.totalServers.toLocaleString()}</p>
                <p className="text-sm text-muted-foreground">总服务器数</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold">{mockIDCData.length}</p>
                <p className="text-sm text-muted-foreground">数据中心数</p>
              </div>
            </div>
            
            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>CPU使用率</span>
                  <span>{capacityData.totalCpuUsage}%</span>
                </div>
                <Progress value={capacityData.totalCpuUsage} className="h-2" />
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>内存使用率</span>
                  <span>{capacityData.totalMemoryUsage}%</span>
                </div>
                <Progress value={capacityData.totalMemoryUsage} className="h-2" />
              </div>
              
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>网络负载</span>
                  <span>{capacityData.avgNetworkLoad}%</span>
                </div>
                <Progress value={capacityData.avgNetworkLoad} className="h-2" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* SLA达成情况 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="h-5 w-5" />
              SLA达成情况
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {slaData.map(item => (
                <div key={item.name} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">{item.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{item.sla.toFixed(2)}%</span>
                      <Badge 
                        variant={item.status === 'achieved' ? 'default' : 
                                item.status === 'warning' ? 'secondary' : 'destructive'}
                        className="text-xs"
                      >
                        {item.status === 'achieved' ? '达标' : 
                         item.status === 'warning' ? '警告' : '未达标'}
                      </Badge>
                    </div>
                  </div>
                  <div className="relative">
                    <Progress value={item.sla} className="h-2" />
                    <div 
                      className="absolute top-0 w-0.5 h-2 bg-red-500"
                      style={{ left: `${item.target}%` }}
                      title={`目标: ${item.target}%`}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 成本效率分析 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <DollarSign className="h-5 w-5" />
              成本效率分析
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={costEfficiencyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip 
                  content={({ active, payload, label }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      return (
                        <div className="bg-white p-3 border rounded shadow">
                          <p className="font-medium">{label}</p>
                          <p>月电费: ¥{data.powerCost.toLocaleString()}</p>
                          <p>单服务器成本: ¥{data.costPerServer}</p>
                          <p>效率指数: {data.efficiency}</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Bar dataKey="costPerServer" fill="#8884d8" name="单服务器成本" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* 业务分布概览 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              业务分布概览
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={businessDistribution}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  dataKey="instances"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {businessDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* 历史趋势概览 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            历史趋势概览（过去7天）
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area 
                type="monotone" 
                dataKey="avgCpuUsage" 
                stackId="1" 
                stroke="#8884d8" 
                fill="#8884d8" 
                fillOpacity={0.6}
                name="平均CPU使用率%"
              />
              <Area 
                type="monotone" 
                dataKey="avgMemoryUsage" 
                stackId="2" 
                stroke="#82ca9d" 
                fill="#82ca9d" 
                fillOpacity={0.6}
                name="平均内存使用率%"
              />
              <Area 
                type="monotone" 
                dataKey="networkLoad" 
                stackId="3" 
                stroke="#ffc658" 
                fill="#ffc658" 
                fillOpacity={0.6}
                name="网络负载%"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}