import React from 'react';
import ZabbixChart from './ZabbixChart';

// 检测是否为Zabbix监控数据
const isZabbixMetricsData = (data: any): boolean => {
  if (!data || typeof data !== 'object') return false;
  
  // 检查get_host_metrics的数据格式
  if (data.metrics && typeof data.metrics === 'object') {
    const metricsKeys = Object.keys(data.metrics);
    if (metricsKeys.length > 0) {
      const firstMetric = data.metrics[metricsKeys[0]];
      // 检查是否有history数组和metric相关字段
      return firstMetric && 
             Array.isArray(firstMetric.history) && 
             firstMetric.history.length > 0 &&
             firstMetric.name &&
             firstMetric.units !== undefined;
    }
  }
  
  return false;
};

// 检测是否为Zabbix指标列表数据
const isZabbixMetricsListData = (data: any): boolean => {
  if (!data || typeof data !== 'object') return false;
  
  // 检查get_zabbix_metrics的数据格式
  return data.metrics_by_category && 
         typeof data.metrics_by_category === 'object' &&
         data.total_metrics &&
         data.actual_hostname;
};

// 渲染Zabbix指标列表
const ZabbixMetricsList: React.FC<{ data: any }> = ({ data }) => {
  const categories = data.metrics_by_category || {};
  
  return (
    <div className="border-2 border-cyan-400 rounded-xl p-4 my-3 shadow-lg" style={{ background: 'linear-gradient(135deg, #1E3A8A 0%, #3730A3 100%)' }}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-cyan-300">📊</span>
        <h4 className="font-semibold text-cyan-100">Zabbix 监控指标列表</h4>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
        <div className="space-y-2 text-cyan-100">
          <p><strong>输入主机:</strong> {data.input_hostname}</p>
          <p><strong>实际主机:</strong> {data.actual_hostname}</p>
          <p><strong>主机名称:</strong> {data.host_name}</p>
          <p><strong>指标总数:</strong> {data.total_metrics}</p>
        </div>
        
        <div className="space-y-2">
          <h5 className="font-medium text-yellow-400">指标分类统计:</h5>
          {Object.entries(categories).map(([category, metrics]: [string, any]) => (
            <div key={category} className="flex justify-between">
              <span className="text-cyan-200">{category}:</span>
              <span className="font-medium text-yellow-400">{metrics.length}个</span>
            </div>
          ))}
        </div>
      </div>
      
      <div className="mt-4">
        <details className="cursor-pointer">
          <summary className="text-sm font-medium text-cyan-300 hover:text-cyan-200">
            📋 查看详细指标列表
          </summary>
          <div className="mt-2 max-h-60 overflow-y-auto space-y-3">
            {Object.entries(categories).map(([category, metrics]: [string, any]) => (
              <div key={category} className="border-l-2 border-cyan-400 pl-3">
                <h6 className="font-medium text-yellow-400 mb-1">{category} ({metrics.length}个)</h6>
                <div className="space-y-1 text-xs">
                  {metrics.map((metric: any, index: number) => (
                    <div key={index} className="flex justify-between items-start">
                      <code className="text-cyan-300 bg-gray-900 px-1 rounded mr-2 flex-shrink-0">
                        {metric.key}
                      </code>
                      <span className="text-cyan-200 text-right">{metric.name}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </details>
      </div>
    </div>
  );
};

// 渲染Zabbix监控数据图表
const ZabbixMetricsCharts: React.FC<{ data: any }> = ({ data }) => {
  const metrics = data.metrics || {};
  const metricsEntries = Object.entries(metrics);
  
  return (
    <div className="space-y-4">
        {metricsEntries.map(([metricKey, metricData]: [string, any]) => {
          // 转换数据格式为ZabbixChart需要的格式
          const chartData = metricData.history?.map((item: any) => ({
            metric_time: item[0], // 时间戳
            value: item[1],       // 数值
            key_: metricKey,
            units: metricData.units || '',
            hostname: data.hostname,
            timeRange: data.time_range
          })) || [];
          
          if (chartData.length === 0) {
            return (
              <div key={metricKey} className="border border-cyan-500 rounded-lg p-2" style={{ background: 'rgba(59, 130, 246, 0.1)' }}>
                <h5 className="font-medium text-cyan-100 mb-2">{metricData.name}</h5>
                <div className="text-center text-cyan-200 py-4">
                  <p>当前值: {metricData.current_value} {metricData.units}</p>
                  <p className="text-sm">暂无历史数据</p>
                </div>
              </div>
            );
          }
          
          return (
            <div key={metricKey} className="border border-cyan-500 rounded-lg p-2" style={{ background: 'rgba(59, 130, 246, 0.1)' }}>
              <ZabbixChart 
                data={chartData}
                showHeader={true}
                style={{ height: '167px' }}
              />
            </div>
          );
        })}
    </div>
  );
};

// 主要的Zabbix数据渲染组件
const ZabbixDataRenderer: React.FC<{ data: any; toolName?: string }> = ({ data, toolName }) => {
  // 只对 get_zabbix_metric_data 工具显示图表
  if (toolName !== 'get_zabbix_metric_data') {
    return null; // 其他工具不处理，显示普通输出
  }
  
  // 尝试解析JSON字符串
  let parsedData = data;
  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data);
    } catch (e) {
      return null; // 不是JSON，不处理
    }
  }
  
  // 检查是否为监控数据（带图表）
  if (isZabbixMetricsData(parsedData)) {
    return <ZabbixMetricsCharts data={parsedData} />;
  }
  
  return null; // 不是有效的图表数据，不处理
};

// 检查是否可以渲染图表
export const canRenderChart = (data: any, toolName?: string): boolean => {
  if (toolName !== 'get_zabbix_metric_data') {
    return false;
  }
  
  let parsedData = data;
  if (typeof data === 'string') {
    try {
      parsedData = JSON.parse(data);
    } catch (e) {
      return false;
    }
  }
  
  return isZabbixMetricsData(parsedData);
};

export default ZabbixDataRenderer;