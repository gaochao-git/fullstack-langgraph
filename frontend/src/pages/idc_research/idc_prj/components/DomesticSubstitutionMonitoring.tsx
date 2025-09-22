import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { mockHardwareProducts, domesticSubstitutionMetrics, substitutionPlans, hardwareIdcNameMap, categoryNames } from '../data/hardwareData';
import { IDCData } from '../types/idc';
import { Flag, Target, TrendingUp, AlertTriangle, CheckCircle, XCircle, Zap, Shield, Database, Server } from 'lucide-react';

interface DomesticSubstitutionMonitoringProps {
  selectedIDCs: IDCData[];
}

export function DomesticSubstitutionMonitoring({ selectedIDCs }: DomesticSubstitutionMonitoringProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'overview' | 'detailed' | 'planning'>('overview');

  // 获取产品类别图标
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'server':
        return <Server className="h-4 w-4" />;
      case 'network':
        return <Zap className="h-4 w-4" />;
      case 'storage':
        return <Database className="h-4 w-4" />;
      case 'security':
        return <Shield className="h-4 w-4" />;
      default:
        return <Server className="h-4 w-4" />;
    }
  };

  // 获取优先级颜色
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
        return 'text-green-500';
      default:
        return 'text-gray-500';
    }
  };

  // 过滤数据
  const filteredProducts = selectedCategory === 'all' 
    ? mockHardwareProducts 
    : mockHardwareProducts.filter(product => product.category === selectedCategory);

  const filteredMetrics = selectedCategory === 'all'
    ? domesticSubstitutionMetrics
    : domesticSubstitutionMetrics.filter(metric => 
        Object.keys(categoryNames).find(key => categoryNames[key] === metric.category) === selectedCategory
      );

  // 按IDC分组的替代率数据
  const idcSubstitutionData = selectedIDCs.length > 0 ? selectedIDCs.map(idc => {
    const idcProducts = mockHardwareProducts.filter(product => product.idcId === idc.id);
    const categories = Object.keys(categoryNames);
    
    const categoryData = categories.reduce((acc, category) => {
      const categoryProducts = idcProducts.filter(p => p.category === category);
      const totalCount = categoryProducts.reduce((sum, p) => sum + p.quantity, 0);
      const domesticCount = categoryProducts.filter(p => p.isDomestic).reduce((sum, p) => sum + p.quantity, 0);
      const substitutionRate = totalCount > 0 ? (domesticCount / totalCount) * 100 : 0;
      
      acc[categoryNames[category]] = Math.round(substitutionRate * 10) / 10;
      return acc;
    }, {} as Record<string, number>);

    return {
      name: idc.name.replace('数据中心', ''),
      ...categoryData,
    };
  }) : [];

  // 品牌分布数据（仅显示前8个品牌）
  const brandData = filteredMetrics.length > 0 
    ? [...filteredMetrics[0].brands]
        .sort((a, b) => b.count - a.count)
        .slice(0, 8)
        .map(brand => ({
          name: brand.brand,
          count: brand.count,
          percentage: brand.percentage,
          isDomestic: brand.isDomestic,
          color: brand.isDomestic ? '#22c55e' : '#ef4444',
        }))
    : [];

  // 故障率比较数据
  const failureRateData = domesticSubstitutionMetrics.map(metric => ({
    category: metric.category,
    domestic: metric.domesticFailureRate,
    imported: metric.importedFailureRate,
    average: metric.avgFailureRate,
  }));

  // 雷达图数据（替代率概览）
  const radarData = domesticSubstitutionMetrics.map(metric => ({
    category: metric.category,
    substitutionRate: metric.substitutionRate,
    target: 70, // 目标替代率
  }));

  // 计算总体统计
  const totalStats = {
    totalProducts: mockHardwareProducts.reduce((sum, p) => sum + p.quantity, 0),
    domesticProducts: mockHardwareProducts.filter(p => p.isDomestic).reduce((sum, p) => sum + p.quantity, 0),
    categories: Object.keys(categoryNames).length,
    avgSubstitutionRate: Math.round(domesticSubstitutionMetrics.reduce((sum, m) => sum + m.substitutionRate, 0) / domesticSubstitutionMetrics.length * 10) / 10,
  };

  return (
    <div className="space-y-6">
      {/* 控制面板 */}
      <div className="flex flex-wrap items-center gap-4">
        <Select value={selectedCategory} onValueChange={setSelectedCategory}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="选择产品类别" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">所有类别</SelectItem>
            {Object.entries(categoryNames).map(([key, name]) => (
              <SelectItem key={key} value={key}>{name}</SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'overview' | 'detailed' | 'planning')}>
          <TabsList>
            <TabsTrigger value="overview">总体概览</TabsTrigger>
            <TabsTrigger value="detailed">详细分析</TabsTrigger>
            <TabsTrigger value="planning">替代规划</TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* 总体统计 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Flag className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-sm text-muted-foreground">总产品数量</p>
                <p className="text-2xl font-bold">{totalStats.totalProducts.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-sm text-muted-foreground">国产产品数量</p>
                <p className="text-2xl font-bold">{totalStats.domesticProducts.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <Target className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-sm text-muted-foreground">平均替代率</p>
                <p className="text-2xl font-bold">{totalStats.avgSubstitutionRate}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-purple-500" />
              <div>
                <p className="text-sm text-muted-foreground">产品类别</p>
                <p className="text-2xl font-bold">{totalStats.categories}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={viewMode}>
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 国产替代率雷达图 */}
            <Card>
              <CardHeader>
                <CardTitle>国产替代率概览</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="category" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="当前替代率"
                      dataKey="substitutionRate"
                      stroke="#8884d8"
                      fill="#8884d8"
                      fillOpacity={0.6}
                    />
                    <Radar
                      name="目标替代率"
                      dataKey="target"
                      stroke="#82ca9d"
                      fill="#82ca9d"
                      fillOpacity={0.3}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 各类别替代率柱状图 */}
            <Card>
              <CardHeader>
                <CardTitle>各类别国产替代率</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={domesticSubstitutionMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Bar dataKey="substitutionRate" fill="#8884d8" name="替代率%" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* 品牌分布饼图 */}
          {brandData.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>品牌分布情况 {selectedCategory !== 'all' && `- ${categoryNames[selectedCategory]}`}</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={brandData}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="count"
                      label={({ name, percentage }) => `${name}: ${percentage.toFixed(1)}%`}
                    >
                      {brandData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="detailed" className="space-y-6">
          {/* 故障率对比分析 */}
          <Card>
            <CardHeader>
              <CardTitle>故障率对比分析</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={failureRateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="domestic" fill="#22c55e" name="国产产品故障率" />
                  <Bar dataKey="imported" fill="#ef4444" name="进口产品故障率" />
                  <Bar dataKey="average" fill="#8884d8" name="平均故障率" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* 跨数据中心替代率比较 */}
          {selectedIDCs.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>跨数据中心替代率比较</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={idcSubstitutionData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="服务器" fill="#8884d8" name="服务器" />
                    <Bar dataKey="网络设备" fill="#82ca9d" name="网络设备" />
                    <Bar dataKey="存储设备" fill="#ffc658" name="存储设备" />
                    <Bar dataKey="操作系统" fill="#ff7300" name="操作系统" />
                    <Bar dataKey="数据库" fill="#00ff88" name="数据库" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}

          {/* 详细产品列表 */}
          <Card>
            <CardHeader>
              <CardTitle>产品类别详细信息</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {filteredMetrics.map((metric) => (
                  <div key={metric.category} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <h4 className="font-medium">{metric.category}</h4>
                        <Badge variant="outline">
                          {metric.totalCount} 个产品
                        </Badge>
                        <Badge 
                          className={metric.substitutionRate >= 50 ? 'bg-green-100 text-green-800' : 'bg-orange-100 text-orange-800'}
                        >
                          替代率 {metric.substitutionRate}%
                        </Badge>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <p className="text-sm font-medium mb-2">替代进度</p>
                        <Progress value={metric.substitutionRate} className="h-2" />
                        <p className="text-xs text-muted-foreground mt-1">
                          {metric.domesticCount}/{metric.totalCount} 个国产产品
                        </p>
                      </div>

                      <div>
                        <p className="text-sm font-medium mb-2">故障率对比</p>
                        <div className="space-y-1">
                          <div className="flex justify-between text-xs">
                            <span>国产: {metric.domesticFailureRate}</span>
                            <span>进口: {metric.importedFailureRate}</span>
                          </div>
                          <div className="text-xs text-muted-foreground">
                            平均: {metric.avgFailureRate}
                          </div>
                        </div>
                      </div>

                      <div>
                        <p className="text-sm font-medium mb-2">主要品牌</p>
                        <div className="flex flex-wrap gap-1">
                          {metric.brands.slice(0, 3).map((brand) => (
                            <Badge 
                              key={brand.brand}
                              variant="outline" 
                              className={`text-xs ${brand.isDomestic ? 'border-green-500 text-green-700' : 'border-orange-500 text-orange-700'}`}
                            >
                              {brand.brand}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="planning" className="space-y-6">
          {/* 替代规划概览 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {substitutionPlans.map((plan) => (
              <Card key={plan.category}>
                <CardHeader>
                  <CardTitle className="flex items-center justify-between">
                    <span>{plan.category}</span>
                    <Badge 
                      className={`${getPriorityColor(plan.priority)} border-current`}
                      variant="outline"
                    >
                      {plan.priority === 'high' ? '高优先级' : plan.priority === 'medium' ? '中优先级' : '低优先级'}
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <div className="flex justify-between text-sm mb-2">
                      <span>当前进度</span>
                      <span>{plan.currentRate}%</span>
                    </div>
                    <Progress value={plan.currentRate} className="h-2" />
                    <div className="flex justify-between text-xs text-muted-foreground mt-1">
                      <span>目标: {plan.targetRate}%</span>
                      <span>期限: {plan.timeline}</span>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm font-medium mb-2">主要挑战</p>
                    <ul className="space-y-1">
                      {plan.challenges.slice(0, 2).map((challenge, index) => (
                        <li key={index} className="text-xs text-muted-foreground flex items-start gap-1">
                          <AlertTriangle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                          {challenge}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <p className="text-sm font-medium mb-2">建议措施</p>
                    <ul className="space-y-1">
                      {plan.recommendations.slice(0, 2).map((recommendation, index) => (
                        <li key={index} className="text-xs text-muted-foreground flex items-start gap-1">
                          <CheckCircle className="h-3 w-3 mt-0.5 flex-shrink-0" />
                          {recommendation}
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* 替代时间线 */}
          <Card>
            <CardHeader>
              <CardTitle>国产替代时间线</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {substitutionPlans
                  .sort((a, b) => new Date(a.timeline.replace('年', '/').replace('月', '/').replace('底', '').replace('中', '')).getTime() - 
                              new Date(b.timeline.replace('年', '/').replace('月', '/').replace('底', '').replace('中', '')).getTime())
                  .map((plan, index) => (
                  <div key={plan.category} className="flex items-start gap-4">
                    <div className="flex flex-col items-center">
                      <div className={`w-4 h-4 rounded-full border-2 ${
                        plan.priority === 'high' ? 'bg-red-500 border-red-500' :
                        plan.priority === 'medium' ? 'bg-yellow-500 border-yellow-500' :
                        'bg-green-500 border-green-500'
                      }`} />
                      {index < substitutionPlans.length - 1 && (
                        <div className="w-0.5 h-16 bg-border mt-2" />
                      )}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <h4 className="font-medium">{plan.category}</h4>
                        <span className="text-sm text-muted-foreground">{plan.timeline}</span>
                      </div>
                      <div className="flex items-center gap-4 mb-2">
                        <span className="text-sm">
                          {plan.currentRate}% → {plan.targetRate}%
                        </span>
                        <Progress value={(plan.currentRate / plan.targetRate) * 100} className="h-1 flex-1" />
                      </div>
                      <p className="text-xs text-muted-foreground">
                        关键挑战: {plan.challenges[0]}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}