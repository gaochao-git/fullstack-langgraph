import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, ScatterChart, Scatter } from 'recharts';
import { mockApplications, businessTypes, idcNameMap } from '../data/applicationData';
import { IDCData, Application, ApplicationService } from '../types/idc';
import { Server, Database, Layers, MessageSquare, Globe, AlertCircle, CheckCircle, TrendingUp, Activity } from 'lucide-react';

interface ApplicationMonitoringProps {
  selectedIDCs: IDCData[];
}

export function ApplicationMonitoring({ selectedIDCs }: ApplicationMonitoringProps) {
  const [selectedBusiness, setSelectedBusiness] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'business' | 'idc'>('business');

  // 获取服务类型图标
  const getServiceIcon = (type: string) => {
    switch (type) {
      case 'app':
        return <Server className="h-4 w-4" />;
      case 'database':
        return <Database className="h-4 w-4" />;
      case 'cache':
        return <Layers className="h-4 w-4" />;
      case 'mq':
        return <MessageSquare className="h-4 w-4" />;
      case 'gateway':
        return <Globe className="h-4 w-4" />;
      default:
        return <Server className="h-4 w-4" />;
    }
  };

  // 获取服务类型颜色
  const getServiceColor = (type: string) => {
    const colors = {
      app: '#8884d8',
      database: '#82ca9d',
      cache: '#ffc658',
      mq: '#ff7300',
      gateway: '#00ff88',
    };
    return colors[type as keyof typeof colors] || '#8884d8';
  };

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-500';
      case 'warning':
        return 'text-yellow-500';
      case 'critical':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  // 过滤应用程序
  const filteredApplications = selectedBusiness === 'all' 
    ? mockApplications 
    : mockApplications.filter(app => app.businessType === selectedBusiness);

  // 按业务类型分组的数据
  const businessData = businessTypes.map(businessType => {
    const apps = mockApplications.filter(app => app.businessType === businessType);
    const allServices = apps.flatMap(app => app.services);
    
    if (allServices.length === 0) return null;

    const avgMetrics = {
      cpuUsage: allServices.reduce((sum, s) => sum + s.metrics.cpuUsage, 0) / allServices.length,
      memoryUsage: allServices.reduce((sum, s) => sum + s.metrics.memoryUsage, 0) / allServices.length,
      responseTime: allServices.reduce((sum, s) => sum + s.metrics.responseTime, 0) / allServices.length,
      errorRate: allServices.reduce((sum, s) => sum + s.metrics.errorRate, 0) / allServices.length,
      availability: allServices.reduce((sum, s) => sum + s.metrics.availability, 0) / allServices.length,
    };

    return {
      name: businessType,
      ...avgMetrics,
      totalInstances: allServices.reduce((sum, s) => sum + s.instances, 0),
      idcCount: new Set(apps.flatMap(app => app.deployedIDCs)).size,
    };
  }).filter(Boolean);

  // 按数据中心分组的数据
  const idcData = selectedIDCs.length > 0 ? selectedIDCs.map(idc => {
    const services = mockApplications.flatMap(app => 
      app.services.filter(service => service.idcId === idc.id)
    );

    if (services.length === 0) return null;

    const avgMetrics = {
      cpuUsage: services.reduce((sum, s) => sum + s.metrics.cpuUsage, 0) / services.length,
      memoryUsage: services.reduce((sum, s) => sum + s.metrics.memoryUsage, 0) / services.length,
      responseTime: services.reduce((sum, s) => sum + s.metrics.responseTime, 0) / services.length,
      errorRate: services.reduce((sum, s) => sum + s.metrics.errorRate, 0) / services.length,
      availability: services.reduce((sum, s) => sum + s.metrics.availability, 0) / services.length,
    };

    return {
      name: idc.name.replace('数据中心', ''),
      ...avgMetrics,
      totalServices: services.length,
      totalInstances: services.reduce((sum, s) => sum + s.instances, 0),
    };
  }).filter(Boolean) : [];

  // 服务类型分布数据
  const serviceTypeData = mockApplications.flatMap(app => app.services)
    .reduce((acc, service) => {
      acc[service.type] = (acc[service.type] || 0) + service.instances;
      return acc;
    }, {} as Record<string, number>);

  const pieData = Object.entries(serviceTypeData).map(([type, count]) => ({
    name: type,
    value: count,
    color: getServiceColor(type),
  }));

  // 跨数据中心业务健康度数据
  const crossIDCHealthData = mockApplications
    .filter(app => app.isShared && app.deployedIDCs.length > 1)
    .map(app => {
      const servicesByIDC = app.deployedIDCs.map(idcId => {
        const services = app.services.filter(s => s.idcId === idcId);
        const avgAvailability = services.length > 0 
          ? services.reduce((sum, s) => sum + s.metrics.availability, 0) / services.length 
          : 0;
        return {
          idc: idcNameMap[idcId]?.replace('数据中心', '') || idcId,
          availability: avgAvailability,
        };
      });

      return {
        business: app.businessType,
        ...servicesByIDC.reduce((acc, item, index) => {
          acc[item.idc] = item.availability;
          return acc;
        }, {} as Record<string, number>),
      };
    });

  return (
    <div className="space-y-6">
      {/* 控制面板 */}
      <div className="flex flex-wrap items-center gap-4">
        <Select value={selectedBusiness} onValueChange={setSelectedBusiness}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="选择业务类型" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有业务</SelectItem>
            {businessTypes.map(type => (
              <SelectItem key={type} value={type}>{type}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'business' | 'idc')}>
          <TabsList>
            <TabsTrigger value="business">按业务分析</TabsTrigger>
            <TabsTrigger value="idc">按数据中心分析</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* 应用概览 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Activity className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">总应用数</p>
                <p className="text-2xl font-bold">{filteredApplications.length}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">总服务实例</p>
                <p className="text-2xl font-bold">
                  {filteredApplications.flatMap(app => app.services).reduce((sum, s) => sum + s.instances, 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">健康应用</p>
                <p className="text-2xl font-bold">
                  {filteredApplications.filter(app => app.status === 'healthy').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-sm text-muted-foreground">异常应用</p>
                <p className="text-2xl font-bold">
                  {filteredApplications.filter(app => app.status !== 'healthy').length}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={viewMode}>
        <TabsContent value="business" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 业务性能比较 */}
            <Card>
              <CardHeader>
                <CardTitle>业务性能比较</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={businessData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="cpuUsage" fill="#8884d8" name="CPU使用率%" />
                    <Bar dataKey="memoryUsage" fill="#82ca9d" name="内存使用率%" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 服务类型分布 */}
            <Card>
              <CardHeader>
                <CardTitle>服务类型分布</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, value }) => `${name}: ${value}`}
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* 业务响应时间与错误率 */}
          <Card>
            <CardHeader>
              <CardTitle>业务响应时间与错误率分析</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <ScatterChart data={businessData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="responseTime" name="响应时间(ms)" />
                  <YAxis dataKey="errorRate" name="错误率%" />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3 3' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="bg-white p-3 border rounded shadow">
                            <p className="font-medium">{data.name}</p>
                            <p>响应时间: {data.responseTime.toFixed(1)}ms</p>
                            <p>错误率: {data.errorRate.toFixed(2)}%</p>
                            <p>可用性: {data.availability.toFixed(2)}%</p>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Scatter dataKey="errorRate" fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* 跨数据中心业务健康度 */}
          {crossIDCHealthData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>跨数据中心业务可用性比较</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={crossIDCHealthData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="business" />
                    <YAxis domain={[90, 100]} />
                    <Tooltip />
                    <Bar dataKey="北京" fill="#8884d8" name="北京" />
                    <Bar dataKey="上海" fill="#82ca9d" name="上海" />
                    <Bar dataKey="广州" fill="#ffc658" name="广州" />
                    <Bar dataKey="深圳" fill="#ff7300" name="深圳" />
                    <Bar dataKey="成都" fill="#00ff88" name="成都" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="idc" className="space-y-6">
          {selectedIDCs.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <p className="text-muted-foreground">请先选择数据中心进行应用监控分析</p>
              </CardContent>
            </Card>
          ) : (
            <>
              {/* 数据中心应用性能比较 */}
              <Card>
                <CardHeader>
                  <CardTitle>数据中心应用性能比较</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={idcData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis />
                      <Tooltip />
                      <Bar dataKey="cpuUsage" fill="#8884d8" name="CPU使用率%" />
                      <Bar dataKey="memoryUsage" fill="#82ca9d" name="内存使用率%" />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* 数据中心可用性趋势 */}
              <Card>
                <CardHeader>
                  <CardTitle>数据中心应用可用性</CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={idcData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[95, 100]} />
                      <Tooltip />
                      <Line 
                        type="monotone" 
                        dataKey="availability" 
                        stroke="#8884d8" 
                        strokeWidth={3}
                        name="可用性%"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>
      </Tabs>

      {/* 应用详细列表 */}
      <Card>
        <CardHeader>
          <CardTitle>应用详细信息</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {filteredApplications.map(app => (
              <div key={app.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <h4 className="font-medium">{app.name}</h4>
                    <Badge variant="outline">{app.businessType}</Badge>
                    <Badge variant="secondary">v{app.version}</Badge>
                    <Badge className={app.isShared ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}>
                      {app.isShared ? '跨数据中心' : '单数据中心'}
                    </Badge>
                  </div>
                  <div className={`flex items-center gap-1 ${getStatusColor(app.status)}`}>
                    {app.status === 'healthy' ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <AlertCircle className="h-4 w-4" />
                    )}
                    <span className="text-sm capitalize">{app.status}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {app.services
                    .filter(service => selectedIDCs.length === 0 || selectedIDCs.some(idc => idc.id === service.idcId))
                    .map(service => (
                    <div key={service.id} className="p-3 bg-muted rounded-lg">
                      <div className="flex items-center gap-2 mb-2">
                        {getServiceIcon(service.type)}
                        <span className="font-medium text-sm">{service.name}</span>
                        <Badge variant="outline" className="text-xs">
                          {idcNameMap[service.idcId]?.replace('数据中心', '') || service.idcId}
                        </Badge>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>实例: {service.instances}</div>
                        <div>CPU: {service.metrics.cpuUsage.toFixed(1)}%</div>
                        <div>内存: {service.metrics.memoryUsage.toFixed(1)}%</div>
                        <div>可用性: {service.metrics.availability.toFixed(1)}%</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}