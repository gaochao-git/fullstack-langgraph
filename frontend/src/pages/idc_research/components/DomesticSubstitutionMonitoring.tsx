import React, { useMemo, useState } from 'react';
import { Card, Badge, Progress, Tabs, Select, Alert, Row, Col, Statistic } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';
import { mockHardwareProducts, domesticSubstitutionMetrics, substitutionPlans, hardwareIdcNameMap, categoryNames } from '../data/hardwareData';
import { IDCData } from '../types/idc';
import { FlagOutlined, AimOutlined, RiseOutlined, WarningOutlined, CheckCircleOutlined, CloseCircleOutlined, ThunderboltOutlined, SafetyOutlined, DatabaseOutlined, CloudServerOutlined } from '@ant-design/icons';

const { TabPane } = Tabs;
const { Option } = Select;

interface DomesticSubstitutionMonitoringProps {
  selectedIDCs: IDCData[];
}

export function DomesticSubstitutionMonitoring({ selectedIDCs }: DomesticSubstitutionMonitoringProps) {
  const getCssVar = (name: string, fallback: string) => {
    if (typeof window === 'undefined') return fallback;
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  };

  const colors = useMemo(() => ({
    chart1: getCssVar('--color-chart-1', '#8884d8'),
    chart2: getCssVar('--color-chart-2', '#82ca9d'),
    chart3: getCssVar('--color-chart-3', '#ffc658'),
    chart4: getCssVar('--color-chart-4', '#ff7300'),
    chart5: getCssVar('--color-chart-5', '#00ff88'),
    success: getCssVar('--color-success', '#22c55e'),
    warning: getCssVar('--color-warning', '#f59e0b'),
    destructive: getCssVar('--color-destructive', '#ef4444'),
    primary: getCssVar('--color-primary', '#1890ff'),
    accent: getCssVar('--color-accent', '#722ed1'),
    border: getCssVar('--color-border', '#f0f0f0'),
    muted: getCssVar('--color-muted', '#f0f0f0'),
    mutedFg: getCssVar('--color-muted-foreground', '#8c8c8c'),
  }), []);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'overview' | 'detailed' | 'planning'>('overview');

  // 获取产品类别图标
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'server':
        return <CloudServerOutlined />;
      case 'network':
        return <ThunderboltOutlined />;
      case 'storage':
        return <DatabaseOutlined />;
      case 'security':
        return <SafetyOutlined />;
      default:
        return <CloudServerOutlined />;
    }
  };

  // 获取优先级颜色和类型
  const getPriorityProps = (priority: string) => {
    switch (priority) {
      case 'high':
        return { color: 'error', style: { color: colors.destructive } };
      case 'medium':
        return { color: 'warning', style: { color: colors.warning } };
      case 'low':
        return { color: 'success', style: { color: colors.success } };
      default:
        return { color: 'default', style: { color: colors.mutedFg } };
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
        color: brand.isDomestic ? colors.success : colors.destructive,
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* 控制面板 */}
      <Row gutter={16} align="middle">
        <Col>
          <Select
            value={selectedCategory}
            onChange={setSelectedCategory}
            style={{ width: 200 }}
            placeholder="选择产品类别"
          >
            <Option value="all">所有类别</Option>
            {Object.entries(categoryNames).map(([key, name]) => (
              <Option key={key} value={key}>{name}</Option>
            ))}
          </Select>
        </Col>
        <Col>
          <Tabs activeKey={viewMode} onChange={(key) => setViewMode(key as 'overview' | 'detailed' | 'planning')} type="card">
            <TabPane tab="总体概览" key="overview" />
            <TabPane tab="详细分析" key="detailed" />
            <TabPane tab="替代规划" key="planning" />
          </Tabs>
        </Col>
      </Row>

      {/* 总体统计 */}
      <Row gutter={[16, 16]}>
        <Col lg={6} md={12} xs={24}>
          <Card>
            <Statistic
              title="总产品数量"
              value={totalStats.totalProducts}
              formatter={(value) => value?.toLocaleString()}
              prefix={<FlagOutlined style={{ color: 'var(--color-primary, var(--primary, #1890ff))' }} />}
            />
          </Card>
        </Col>

        <Col lg={6} md={12} xs={24}>
          <Card>
            <Statistic
              title="国产产品数量"
              value={totalStats.domesticProducts}
              formatter={(value) => value?.toLocaleString()}
              prefix={<CheckCircleOutlined style={{ color: 'var(--color-success, var(--success, #22c55e))' }} />}
            />
          </Card>
        </Col>

        <Col lg={6} md={12} xs={24}>
          <Card>
            <Statistic
              title="平均替代率"
              value={totalStats.avgSubstitutionRate}
              suffix="%"
              prefix={<AimOutlined style={{ color: 'var(--color-warning, var(--warning, #f59e0b))' }} />}
            />
          </Card>
        </Col>

        <Col lg={6} md={12} xs={24}>
          <Card>
            <Statistic
              title="产品类别"
              value={totalStats.categories}
              prefix={<RiseOutlined style={{ color: 'var(--color-accent, #722ed1)' }} />}
            />
          </Card>
        </Col>
      </Row>

      {viewMode === 'overview' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          <Row gutter={[24, 24]}>
            {/* 国产替代率雷达图 */}
            <Col lg={12} xs={24}>
              <Card title="国产替代率概览">
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={radarData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="category" />
                    <PolarRadiusAxis angle={90} domain={[0, 100]} />
                    <Radar
                      name="当前替代率"
                      dataKey="substitutionRate"
                      stroke={colors.chart1}
                      fill={colors.chart1}
                      fillOpacity={0.6}
                    />
                    <Radar
                      name="目标替代率"
                      dataKey="target"
                      stroke={colors.chart2}
                      fill={colors.chart2}
                      fillOpacity={0.3}
                    />
                    <Tooltip />
                  </RadarChart>
                </ResponsiveContainer>
              </Card>
            </Col>

            {/* 各类别替代率柱状图 */}
            <Col lg={12} xs={24}>
              <Card title="各类别国产替代率">
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={domesticSubstitutionMetrics}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Bar dataKey="substitutionRate" fill={colors.chart1} name="替代率%" />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </Col>
          </Row>

          {/* 品牌分布饼图 */}
          {brandData.length > 0 && (
            <Card title={`品牌分布情况 ${selectedCategory !== 'all' ? `- ${categoryNames[selectedCategory]}` : ''}`}>
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
            </Card>
          )}
        </div>
      )}

      {viewMode === 'detailed' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 故障率对比分析 */}
          <Card title="故障率对比分析">
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={failureRateData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" angle={-45} textAnchor="end" height={80} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="domestic" fill={colors.success} name="国产产品故障率" />
                <Bar dataKey="imported" fill={colors.destructive} name="进口产品故障率" />
                <Bar dataKey="average" fill={colors.chart1} name="平均故障率" />
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* 跨数据中心替代率比较 */}
          {selectedIDCs.length > 0 && (
            <Card title="跨数据中心替代率比较">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={idcSubstitutionData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="服务器" fill={colors.chart1} name="服务器" />
                  <Bar dataKey="网络设备" fill={colors.chart2} name="网络设备" />
                  <Bar dataKey="存储设备" fill={colors.chart3} name="存储设备" />
                  <Bar dataKey="操作系统" fill={colors.chart4} name="操作系统" />
                  <Bar dataKey="数据库" fill={colors.chart5} name="数据库" />
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}

          {/* 详细产品列表 */}
          <Card title="产品类别详细信息">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {filteredMetrics.map((metric) => (
                <Card key={metric.category} size="small" style={{ border: '1px solid var(--color-border)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <h4 style={{ margin: 0, fontWeight: 500 }}>{metric.category}</h4>
                      <Badge count={`${metric.totalCount} 个产品`} style={{ backgroundColor: 'var(--color-muted)', color: 'var(--color-muted-foreground)' }} />
                      <Badge
                        count={`替代率 ${metric.substitutionRate}%`}
                        style={{
                          backgroundColor: metric.substitutionRate >= 50 ? 'color-mix(in oklch, var(--color-success) 15%, transparent)' : 'color-mix(in oklch, var(--color-warning) 15%, transparent)',
                          color: metric.substitutionRate >= 50 ? 'var(--color-success)' : 'var(--color-warning)',
                          border: `1px solid ${metric.substitutionRate >= 50 ? 'color-mix(in oklch, var(--color-success) 60%, transparent)' : 'color-mix(in oklch, var(--color-warning) 60%, transparent)'}`
                        }}
                      />
                    </div>
                  </div>

                  <Row gutter={[16, 16]}>
                    <Col md={8} xs={24}>
                      <div>
                        <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 8 }}>替代进度</p>
                        <Progress percent={metric.substitutionRate} size="small" strokeColor="var(--color-primary, var(--primary))" trailColor="var(--color-input-background, var(--input-background))" />
                        <p style={{ fontSize: 12, color: 'var(--color-muted-foreground)', marginTop: 4, margin: 0 }}>
                          {metric.domesticCount}/{metric.totalCount} 个国产产品
                        </p>
                      </div>
                    </Col>

                    <Col md={8} xs={24}>
                      <div>
                        <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 8 }}>故障率对比</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12 }}>
                            <span>国产: {metric.domesticFailureRate}</span>
                            <span>进口: {metric.importedFailureRate}</span>
                          </div>
                          <div style={{ fontSize: 12, color: '#8c8c8c' }}>
                            平均: {metric.avgFailureRate}
                          </div>
                        </div>
                      </div>
                    </Col>

                    <Col md={8} xs={24}>
                      <div>
                        <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 8 }}>主要品牌</p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                          {metric.brands.slice(0, 3).map((brand) => (
                            <Badge
                              key={brand.brand}
                              count={brand.brand}
                              style={{
                                backgroundColor: brand.isDomestic ? '#f6ffed' : '#fff7e6',
                                color: brand.isDomestic ? '#52c41a' : '#fa8c16',
                                border: `1px solid ${brand.isDomestic ? '#b7eb8f' : '#ffd591'}`,
                                fontSize: 12
                              }}
                            />
                          ))}
                        </div>
                      </div>
                    </Col>
                  </Row>
                </Card>
              ))}
            </div>
          </Card>
        </div>
      )}

      {viewMode === 'planning' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 替代规划概览 */}
          <Row gutter={[16, 16]}>
            {substitutionPlans.map((plan) => {
              const priorityProps = getPriorityProps(plan.priority);
              return (
                <Col lg={8} md={12} xs={24} key={plan.category}>
                  <Card
                    title={
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>{plan.category}</span>
                        <Badge
                          count={
                            plan.priority === 'high' ? '高优先级' :
                              plan.priority === 'medium' ? '中优先级' : '低优先级'
                          }
                          style={{ backgroundColor: 'transparent', color: priorityProps.style.color, border: `1px solid ${priorityProps.style.color}` }}
                        />
                      </div>
                    }
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                      <div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, marginBottom: 8 }}>
                          <span>当前进度</span>
                          <span>{plan.currentRate}%</span>
                        </div>
                        <Progress percent={plan.currentRate} size="small" strokeColor="var(--color-accent, var(--primary))" trailColor="var(--color-input-background, var(--input-background))" />
                        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#8c8c8c', marginTop: 4 }}>
                          <span>目标: {plan.targetRate}%</span>
                          <span>期限: {plan.timeline}</span>
                        </div>
                      </div>

                      <div>
                        <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 8 }}>主要挑战</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {plan.challenges.slice(0, 2).map((challenge, index) => (
                            <div key={index} style={{ display: 'flex', alignItems: 'flex-start', gap: 4, fontSize: 12, color: 'var(--color-muted-foreground)' }}>
                              <WarningOutlined style={{ fontSize: 12, marginTop: 2 }} />
                              {challenge}
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <p style={{ fontSize: 14, fontWeight: 500, marginBottom: 8 }}>建议措施</p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          {plan.recommendations.slice(0, 2).map((recommendation, index) => (
                            <div key={index} style={{ display: 'flex', alignItems: 'flex-start', gap: 4, fontSize: 12, color: 'var(--color-muted-foreground)' }}>
                              <CheckCircleOutlined style={{ fontSize: 12, marginTop: 2 }} />
                              {recommendation}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </Card>
                </Col>
              );
            })}
          </Row>

          {/* 替代时间线 */}
          <Card title="国产替代时间线">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {substitutionPlans
                .sort((a, b) => new Date(a.timeline.replace('年', '/').replace('月', '/').replace('底', '').replace('中', '')).getTime() -
                  new Date(b.timeline.replace('年', '/').replace('月', '/').replace('底', '').replace('中', '')).getTime())
                .map((plan, index) => {
                  const priorityProps = getPriorityProps(plan.priority);
                  return (
                    <div key={plan.category} style={{ display: 'flex', alignItems: 'flex-start', gap: 16 }}>
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                        <div style={{
                          width: 16,
                          height: 16,
                          borderRadius: '50%',
                          border: `2px solid ${priorityProps.style.color}`,
                          backgroundColor: priorityProps.style.color
                        }} />
                        {index < substitutionPlans.length - 1 && (
                          <div style={{ width: 2, height: 64, backgroundColor: 'var(--color-border)', marginTop: 8 }} />
                        )}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 4 }}>
                          <h4 style={{ margin: 0, fontWeight: 500 }}>{plan.category}</h4>
                          <span style={{ fontSize: 14, color: 'var(--color-muted-foreground)' }}>{plan.timeline}</span>
                        </div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 8 }}>
                          <span style={{ fontSize: 14 }}>
                            {plan.currentRate}% → {plan.targetRate}%
                          </span>
                          <div style={{ flex: 1 }}>
                            <Progress percent={(plan.currentRate / plan.targetRate) * 100} size="small" strokeColor={'var(--color-accent, var(--primary))'} trailColor={'var(--color-input-background, var(--input-background))'} />
                          </div>
                        </div>
                        <p style={{ fontSize: 12, color: 'var(--color-muted-foreground)', margin: 0 }}>
                          关键挑战: {plan.challenges[0]}
                        </p>
                      </div>
                    </div>
                  );
                })}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
