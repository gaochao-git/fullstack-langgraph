import React, { useMemo, useState } from 'react';
import { Card, Tabs, Select, Badge, Row, Col, Alert } from 'antd';
import { Badge as UIBadge } from './ui/badge';
import { CloudServerOutlined, DatabaseOutlined, CloudOutlined, ApiOutlined, GlobalOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { IDCData, Application, ApplicationService } from '../types/idc';
import { mockApplications, businessTypes, idcNameMap } from '../data/applicationData';

const { TabPane } = Tabs;
const { Option } = Select;

interface ApplicationMonitoringProps {
  selectedIDCs: IDCData[];
}

export function ApplicationMonitoring({ selectedIDCs }: ApplicationMonitoringProps) {
  const [selectedBusiness, setSelectedBusiness] = useState<string>('all');
  const [viewMode, setViewMode] = useState<'business' | 'idc'>('business');

  // 读取 CSS 变量的工具与调色板（放在组件内部，避免 hooks 报错）
  const getCssVar = (name: string, fallback: string) => {
    if (typeof window === 'undefined') return fallback;
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  };

  const palette = useMemo(() => ({
    app: getCssVar('--color-primary', '#1890ff'),
    database: getCssVar('--color-success', '#22c55e'),
    cache: getCssVar('--color-warning', '#f59e0b'),
    mq: getCssVar('--color-destructive', '#ef4444'),
    gateway: getCssVar('--color-accent', '#722ed1'),
  }), []);

  // 获取服务类型图标
  const getServiceIcon = (type: string) => {
    switch (type) {
      case 'app':
        return <CloudServerOutlined style={{ color: 'var(--color-primary, #1890ff)' }} />;
      case 'database':
        return <DatabaseOutlined style={{ color: 'var(--color-success, #22c55e)' }} />;
      case 'cache':
        return <CloudOutlined style={{ color: 'var(--color-warning, #f59e0b)' }} />;
      case 'mq':
        return <ApiOutlined style={{ color: 'var(--color-destructive, #ef4444)' }} />;
      case 'gateway':
        return <GlobalOutlined style={{ color: 'var(--color-accent, #722ed1)' }} />;
      default:
        return <CloudServerOutlined />;
    }
  };

  // 获取服务类型颜色
  const getServiceColor = (type: string) => (palette as any)[type] || palette.app;

  // 获取状态颜色
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'var(--color-success, #22c55e)';
      case 'warning':
        return 'var(--color-warning, #f59e0b)';
      case 'critical':
        return 'var(--color-destructive, #ef4444)';
      default:
        return 'var(--color-border, #e5e7eb)';
    }
  };

  // 文本颜色类（用于状态行与图标），对齐 idc_prj 显示风格
  const getStatusClass = (status: string) => {
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
      cpuUsage: Math.round(allServices.reduce((sum, s) => sum + s.metrics.cpuUsage, 0) / allServices.length),
      memoryUsage: Math.round(allServices.reduce((sum, s) => sum + s.metrics.memoryUsage, 0) / allServices.length),
      responseTime: Math.round(allServices.reduce((sum, s) => sum + s.metrics.responseTime, 0) / allServices.length),
      errorRate: Number((allServices.reduce((sum, s) => sum + s.metrics.errorRate, 0) / allServices.length).toFixed(3)),
      availability: Number((allServices.reduce((sum, s) => sum + s.metrics.availability, 0) / allServices.length).toFixed(2)),
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
      cpuUsage: Math.round(services.reduce((sum, s) => sum + s.metrics.cpuUsage, 0) / services.length),
      memoryUsage: Math.round(services.reduce((sum, s) => sum + s.metrics.memoryUsage, 0) / services.length),
      responseTime: Math.round(services.reduce((sum, s) => sum + s.metrics.responseTime, 0) / services.length),
      errorRate: Number((services.reduce((sum, s) => sum + s.metrics.errorRate, 0) / services.length).toFixed(3)),
      availability: Number((services.reduce((sum, s) => sum + s.metrics.availability, 0) / services.length).toFixed(2)),
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
    itemStyle: { color: getServiceColor(type) },
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

      const result: any = {
        business: app.businessType,
      };
      servicesByIDC.forEach(item => {
        result[item.idc] = item.availability;
      });
      return result;
    });

  // 业务性能比较柱状图配置
  const businessBarChartOption = {
    title: {
      text: '业务性能比较',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['CPU使用率', '内存使用率'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '20%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: businessData.map(d => d?.name || ''),
      axisLabel: {
        rotate: -45
      }
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'CPU使用率',
        type: 'bar',
        data: businessData.map(d => d?.cpuUsage || 0),
        itemStyle: { color: palette.app }
      },
      {
        name: '内存使用率',
        type: 'bar',
        data: businessData.map(d => d?.memoryUsage || 0),
        itemStyle: { color: palette.database }
      }
    ]
  };

  // 服务类型分布饼图配置
  const serviceTypePieOption = {
    title: {
      text: '服务类型分布',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'item',
      formatter: '{a} <br/>{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: '实例数量',
        type: 'pie',
        radius: '60%',
        center: ['60%', '50%'],
        data: pieData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  };

  // 响应时间与错误率散点图配置
  const scatterChartOption = {
    title: {
      text: '业务响应时间与错误率分析',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const data = params.data;
        return `${data.name}<br/>响应时间: ${data.value[0]}ms<br/>错误率: ${data.value[1]}%<br/>可用性: ${data.availability}%`;
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      name: '响应时间(ms)',
      nameLocation: 'middle',
      nameGap: 30
    },
    yAxis: {
      type: 'value',
      name: '错误率(%)',
      nameLocation: 'middle',
      nameGap: 40
    },
    series: [
      {
        type: 'scatter',
        symbolSize: 60,
        data: businessData.map(d => ({
          name: d?.name,
          value: [d?.responseTime, d?.errorRate],
          availability: d?.availability,
          itemStyle: {
            color: getServiceColor('app')
          }
        }))
      }
    ]
  };

  // 跨数据中心业务可用性比较
  const crossIDCBarOption = {
    title: {
      text: '跨数据中心业务可用性比较',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['北京', '上海', '广州', '深圳', '成都'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: crossIDCHealthData.map(d => d.business)
    },
    yAxis: {
      type: 'value',
      min: 90,
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: '北京',
        type: 'bar',
        data: crossIDCHealthData.map(d => d['北京'] || null),
        itemStyle: { color: palette.app }
      },
      {
        name: '上海',
        type: 'bar',
        data: crossIDCHealthData.map(d => d['上海'] || null),
        itemStyle: { color: palette.database }
      },
      {
        name: '广州',
        type: 'bar',
        data: crossIDCHealthData.map(d => d['广州'] || null),
        itemStyle: { color: palette.cache }
      },
      {
        name: '深圳',
        type: 'bar',
        data: crossIDCHealthData.map(d => d['深圳'] || null),
        itemStyle: { color: palette.mq }
      },
      {
        name: '成都',
        type: 'bar',
        data: crossIDCHealthData.map(d => d['成都'] || null),
        itemStyle: { color: palette.gateway }
      }
    ]
  };

  // IDC应用性能比较
  const idcBarOption = {
    title: {
      text: '数据中心应用性能比较',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    legend: {
      data: ['CPU使用率', '内存使用率'],
      top: 30
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: idcData.map(d => d?.name || '')
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'CPU使用率',
        type: 'bar',
        data: idcData.map(d => d?.cpuUsage || 0),
        itemStyle: { color: palette.app }
      },
      {
        name: '内存使用率',
        type: 'bar',
        data: idcData.map(d => d?.memoryUsage || 0),
        itemStyle: { color: palette.database }
      }
    ]
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* 控制面板 */}
      <Card size="small">
        <Row gutter={16} align="middle">
          <Col span={6}>
            <label style={{ marginRight: 8 }}>查看维度:</label>
            <Tabs
              activeKey={viewMode}
              onChange={(key) => setViewMode(key as 'business' | 'idc')}
              size="small"
              type="card"
            >
              <TabPane tab="按业务分析" key="business" />
              <TabPane tab="按数据中心分析" key="idc" />
            </Tabs>
          </Col>
          <Col span={6}>
            <label style={{ marginRight: 8 }}>业务筛选:</label>
            <Select
              value={selectedBusiness}
              onChange={setSelectedBusiness}
              style={{ width: 150 }}
            >
              <Option value="all">全部业务</Option>
              {businessTypes.map(type => (
                <Option key={type} value={type}>{type}</Option>
              ))}
            </Select>
          </Col>
        </Row>
      </Card>

      {/* 应用概览统计 */}
      <Row gutter={24}>
        <Col span={6}>
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <CloudServerOutlined style={{ fontSize: 20, color: 'var(--color-primary, #1890ff)' }} />
              <div>
                <p style={{ margin: 0, fontSize: 14, color: 'var(--color-muted-foreground)' }}>总应用数</p>
                <p style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>{filteredApplications.length}</p>
              </div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <DatabaseOutlined style={{ fontSize: 20, color: 'var(--color-success, #22c55e)' }} />
              <div>
                <p style={{ margin: 0, fontSize: 14, color: 'var(--color-muted-foreground)' }}>总服务实例</p>
                <p style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>
                  {filteredApplications.flatMap(app => app.services).reduce((sum, s) => sum + s.instances, 0)}
                </p>
              </div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <CheckCircleOutlined style={{ fontSize: 20, color: 'var(--color-success, #22c55e)' }} />
              <div>
                <p style={{ margin: 0, fontSize: 14, color: 'var(--color-muted-foreground)' }}>健康应用</p>
                <p style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>
                  {filteredApplications.filter(app => app.status === 'healthy').length}
                </p>
              </div>
            </div>
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <ExclamationCircleOutlined style={{ fontSize: 20, color: 'var(--color-destructive, #ef4444)' }} />
              <div>
                <p style={{ margin: 0, fontSize: 14, color: 'var(--color-muted-foreground)' }}>异常应用</p>
                <p style={{ margin: 0, fontSize: 24, fontWeight: 600 }}>
                  {filteredApplications.filter(app => app.status !== 'healthy').length}
                </p>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {viewMode === 'business' ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {/* 业务性能分析 */}
          <Row gutter={24}>
            <Col span={12}>
              <Card>
                <ReactECharts option={businessBarChartOption} style={{ height: 350 }} />
              </Card>
            </Col>
            <Col span={12}>
              <Card>
                <ReactECharts option={serviceTypePieOption} style={{ height: 350 }} />
              </Card>
            </Col>
          </Row>

          {/* 响应时间与错误率分析 */}
          <Card>
            <ReactECharts option={scatterChartOption} style={{ height: 350 }} />
          </Card>

          {/* 跨数据中心业务健康度 */}
          {crossIDCHealthData.length > 0 && (
            <Card>
              <ReactECharts option={crossIDCBarOption} style={{ height: 350 }} />
            </Card>
          )}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
          {selectedIDCs.length === 0 ? (
            <Card>
              <Alert
                message="请先选择数据中心"
                description="请在上方选择需要分析的数据中心，以查看应用程序监控信息"
                type="info"
                showIcon
              />
            </Card>
          ) : (
            <>
              {/* 数据中心应用性能比较 */}
              <Card>
                <ReactECharts option={idcBarOption} style={{ height: 350 }} />
              </Card>

              {/* 数据中心应用可用性 */}
              <Card title="数据中心应用可用性">
                <Row gutter={[16, 16]}>
                  {idcData.map((idc, index) => (
                    <Col span={8} key={index}>
                      <Card size="small">
                        <div style={{ textAlign: 'center' }}>
                          <h4 style={{ margin: '0 0 8px 0' }}>{idc?.name}</h4>
                          <div style={{ fontSize: 24, fontWeight: 600, color: (idc?.availability || 0) >= 99 ? 'var(--color-success)' : 'var(--color-warning)' }}>
                            {idc?.availability?.toFixed(2)}%
                          </div>
                          <div style={{ fontSize: 12, color: 'var(--color-muted-foreground)', marginTop: 4 }}>
                            {idc?.totalServices} 个服务 | {idc?.totalInstances} 个实例
                          </div>
                        </div>
                      </Card>
                    </Col>
                  ))}
                </Row>
              </Card>
            </>
          )}
        </div>
      )}

      {/* 应用详细信息 */}
      <Card title="应用详细信息">
        <div className="space-y-4">
          {filteredApplications.map(app => (
            <div
              key={app.id}
              className="border rounded-lg p-4"
              style={{ borderColor: 'var(--color-border, #e5e7eb)' }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <h4 className="font-medium m-0">{app.name}</h4>
                  <UIBadge variant="outline">{app.businessType}</UIBadge>
                  <UIBadge variant="secondary">v{app.version}</UIBadge>
                  <UIBadge className={app.isShared ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'}>
                    {app.isShared ? '跨数据中心' : '单数据中心'}
                  </UIBadge>
                </div>
                <div className={`flex items-center gap-1 ${getStatusClass(app.status)}`}>
                  {app.status === 'healthy' ? (
                    <CheckCircleOutlined style={{ fontSize: 16 }} />
                  ) : (
                    <ExclamationCircleOutlined style={{ fontSize: 16 }} />
                  )}
                  <span className="text-sm capitalize">{app.status}</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {app.services
                  .filter(service => selectedIDCs.length === 0 || selectedIDCs.some(idc => idc.id === service.idcId))
                  .map(service => (
                    <div
                      key={service.id}
                      className="p-3 rounded-lg"
                      style={{
                        backgroundColor: 'var(--color-muted, var(--muted, #f6f6f6))',
                        border: '1px solid var(--color-border, #e5e7eb)'
                      }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        {getServiceIcon(service.type)}
                        <span className="font-medium text-sm">{service.name}</span>
                        <UIBadge variant="outline" className="text-xs">
                          {idcNameMap[service.idcId]?.replace('数据中心', '') || service.idcId}
                        </UIBadge>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>实例: {service.instances}</div>
                        <div>CPU: {service.metrics.cpuUsage}%</div>
                        <div>内存: {service.metrics.memoryUsage}%</div>
                        <div>可用性: {service.metrics.availability.toFixed(1)}%</div>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
