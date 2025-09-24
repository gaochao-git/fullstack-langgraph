import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { mockIDCData } from '../data/mockData';
import { mockApplications, businessTypes } from '../data/applicationData';
import { mockServerFailureData, idcMapping, brandCategories } from '../data/serverFailureData';
import { Server, Target, TrendingUp, DollarSign, Activity, AlertTriangle, Wrench, RotateCcw } from 'lucide-react';

export function IDCOverviewDashboard() {
  // 固定机房编码顺序，保证各处渲染稳定
  const IDC_CODES = useMemo(() => ["BJ1", "BJ2", "SH1", "SH2", "SZ1", "SZ2"] as const, []);

  // 排序后的故障数据（按月份升序）
  const sortedFailureData = useMemo(
    () => [...mockServerFailureData.data].sort((a, b) => a.month - b.month),
    [],
  );

  // 构造折线图数据
  const monthlyFailureTrendData = useMemo(() => {
    return sortedFailureData.map((monthData) => {
      const monthStr = monthData.month.toString();
      const formattedMonth = `${monthStr.slice(0, 4)}-${monthStr.slice(4)}`;
      const result: Record<string, any> = { month: formattedMonth };

      IDC_CODES.forEach((code) => {
        const servers = (monthData as any)[code] || [];
        const totalServers = (servers as any[]).reduce((sum, s) => sum + (s?.count || 0), 0);
        const totalTroubles = (servers as any[]).reduce((sum, s) => sum + (s?.trouble || 0), 0);
        const failureRate = totalServers > 0 ? Number(((totalTroubles / totalServers) * 100).toFixed(2)) : 0;
        (result as any)[code] = failureRate;
      });

      return result;
    });
  }, [sortedFailureData, IDC_CODES]);

  // 默认选中最新月份（最后一条）
  const defaultMonthStr = useMemo(() => {
    const latest = sortedFailureData[sortedFailureData.length - 1]?.month;
    if (!latest) return '';
    const s = latest.toString();
    return `${s.slice(0, 4)}-${s.slice(4)}`;
  }, [sortedFailureData]);

  const [selectedMonth, setSelectedMonth] = useState<string>(defaultMonthStr);

  // 当前选中月份的原始数据
  const selectedMonthData = useMemo(() => {
    const numeric = Number((selectedMonth || defaultMonthStr).replace('-', ''));
    return (
      sortedFailureData.find((d) => d.month === numeric) ||
      sortedFailureData[sortedFailureData.length - 1]
    );
  }, [selectedMonth, defaultMonthStr, sortedFailureData]);

  // 机房故障详情（随月份切换）
  const failureOverviewData = useMemo(() => {
    return IDC_CODES.map((code) => {
      const arr = ((selectedMonthData as any)[code] || []) as any[];
      const totalServers = arr.reduce((sum, server) => sum + (server?.count || 0), 0);
      const totalTroubles = arr.reduce((sum, server) => sum + (server?.trouble || 0), 0);
      const failureRate = totalServers > 0 ? (totalTroubles / totalServers) * 100 : 0;

      const domesticServers = arr
        .filter((s) => brandCategories[s.brand] === 'domestic')
        .reduce((sum, s) => sum + (s?.count || 0), 0);
      const foreignServers = arr
        .filter((s) => brandCategories[s.brand] === 'foreign')
        .reduce((sum, s) => sum + (s?.count || 0), 0);
      const domesticTroubles = arr
        .filter((s) => brandCategories[s.brand] === 'domestic')
        .reduce((sum, s) => sum + (s?.trouble || 0), 0);
      const foreignTroubles = arr
        .filter((s) => brandCategories[s.brand] === 'foreign')
        .reduce((sum, s) => sum + (s?.trouble || 0), 0);

      const codeStr = code as unknown as string;
      return {
        idc: idcMapping[codeStr as keyof typeof idcMapping] || codeStr,
        code: codeStr,
        hasData: arr.length > 0,
        totalServers,
        totalTroubles,
        failureRate: Number(failureRate.toFixed(2)),
        domesticServers,
        foreignServers,
        domesticTroubles,
        foreignTroubles,
        domesticFailureRate: domesticServers > 0 ? Number(((domesticTroubles / domesticServers) * 100).toFixed(2)) : 0,
        foreignFailureRate: foreignServers > 0 ? Number(((foreignTroubles / foreignServers) * 100).toFixed(2)) : 0,
      };
    });
  }, [selectedMonthData, IDC_CODES]);

  // 故障类型统计（随月份切换）
  const failureTypeStats = useMemo(() => {
    const typeMap: Record<string, number> = {};
    Object.values(selectedMonthData).forEach((servers) => {
      if (Array.isArray(servers)) {
        servers.forEach((server) => {
          server.tb_detail.forEach((detail: any) => {
            typeMap[detail.name] = (typeMap[detail.name] || 0) + detail.number;
          });
        });
      }
    });
    return Object.entries(typeMap)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count);
  }, [selectedMonthData]);

  // 品牌故障率对比（随月份切换）
  const brandFailureComparison = useMemo(() => {
    const brandMap: Record<string, { count: number; trouble: number }> = {};
    Object.values(selectedMonthData).forEach((servers) => {
      if (Array.isArray(servers)) {
        servers.forEach((server) => {
          if (!brandMap[server.brand]) {
            brandMap[server.brand] = { count: 0, trouble: 0 };
          }
          brandMap[server.brand].count += server.count;
          brandMap[server.brand].trouble += server.trouble;
        });
      }
    });
    return Object.entries(brandMap)
      .map(([brand, data]) => ({
        brand,
        count: data.count,
        trouble: data.trouble,
        failureRate: Number(((data.trouble / data.count) * 100).toFixed(2)),
        category: brandCategories[brand] || 'unknown',
      }))
      .sort((a, b) => b.failureRate - a.failureRate);
  }, [selectedMonthData]);

  // 整体容量概览数据
  const capacityData = {
    totalServers: mockIDCData.reduce((sum, idc) => sum + idc.serverCount, 0),
    totalCpuUsage: Math.round(
      mockIDCData.reduce((sum, idc) => sum + idc.cpuUsage * idc.serverCount, 0) /
        mockIDCData.reduce((sum, idc) => sum + idc.serverCount, 0)
    ),
    totalMemoryUsage: Math.round(
      mockIDCData.reduce((sum, idc) => sum + idc.memoryUsage * idc.serverCount, 0) /
        mockIDCData.reduce((sum, idc) => sum + idc.serverCount, 0)
    ),
    avgNetworkLoad: Math.round(
      mockIDCData.reduce((sum, idc) => sum + idc.networkLoad, 0) / mockIDCData.length
    ),
    avgPowerUsage: Math.round(
      mockIDCData.reduce((sum, idc) => sum + idc.powerUsage, 0) / mockIDCData.length
    ),
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
    powerCost: Math.round(idc.powerUsage * 0.8 * 24 * 30),
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
    const totalInstances = apps.reduce(
      (sum, app) => sum + app.services.reduce((serviceSum, service) => serviceSum + service.instances, 0),
      0
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

  // 故障率徽标底色（确保明显可见）
  const rateBadgeClass = (rate: number) => {
    if (rate < 5) return 'bg-green-500 text-white';
    if (rate < 10) return 'bg-amber-500 text-white';
    return 'bg-red-500 text-white';
  };

  return (
    <div className="space-y-6">
      {/* 服务器故障分析（统一大框体） */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            服务器故障分析
          </CardTitle>
        </CardHeader>
        <CardContent>
          {/* 当前月份信息 + 重置按钮 */}
          <div className="flex items-center gap-3 flex-wrap text-sm text-muted-foreground mb-4">
            <div>
              当前月份：<span className="font-medium text-foreground">{selectedMonth}</span>（点击折线图上的点可切换）
            </div>
            <Button
              variant="outline"
              size="sm"
              className="ml-auto"
              onClick={() => setSelectedMonth(defaultMonthStr)}
            >
              <RotateCcw className="h-4 w-4" /> 重置为最新
            </Button>
          </div>

          {/* 上半部分：趋势 + 机房详情 */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 机房故障率趋势对比（12个月） */}
            <div>
              <h4 className="font-medium mb-4">机房故障率趋势对比（近12个月）</h4>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart
                  data={monthlyFailureTrendData}
                  onClick={(state: any) => {
                    const label = state?.activeLabel as string | undefined;
                    if (label) setSelectedMonth(label);
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis label={{ value: '故障率(%)', angle: -90, position: 'insideLeft' }} />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        return (
                          <div className="bg-white p-3 border rounded shadow">
                            <p className="font-medium">{label}</p>
                            {payload.map((entry, index) => (
                              <p key={index} style={{ color: entry.color }}>
                                {idcMapping[entry.dataKey as keyof typeof idcMapping] || entry.dataKey}: {entry.value}%
                              </p>
                            ))}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Line type="monotone" dataKey="BJ1" stroke="#8884d8" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} name="北京数据中心1" />
                  <Line type="monotone" dataKey="BJ2" stroke="#82ca9d" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} name="北京数据中心2" />
                  <Line type="monotone" dataKey="SH1" stroke="#ffc658" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} name="上海数据中心1" />
                  <Line type="monotone" dataKey="SH2" stroke="#ff7300" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} name="上海数据中心2" />
                  <Line type="monotone" dataKey="SZ1" stroke="#00ff88" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} name="深圳数据中心1" />
                  <Line type="monotone" dataKey="SZ2" stroke="#ff6b6b" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 5 }} name="深圳数据中心2" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* 机房详细故障信息 */}
            <div>
              <h4 className="font-medium mb-4">机房故障详情（{selectedMonth}）</h4>
              {/* 月度总览 */}
              {(() => {
                const totals = IDC_CODES.reduce(
                  (acc, code) => {
                    const arr = ((selectedMonthData as any)[code] || []) as any[];
                    const s = arr.reduce((sum, it) => sum + (it?.count || 0), 0);
                    const t = arr.reduce((sum, it) => sum + (it?.trouble || 0), 0);
                    acc.totalServers += s;
                    acc.totalTroubles += t;
                    return acc;
                  },
                  { totalServers: 0, totalTroubles: 0 },
                );
                const rate = totals.totalServers > 0 ? (totals.totalTroubles / totals.totalServers) * 100 : 0;
                return (
                  <div className="p-3 mb-3 rounded-lg border bg-card/50 flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      <span className="font-medium text-foreground mr-2">月度总览</span>
                      总服务器: <span className="text-foreground">{totals.totalServers}</span> 台，
                      故障数: <span className="text-foreground">{totals.totalTroubles}</span> 台
                    </div>
                    <Badge className={rateBadgeClass(rate)}>
                      {rate.toFixed(1)}% 故障率
                    </Badge>
                  </div>
                );
              })()}
              <div className="space-y-3 max-h-80 overflow-y-auto">
                {failureOverviewData.map(item => (
                  <div key={item.code} className="p-3 rounded-lg border" style={{ backgroundColor: 'var(--color-muted)' }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium">{item.idc}</span>
                      {item.hasData ? (
                        <Badge className={rateBadgeClass(item.failureRate)}>
                          {item.failureRate.toFixed(1)}% 故障率
                        </Badge>
                      ) : (
                        <Badge variant="outline">无数据</Badge>
                      )}
                    </div>
                    {item.hasData ? (
                      <div className="grid grid-cols-2 gap-2 text-sm text-muted-foreground">
                        <div>总服务器: {item.totalServers}台</div>
                        <div>故障数: {item.totalTroubles}台</div>
                        <div>国产: {item.domesticServers}台 ({item.domesticFailureRate}%)</div>
                        <div>进口: {item.foreignServers}台 ({item.foreignFailureRate}%)</div>
                      </div>
                    ) : (
                      <div className="text-sm text-muted-foreground">本月该机房无数据</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          {/* 下半部分：故障类型分布 + 品牌故障率对比（统一框体内） */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
            <div className="rounded-lg border p-4">
              <h4 className="font-medium mb-4 flex items-center gap-2">
                <Wrench className="h-5 w-5" />
                故障类型分布
              </h4>
              {failureTypeStats.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={failureTypeStats}
                      cx="50%"
                      cy="50%"
                      outerRadius={80}
                      dataKey="count"
                      label={({ type, count }) => `${type}: ${count}次`}
                    >
                      {failureTypeStats.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#00ff88'][index % 5]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div className="min-h-[250px] flex items-center justify-center text-muted-foreground">
                  本月暂无数据
                </div>
              )}
            </div>

            <div className="rounded-lg border p-4">
              <h4 className="font-medium mb-4 flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                品牌故障率对比
              </h4>
              {brandFailureComparison.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={brandFailureComparison}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="brand" />
                    <YAxis />
                    <Tooltip
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          const data = payload[0].payload as any;
                          return (
                            <div className="bg-white p-3 border rounded shadow">
                              <p className="font-medium">{data.brand}</p>
                              <p>总数: {data.count}台</p>
                              <p>故障: {data.trouble}台</p>
                              <p>故障率: {data.failureRate}%</p>
                              <p>类型: {data.category === 'domestic' ? '国产' : '进口'}</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                    <Bar dataKey="failureRate" name="故障率%">
                      {brandFailureComparison.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.category === 'domestic' ? '#22c55e' : '#3b82f6'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="min-h-[250px] flex items-center justify-center text-muted-foreground">
                  本月暂无数据
                </div>
              )}
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
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{item.name}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-sm">{item.sla.toFixed(2)}%</span>
                      <Badge variant={item.status === 'achieved' ? 'default' : item.status === 'warning' ? 'secondary' : 'destructive'}>
                        {item.status === 'achieved' ? '达标' : item.status === 'warning' ? '警告' : '未达标'}
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
  // 仅使用主题变量控制颜色（不再使用兜底类）
