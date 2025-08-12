import React, { useMemo } from 'react';
import ReactEcharts from 'echarts-for-react';
import { theme } from 'antd';

// 使用React.memo包装组件，避免不必要的重渲染
const ZabbixChart = React.memo(({ data, style = {}, showHeader = true }) => {
    const { token } = theme.useToken();
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
        
        // 简化头部信息：只显示IP和指标名称
        const headerText = `${firstItem.hostname || ''} | ${firstItem.key_}`;

        // 确定是否从0开始
        const shouldStartFromZero = minValue <= maxValue * 0.1;  // 如果最小值小于最大值的10%，则从0开始
        const yAxisMin = shouldStartFromZero ? 0 : minValue * 0.95;

        return {
            tooltip: {
                trigger: 'axis',
                formatter: function(params) {
                    const value = parseFloat(params[0].value);
                    // 使用与Y轴标签相同的格式化逻辑
                    let formattedValue;
                    if (value >= 1000000) {
                        formattedValue = (value / 1000000).toFixed(1) + 'M';
                    } else if (value >= 1000) {
                        formattedValue = (value / 1000).toFixed(1) + 'K';
                    } else {
                        formattedValue = Number.isInteger(value) ? value.toString() : value.toFixed(1);
                    }
                    const time = params[0].axisValue;
                    return `${time}<br/>${formattedValue}${firstItem.units}`;
                },
                axisPointer: {
                    type: 'line',
                    lineStyle: {
                        color: token.colorWarning,
                        type: 'dashed'
                    }
                }
            },
            grid: {
                top: showHeader ? 40 : 2,
                left: '8%',
                right: '1%',
                bottom: showHeader ? '3%' : '3%',
                containLabel: true
            },
            xAxis: {
                type: 'category',
                data: times,
                axisLabel: {
                    rotate: 45,
                    color: token.colorText,
                    fontSize: 11,
                    formatter: function(value) {
                        // 只显示时间部分，如果需要
                        return value.split(' ')[1];
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: token.colorBorder
                    }
                },
                axisTick: {
                    lineStyle: {
                        color: token.colorBorder
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
                    color: token.colorText,
                    fontSize: 11,
                    formatter: (value) => {
                        const numValue = parseFloat(value);
                        // 对于大数字，使用K/M/G等单位简化显示
                        let formattedValue;
                        if (numValue >= 1000000) {
                            formattedValue = (numValue / 1000000).toFixed(1) + 'M';
                        } else if (numValue >= 1000) {
                            formattedValue = (numValue / 1000).toFixed(1) + 'K';
                        } else {
                            formattedValue = Number.isInteger(numValue) ? numValue.toString() : numValue.toFixed(1);
                        }
                        return formattedValue + firstItem.units;
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: token.colorBorder
                    }
                },
                axisTick: {
                    lineStyle: {
                        color: token.colorBorder
                    }
                },
                splitLine: {
                    show: true,
                    lineStyle: {
                        type: 'dashed',
                        color: token.colorBorderSecondary
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
                    color: token.colorSuccess
                },
                itemStyle: {
                    color: token.colorSuccess
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
                            color: `${token.colorSuccess}33`
                        }, {
                            offset: 1,
                            color: `${token.colorSuccess}0D`
                        }]
                    }
                }
            }]
        };
    }, [data, showHeader, token]); // 只有当data、showHeader或主题变化时才重新计算

    // 计算统计信息用于底部显示
    const statsInfo = useMemo(() => {
        if (!showHeader || !Array.isArray(data) || data.length === 0) return null;
        
        const values = data.map(item => parseFloat(item.value));
        const firstItem = data[0];
        
        const minValue = Math.min(...values);
        const maxValue = Math.max(...values);
        const currentValue = values[values.length - 1];
        
        const formatValue = (val) => Number.isInteger(val) ? val.toString() : val.toFixed(2);
        
        return {
            max: formatValue(maxValue),
            min: formatValue(minValue),
            units: firstItem.units
        };
    }, [data, showHeader]);

    // 获取头部信息用于显示
    const headerInfo = useMemo(() => {
        if (!showHeader || !Array.isArray(data) || data.length === 0) return null;
        const firstItem = data[0];
        return {
            hostname: firstItem.hostname || '',
            key: firstItem.key_ || ''
        };
    }, [data, showHeader]);

    return (
        <div style={{ width: '100%', padding: '0', position: 'relative' }}>
            {/* 自定义头部 - 支持悬浮显示 */}
            {headerInfo && (
                <div style={{
                    position: 'absolute',
                    top: '5px',
                    left: '10px',
                    zIndex: 10,
                    color: token.colorWarning,
                    fontSize: '13px',
                    fontWeight: 'bold',
                    maxWidth: 'calc(100% - 20px)',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap'
                }}
                title={`${headerInfo.hostname} | ${headerInfo.key}`} // 悬浮显示完整内容
                >
                    {headerInfo.hostname} | {headerInfo.key}
                </div>
            )}
            
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
            
            {/* 统计信息显示在图表下方 */}
            {statsInfo && (
                <div style={{ 
                    color: token.colorWarning, 
                    fontSize: '11px', 
                    fontWeight: 'bold',
                    textAlign: 'center',
                    marginTop: '2px',
                    padding: '2px 8px',
                    background: token.colorPrimaryBg,
                    borderRadius: '4px'
                }}>
                    最大值: {statsInfo.max} {statsInfo.units} | 
                    最小值: {statsInfo.min} {statsInfo.units}
                </div>
            )}
        </div>
    );
});

export default ZabbixChart;