// @ts-nocheck
// 资源警报组件
import React, { useEffect, useState } from 'react';
import { Alert } from 'antd';

interface ClusterInfo {
  cluster_group_name?: string;
  cluster_name?: string;
}

interface ServerResourceData {
  ip: string;
  clusters?: ClusterInfo[];
  max_used_memory?: number;
  total_memory?: number;
  max_used_disk?: number;
  total_disk?: number;
  max_cpu_load?: number;
}

interface ThresholdConfig {
  min: number;
  max: number;
}

interface AlertsProps {
  data: ServerResourceData[];
  cpuThresholds: ThresholdConfig;
  memoryThresholds: ThresholdConfig;
  diskThresholds: ThresholdConfig;
  triggerUpdate: number;
  selectedGroups: string[];
}

const Alerts: React.FC<AlertsProps> = ({ data, cpuThresholds, memoryThresholds, diskThresholds, triggerUpdate, selectedGroups }) => {
  const [alerts, setAlerts] = useState<React.ReactElement[]>([]);

  useEffect(() => {
    const filteredData = selectedGroups.length > 0
      ? data.filter(resource => {
          const clusters = resource.clusters || [];
          return clusters.some(cluster => selectedGroups.includes(cluster.cluster_group_name));
        })
      : data;

    // 由于后端现在返回的就是每个主机的最大值数据，直接使用即可
    const newAlerts = filteredData.map(item => {
      const hostKey = `${item.ip}`;
      const clusters = item.clusters || [];
      const clusterInfo = clusters.length > 0 
        ? clusters.map(cluster => `${cluster.cluster_group_name || '未知集群组'} ${cluster.cluster_name || '未知集群'}`).join(', ')
        : '未知集群组 未知集群';
      const alertPrefix = `${item.ip} (${clusterInfo})`;
      const alerts = [];

      // 使用后端返回的最大值数据，添加安全检查
      const maxMemory = (item.max_used_memory && item.total_memory) ? (item.max_used_memory / item.total_memory) * 100 : 0;
      const maxDisk = (item.max_used_disk && item.total_disk) ? (item.max_used_disk / item.total_disk) * 100 : 0;
      const maxCpu = item.max_cpu_load || 0;

      // 内存警报 - 基于最大值
      if (maxMemory > memoryThresholds.max) {
        alerts.push(
          <Alert
            key={`${hostKey}-memory-high`}
            message={`${alertPrefix} | 内存最大值: ${maxMemory.toFixed(2)}% (${(item.max_used_memory || 0).toFixed(2)}GB/${(item.total_memory || 0).toFixed(2)}GB) | 警告：高于${memoryThresholds.max}%阈值`}
            type="error"
            showIcon
            banner
          />
        );
      } else if (maxMemory < memoryThresholds.min) {
        alerts.push(
          <Alert
            key={`${hostKey}-memory-low`}
            message={`${alertPrefix} | 内存最大值: ${maxMemory.toFixed(2)}% (${(item.max_used_memory || 0).toFixed(2)}GB/${(item.total_memory || 0).toFixed(2)}GB) | 提示：低于${memoryThresholds.min}%阈值`}
            type="warning"
            showIcon
            banner
          />
        );
      }

      // 磁盘警报 - 基于最大值
      if (maxDisk > diskThresholds.max) {
        alerts.push(
          <Alert
            key={`${hostKey}-disk-high`}
            message={`${alertPrefix} | 磁盘最大值: ${maxDisk.toFixed(2)}% (${(item.max_used_disk || 0).toFixed(2)}GB/${(item.total_disk || 0).toFixed(2)}GB) | 警告：高于${diskThresholds.max}%阈值`}
            type="error"
            showIcon
            banner
          />
        );
      } else if (maxDisk < diskThresholds.min) {
        alerts.push(
          <Alert
            key={`${hostKey}-disk-low`}
            message={`${alertPrefix} | 磁盘最大值: ${maxDisk.toFixed(2)}% (${(item.max_used_disk || 0).toFixed(2)}GB/${(item.total_disk || 0).toFixed(2)}GB) | 提示：低于${diskThresholds.min}%阈值`}
            type="warning"
            showIcon
            banner
          />
        );
      }

      // CPU警报 - 基于最大值
      if (maxCpu > cpuThresholds.max) {
        alerts.push(
          <Alert
            key={`${hostKey}-cpu-high`}
            message={`${alertPrefix} | CPU最大值: ${maxCpu.toFixed(2)}% | 警告：高于${cpuThresholds.max}%阈值`}
            type="error"
            showIcon
            banner
          />
        );
      } else if (maxCpu < cpuThresholds.min) {
        alerts.push(
          <Alert
            key={`${hostKey}-cpu-low`}
            message={`${alertPrefix} | CPU最大值: ${maxCpu.toFixed(2)}% | 提示：低于${cpuThresholds.min}%阈值`}
            type="warning"
            showIcon
            banner
          />
        );
      }

      return alerts;
    }).flat(); // 使用flat()展开嵌套数组

    setAlerts(newAlerts);
  }, [data, cpuThresholds, memoryThresholds, diskThresholds, triggerUpdate, selectedGroups]);

  return <>{alerts}</>;
};

export default Alerts;
