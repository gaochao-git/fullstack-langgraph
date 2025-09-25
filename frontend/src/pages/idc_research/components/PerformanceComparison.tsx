import React, { useMemo } from 'react';
import { Card, Row, Col, Empty, Progress } from 'antd';
import ReactECharts from 'echarts-for-react';
import { IDCData } from '../types/idc';

interface PerformanceComparisonProps {
  selectedIDCs: IDCData[];
}

export function PerformanceComparison({ selectedIDCs }: PerformanceComparisonProps) {
  const getCssVar = (name: string, fallback: string) => {
    if (typeof window === 'undefined') return fallback;
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  };

  const chartColors = useMemo(() => ({
    c1: getCssVar('--color-chart-1', '#5470c6'),
    c2: getCssVar('--color-chart-2', '#91cc75'),
    c3: getCssVar('--color-chart-3', '#fac858'),
    c4: getCssVar('--color-chart-4', '#ee6666'),
    c5: getCssVar('--color-chart-5', '#73c0de'),
    success: getCssVar('--color-success', '#22c55e'),
    warning: getCssVar('--color-warning', '#f59e0b'),
    destructive: getCssVar('--color-destructive', '#ef4444'),
    border: getCssVar('--color-border', '#e5e7eb'),
  }), []);
  if (selectedIDCs.length === 0) {
    return (
      <Card>
        <div style={{ textAlign: 'center', padding: '64px 0' }}>
          <Empty
            description="请选择至少一个数据中心进行比对分析"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        </div>
      </Card>
    );
  }

  // 关键指标对比柱状图配置
  const barChartOption = {
    title: {
      text: '关键指标对比',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['CPU使用率', '内存使用率', '网络负载'],
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
      data: selectedIDCs.map(idc => idc.name.replace('数据中心', ''))
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
        data: selectedIDCs.map(idc => idc.cpuUsage),
        itemStyle: { color: chartColors.c1 }
      },
      {
        name: '内存使用率',
        type: 'bar',
        data: selectedIDCs.map(idc => idc.memoryUsage),
        itemStyle: { color: chartColors.c2 }
      },
      {
        name: '网络负载',
        type: 'bar',
        data: selectedIDCs.map(idc => idc.networkLoad),
        itemStyle: { color: chartColors.c3 }
      }
    ]
  };

  // 雷达图配置
  const radarChartOption = {
    title: {
      text: '综合性能雷达图',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {},
    legend: {
      data: selectedIDCs.map(idc => idc.name.replace('数据中心', '')),
      top: 30
    },
    radar: {
      indicator: [
        { name: 'CPU性能', max: 100 },
        { name: '内存性能', max: 100 },
        { name: '网络性能', max: 100 },
        { name: '稳定性', max: 100 },
        { name: '温控效果', max: 100 }
      ],
      center: ['50%', '60%'],
      radius: '60%'
    },
    series: [
      {
        type: 'radar',
        data: selectedIDCs.map((idc, index) => ({
          value: [
            100 - idc.cpuUsage, // CPU性能（使用率越低越好）
            100 - idc.memoryUsage, // 内存性能
            100 - idc.networkLoad, // 网络性能
            idc.stabilityScore, // 稳定性
            Math.max(0, 100 - (idc.temperature - 15) * 2) // 温控效果
          ],
          name: idc.name.replace('数据中心', ''),
          itemStyle: {
            color: [chartColors.c1, chartColors.c2, chartColors.c3, chartColors.c4, chartColors.c5][index % 5]
          }
        }))
      }
    ]
  };

  // 趋势图配置
  const trendChartOption = {
    title: {
      text: 'CPU使用率趋势对比（最近6小时）',
      left: 'center',
      textStyle: { fontSize: 16, fontWeight: 'bold' }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'cross'
      }
    },
    legend: {
      data: selectedIDCs.map(idc => idc.name.replace('数据中心', '')),
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
      data: selectedIDCs[0]?.performanceHistory.slice(-6).map(point =>
        new Date(point.timestamp).toLocaleTimeString('zh-CN', {
          hour: '2-digit',
          minute: '2-digit'
        })
      ) || []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: selectedIDCs.map((idc, index) => ({
      name: idc.name.replace('数据中心', ''),
      type: 'line',
      data: idc.performanceHistory.slice(-6).map(point => point.cpu),
      smooth: true,
      itemStyle: {
        color: [chartColors.c1, chartColors.c2, chartColors.c3, chartColors.c4, chartColors.c5][index % 5]
      }
    }))
  };

  // 性能评分对比
  const performanceScores = selectedIDCs.map(idc => {
    const cpuScore = Math.max(0, 100 - idc.cpuUsage);
    const memoryScore = Math.max(0, 100 - idc.memoryUsage);
    const networkScore = Math.max(0, 100 - idc.networkLoad);
    const overallScore = Math.round((cpuScore + memoryScore + networkScore + idc.stabilityScore) / 4);

    return {
      name: idc.name,
      cpuScore,
      memoryScore,
      networkScore,
      stabilityScore: idc.stabilityScore,
      overallScore
    };
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <Row gutter={24}>
        <Col span={12}>
          <Card>
            <ReactECharts option={barChartOption} style={{ height: 350 }} />
          </Card>
        </Col>
        <Col span={12}>
          <Card>
            <ReactECharts option={radarChartOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      <Row gutter={24}>
        <Col span={24}>
          <Card>
            <ReactECharts option={trendChartOption} style={{ height: 350 }} />
          </Card>
        </Col>
      </Row>

      <Card title="性能评分总结" style={{ marginTop: 24 }}>
        <Row gutter={16}>
          {performanceScores.map((score, index) => (
            <Col span={Math.floor(24 / performanceScores.length)} key={index}>
              <Card size="small" style={{ textAlign: 'center' }}>
                <h4 style={{ margin: '0 0 16px 0' }}>{score.name}</h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr 48px', alignItems: 'center', fontSize: 14, gap: 8 }}>
                    <span>CPU性能</span>
                    <Progress percent={score.cpuScore} size="small" strokeColor={score.cpuScore >= 60 ? 'var(--color-success, #22c55e)' : 'var(--color-warning, #f59e0b)'} trailColor={'var(--color-input-background, var(--input-background))'} showInfo={false} />
                    <span style={{ textAlign: 'right' }}>{score.cpuScore}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr 48px', alignItems: 'center', width: '100%', gap: 8 }}>
                      <span>内存性能</span>
                      <Progress percent={score.memoryScore} size="small" strokeColor={score.memoryScore >= 60 ? 'var(--color-success, #22c55e)' : 'var(--color-warning, #f59e0b)'} trailColor={'var(--color-input-background, var(--input-background))'} showInfo={false} />
                      <span style={{ textAlign: 'right' }}>{score.memoryScore}</span>
                    </div>
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr 48px', alignItems: 'center', fontSize: 14, gap: 8 }}>
                    <span>网络性能</span>
                    <Progress percent={score.networkScore} size="small" strokeColor={score.networkScore >= 60 ? 'var(--color-success, #22c55e)' : 'var(--color-warning, #f59e0b)'} trailColor={'var(--color-input-background, var(--input-background))'} showInfo={false} />
                    <span style={{ textAlign: 'right' }}>{score.networkScore}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '100px 1fr 48px', alignItems: 'center', width: '100%', gap: 8 }}>
                      <span>稳定性</span>
                      <Progress percent={Math.min(100, Math.max(0, Math.round(score.stabilityScore)))} size="small" strokeColor={score.stabilityScore >= 95 ? 'var(--color-success, #22c55e)' : 'var(--color-warning, #f59e0b)'} trailColor={'var(--color-input-background, var(--input-background))'} showInfo={false} />
                      <span style={{ textAlign: 'right' }}>{score.stabilityScore}</span>
                    </div>
                  </div>
                  <div style={{
                    borderTop: '1px solid var(--color-border)',
                    paddingTop: 8,
                    marginTop: 8,
                    display: 'flex',
                    justifyContent: 'space-between',
                    fontWeight: 600
                  }}>
                    <span>综合评分:</span>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 56px', alignItems: 'center', gap: 8, width: 200 }}>
                      <Progress percent={score.overallScore} size="small" strokeColor={score.overallScore >= 80 ? 'var(--color-success, #22c55e)' : score.overallScore >= 60 ? 'var(--color-warning, #f59e0b)' : 'var(--color-destructive, #ef4444)'} trailColor={'var(--color-input-background, var(--input-background))'} showInfo={false} />
                      <span style={{ textAlign: 'right' }}>{score.overallScore}</span>
                    </div>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  );
}
