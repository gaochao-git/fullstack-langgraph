import React, { useMemo } from 'react';
import ReactEcharts from 'echarts-for-react';

// 使用React.memo包装组件，避免不必要的重渲染
const ZabbixChart = React.memo(({ data, style = {}, showHeader = true }) => {
    // 确保数据存在且有效
    if (!Array.isArray(data) || data.length === 0) {
        return <div>No data available</div>;
    }

    // 使用useMemo缓存图表配置，避免每次渲染都重新计算
    const chartOption = useMemo(() => {
        // 使用全量数据，不进行采样
        const processedData = data;

        // 提取时间和值的数组
        const times = processedData.map(item => item.metric_time);
        const values = processedData.map(item => parseFloat(item.value));
        
        // 使用第一个数据点获取基本信息
        const firstItem = processedData[0];

        // 计算统计值
        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const avgValue = values.reduce((a, b) => a + b, 0) / values.length;
        
        // 格式化统计值（保留2位小数）
        const formatValue = (val) => Number.isInteger(val) ? val.toString() : val.toFixed(2);
        const statsText = `当前值: ${formatValue(values[values.length - 1])} ${firstItem.units} | 最大值: ${formatValue(maxValue)} ${firstItem.units} | 数据点: ${values.length}`;
        
        // 提取年月日部分
        const extractDate = (timeRange) => {
          if (!timeRange) return '';
          // 假设时间格式包含日期，提取YYYY-MM-DD部分
          const dateMatch = timeRange.match(/(\d{4}-\d{2}-\d{2})/);
          return dateMatch ? dateMatch[1] : timeRange.split(' ')[0] || '';
        };
        const dateText = extractDate(firstItem.timeRange);
        const leftText = `${dateText} | ${firstItem.hostname || ''} | ${firstItem.key_}`;

        // 确定是否从0开始
        const shouldStartFromZero = minValue <= maxValue * 0.1;  // 如果最小值小于最大值的10%，则从0开始
        const yAxisMin = shouldStartFromZero ? 0 : minValue * 0.95;

        return {
            title: showHeader ? [
                {
                    text: `${leftText}`,
                    left: 'left',
                    top: 0,
                    textStyle: {
                        color: '#FCD34D',
                        fontSize: 13,
                        fontWeight: 'bold'
                    }
                },
                {
                    text: `${statsText}`,
                    right: 'right',
                    top: 0,
                    textStyle: {
                        color: '#FCD34D',
                        fontSize: 11,
                        fontWeight: 'bold'
                    }
                }
            ] : undefined,
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const value = parseFloat(params[0].value);
                    const formattedValue = Number.isInteger(value) ? value.toString() : value.toFixed(2);
                    const time = params[0].axisValue;
                    return `${time}<br/>${formattedValue}${firstItem.units}`;
                },
                axisPointer: {
                    type: 'line',
                    lineStyle: {
                        color: '#FBBF24',
                        type: 'dashed'
                    }
                }
            },
            grid: {
                top: showHeader ? 30 : 2,
                left: '1%',
                right: '1%',
                bottom: '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: times,
                axisLabel: {
                    rotate: 45,
                    color: '#E5E7EB',
                    fontSize: 11,
                    formatter: function(value) {
                        // 只显示时间部分，如果需要
                        return value.split(' ')[1];
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: '#60A5FA'
                    }
                },
                axisTick: {
                    lineStyle: {
                        color: '#60A5FA'
                    }
                },
                splitLine: {
                    show: false
                }
            },
            yAxis: {
                type: 'value',
                min: yAxisMin,
                axisLabel: {
                    color: '#E5E7EB',
                    fontSize: 11,
                    formatter: (value) => {
                        const numValue = parseFloat(value);
                        const formattedValue = Number.isInteger(numValue) ? numValue.toString() : numValue.toFixed(2);
                        return formattedValue + firstItem.units;
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: '#60A5FA'
                    }
                },
                axisTick: {
                    lineStyle: {
                        color: '#60A5FA'
                    }
                },
                splitLine: {
                    show: true,
                    lineStyle: {
                        type: 'dashed',
                        color: '#64748B'
                    }
                }
            },
            dataZoom: [
                {
                    type: 'inside',
                    start: 0,
                    end: 100
                },
                {
                    type: 'slider',
                    start: 0,
                    end: 100,
                    height: 20
                }
            ],
            series: [{
                type: 'line',
                data: values,
                smooth: false,
                symbol: 'circle',
                // 大数据量时不显示所有点的标记
                symbolSize: data.length > 100 ? 0 : 4,
                // 保留LTTB采样算法，但仅在ECharts内部渲染优化时使用
                sampling: 'lttb',
                lineStyle: {
                    width: 2,
                    color: '#06D6A0'
                },
                itemStyle: {
                    color: '#06D6A0'
                },
                areaStyle: {
                    color: {
                        type: 'linear',
                        x: 0,
                        y: 0,
                        x2: 0,
                        y2: 1,
                        colorStops: [{
                            offset: 0,
                            color: 'rgba(6,214,160,0.3)'
                        }, {
                            offset: 1,
                            color: 'rgba(6,214,160,0.05)'
                        }]
                    }
                }
            }]
        };
    }, [data, showHeader]); // 只有当data或showHeader变化时才重新计算

    return (
        <div style={{ width: '100%', padding: '5px 0' }}>
            <ReactEcharts 
                option={chartOption} 
                style={{ height: '200px', ...style }}
                opts={{ 
                    renderer: 'canvas',  // 使用canvas渲染器提高性能
                    devicePixelRatio: window.devicePixelRatio  // 适配高DPI显示器
                }}
                lazyUpdate={true}  // 启用懒更新，减少不必要的图表更新
                notMerge={true}    // 完全替换配置，避免合并开销
            />
        </div>
    );
});

export default ZabbixChart;