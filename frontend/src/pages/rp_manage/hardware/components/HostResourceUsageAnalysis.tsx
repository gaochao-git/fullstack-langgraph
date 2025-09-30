// @ts-nocheck
// 主机资源用量分析页
import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Select, Layout, Card, Row, Col, Input, Button, message, DatePicker, ConfigProvider, Spin, Alert, Tabs, Checkbox, Statistic, TabsProps } from 'antd';
import apiClient from '../services/apiClient';
import html2canvas from '../vendor/html2canvas';
import Alerts from './hostResourceUsageSubPage/Alerts';
import ResourceAlerts from './hostResourceUsageSubPage/ResourceAlerts';
import DiskFullPrediction from './hostResourceUsageSubPage/DiskFullPrediction';
import moment from '../vendor/moment';
import 'moment/locale/zh-cn';
import zhCN from 'antd/locale/zh_CN';
import XLSX from '../vendor/xlsx';
import { getResourceAlertsColumns } from './hostResourceUsageSubPage/ResourceAlerts';
import { getDiskPredictionColumns } from './hostResourceUsageSubPage/DiskFullPrediction';
import GeographicDistribution from './hostResourceUsageSubPage/GeographicDistribution';
import HostResourceDetail from './hostResourceUsageSubPage/HostResourceDetail';

const { Content } = Layout;
const { RangePicker } = DatePicker;
const { Option } = Select;

moment.locale('zh-cn');

interface ClusterInfo {
  cluster_name?: string;
  cluster_group_name?: string;
  department_name?: string;
}

interface IdcInfo {
  idc_name?: string;
  idc_code?: string;
}

interface ServerResource {
  id?: string | number;
  ip?: string;
  host_ip?: string;
  host_name?: string;
  clusters?: ClusterInfo[];
  cluster_name?: string;
  idc_info?: IdcInfo;
  idc?: string;
  department?: string;
  max_cpu_load?: number;
  max_used_memory?: number;
  total_memory?: number;
  max_used_disk?: number;
  total_disk?: number;
  [key: string]: any;
}

interface DiskPredictionData {
  id?: string | number;
  ip?: string;
  clusters?: ClusterInfo[];
  idc_info?: IdcInfo;
  current_disk_usage_percent?: number;
  total_disk?: number;
  used_disk?: number;
  daily_growth_rate?: number;
  predicted_full_date?: string;
  days_until_full?: number;
  is_high_risk?: boolean;
}

interface Stats {
  totalClusters: number;
  totalHosts: number;
  compliantClusters: number;
  compliantHosts: number;
  nonCompliantClusters: number;
  nonCompliantHosts: number;
}

interface Thresholds {
  min: number;
  max: number;
}

const HostResourceUsageAnalysis: React.FC = () => {
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8888';
  const [clusterGroups, setClusterGroups] = useState<any[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<string[]>([]);
  const [selectedClusters, setSelectedClusters] = useState<string[]>([]);
  const [selectedDepartments, setSelectedDepartments] = useState<string[]>([]);
  const [selectedIdcs, setSelectedIdcs] = useState<string[]>([]);
  const [serverResources, setServerResources] = useState<ServerResource[]>([]);
  const [dateRange, setDateRange] = useState<[moment.Moment, moment.Moment] | null>(null);
  const [cpuThresholds, setCpuThresholds] = useState<Thresholds>({ min: 10, max: 80 });
  const [memoryThresholds, setMemoryThresholds] = useState<Thresholds>({ min: 10, max: 80 });
  const [diskThresholds, setDiskThresholds] = useState<Thresholds>({ min: 10, max: 80 });
  const [showOnlyNonCompliant, setShowOnlyNonCompliant] = useState(false);
  const [triggerUpdate, setTriggerUpdate] = useState(0);
  const [emailAddress, setEmailAddress] = useState('');
  const contentRef = useRef<HTMLDivElement>(null);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);
  const [selectedCluster, setSelectedCluster] = useState<string | null>(null);
  const [dataLoadingError, setDataLoadingError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [diskPredictionData, setDiskPredictionData] = useState<DiskPredictionData[]>([]);
  const [isDiskPredictionLoading, setIsDiskPredictionLoading] = useState(false);
  const [diskPredictionLoaded, setDiskPredictionLoaded] = useState(false);

  // 统计数据
  const [stats, setStats] = useState<Stats>({
    totalClusters: 0,
    totalHosts: 0,
    compliantClusters: 0,
    compliantHosts: 0,
    nonCompliantClusters: 0,
    nonCompliantHosts: 0
  });

  useEffect(() => {
    apiClient.axiosGet('cmdb/v1/cluster-groups')
      .then(response => {
        let clusterGroupsList = [];

        // 处理不同的数据结构
        if (Array.isArray(response.data)) {
          clusterGroupsList = response.data;
        } else if (response.data && response.data.list) {
          clusterGroupsList = response.data.list;
        } else if (response.data && response.data.data) {
          clusterGroupsList = response.data.data;
        } else {
          console.warn('未知的集群组数据格式:', response.data);
          clusterGroupsList = [];
        }

        setClusterGroups(clusterGroupsList);
      })
      .catch(error => {
        console.error('Error fetching cluster groups:', error);
        setClusterGroups([]);
      });

    fetchServerResources();
  }, []);

  // 设置默认日期范围为最近3个月
  useEffect(() => {
    const endDate = moment();
    const startDate = moment().subtract(3, 'months');
    setDateRange([startDate, endDate]);
  }, []);

  const fetchServerResources = (startDate?: moment.Moment, endDate?: moment.Moment) => {
    const params: any = {};
    if (startDate && endDate) {
      params.startDate = startDate.format('YYYY-MM-DD');
      params.endDate = endDate.format('YYYY-MM-DD');
    } else {
      const threeMonthsAgo = moment().subtract(3, 'months');
      params.startDate = threeMonthsAgo.format('YYYY-MM-DD HH:mm:ss');
      params.endDate = moment().add(1, 'day').format('YYYY-MM-DD');
    }

    setServerResources([]);
    setDataLoadingError(null);
    setIsLoading(true);
    message.loading({ content: '正在加载数据...', key: 'loadingData' });

    // 使用正确的接口 server-resources-max 获取峰值数据
    apiClient.axiosGet('cmdb/v1/server-resources-max', { params })
      .then(response => {
        setIsLoading(false);

        // 检查API是否返回了错误信息
        if (response.data && response.data.success === false) {
          setDataLoadingError(response.data.message || '获取数据失败，但服务器未提供具体错误信息');
          message.error({ content: response.data.message || '获取数据失败', key: 'loadingData', duration: 4 });
          return;
        }

        const serverResourcesList = Array.isArray(response.data)
          ? response.data
          : (response.data.list || []);
        setServerResources(serverResourcesList);
        message.success({ content: '数据加载成功', key: 'loadingData', duration: 2 });
      })
      .catch(error => {
        setIsLoading(false);
        console.error('Error fetching server resources:', error);
        const errorMessage = error.response?.data?.message || '数据加载失败，请检查网络连接或联系管理员';
        setDataLoadingError(errorMessage);
        message.error({ content: errorMessage, key: 'loadingData', duration: 4 });
      });
  };

  // 获取磁盘预测数据
  const fetchDiskPrediction = (startDate?: moment.Moment, endDate?: moment.Moment) => {
    const params: any = {};
    if (startDate && endDate) {
      params.begin_time = startDate.format('YYYY-MM-DD HH:mm:ss');
      params.end_time = endDate.format('YYYY-MM-DD HH:mm:ss');
    } else {
      // 默认获取最近3个月的数据
      const threeMonthsAgo = moment().subtract(3, 'months');
      params.begin_time = threeMonthsAgo.format('YYYY-MM-DD HH:mm:ss');
      params.end_time = moment().format('YYYY-MM-DD HH:mm:ss');
    }

    setIsDiskPredictionLoading(true);

    apiClient.getDiskPrediction(params)
      .then(response => {
        setIsDiskPredictionLoading(false);

        // 检查响应结构
        console.log('磁盘预测数据响应:', response);

        // 检查 response.data 是否存在
        if (!response.data) {
          console.error('获取磁盘预测数据失败: 响应数据格式不正确');
          message.error('获取磁盘预测数据失败: 响应数据格式不正确');
          setDiskPredictionData([]);
          return;
        }

        // 检查 response.data.success 状态
        if (response.data.success === false) {
          console.error('获取磁盘预测数据失败:', response.data.message);
          message.error(response.data.message || '获取磁盘预测数据失败');
          setDiskPredictionData([]);
          return;
        }

        // 正确获取 List 数据
        const diskPredictionList = Array.isArray(response.data.list) ? response.data.list : [];
        console.log('磁盘预测数据字段检查:', {
          'response.data.list存在吗': !!response.data.list,
          'response.data.List存在吗': !!response.data.List,
          '实际使用的数据': diskPredictionList
        });
        setDiskPredictionData(diskPredictionList);
        setDiskPredictionLoaded(true);
        console.log('磁盘预测数据获取成功:', diskPredictionList.length, '条记录');
      })
      .catch(error => {
        setIsDiskPredictionLoading(false);
        console.error('Error fetching disk prediction:', error);

        // 增强错误处理
        let errorMessage = '磁盘预测数据加载失败，请检查网络连接或联系管理员';

        if (error.response && error.response.data) {
          errorMessage = error.response.data.message || errorMessage;
        } else if (error.message) {
          errorMessage = `磁盘预测数据加载失败: ${error.message}`;
        }

        message.error(errorMessage);
        setDiskPredictionData([]);
      });
  };

  const handleGroupChange = (value: string[]) => {
    setSelectedGroups(value);
  };

  const handleClusterChange = (value: string[]) => {
    setSelectedClusters(value);
  };

  const handleDepartmentChange = (value: string[]) => {
    setSelectedDepartments(value);
  };

  const handleIdcChange = (value: string[]) => {
    setSelectedIdcs(value);
  };

  const handleCpuThresholdChange = (type: 'min' | 'max', value: number) => {
    setCpuThresholds(prev => ({
      ...prev,
      [type]: value
    }));
    setTriggerUpdate(prev => prev + 1);
  };

  const handleMemoryThresholdChange = (type: 'min' | 'max', value: number) => {
    setMemoryThresholds(prev => ({
      ...prev,
      [type]: value
    }));
    setTriggerUpdate(prev => prev + 1);
  };

  const handleDiskThresholdChange = (type: 'min' | 'max', value: number) => {
    setDiskThresholds(prev => ({
      ...prev,
      [type]: value
    }));
    setTriggerUpdate(prev => prev + 1);
  };

  const handleShowNonCompliantChange = (e: any) => {
    setShowOnlyNonCompliant(e.target.checked);
  };

  const updateStats = (data: ServerResource[]) => {
    // 第一步：为每台主机计算达标情况，避免重复计算
    const hostCompliance = data.map(resource => {
      const cpuUsage = Number(resource.max_cpu_load) || 0;
      const memoryUsage = (Number(resource.max_used_memory) / Number(resource.total_memory)) * 100 || 0;
      const diskUsage = (Number(resource.max_used_disk) / Number(resource.total_disk)) * 100 || 0;

      const cpuCompliant = cpuUsage >= cpuThresholds.min && cpuUsage <= cpuThresholds.max;
      const memoryCompliant = memoryUsage >= memoryThresholds.min && memoryUsage <= memoryThresholds.max;
      const diskCompliant = diskUsage >= diskThresholds.min && diskUsage <= diskThresholds.max;

      const isCompliant = cpuCompliant && memoryCompliant && diskCompliant;

      // 获取主机所属的集群
      let clusters: string[] = [];
      if (resource.clusters && Array.isArray(resource.clusters) && resource.clusters.length > 0) {
        clusters = resource.clusters.map(cluster => cluster.cluster_name || '未分配集群');
      } else if (resource.cluster_name) {
        clusters = [resource.cluster_name];
      } else {
        clusters = ['未分配集群'];
      }

      return {
        resource,
        isCompliant,
        clusters,
        ip: resource.ip || resource.host_ip || 'unknown'
      };
    });

    // 第二步：按集群分组，计算集群级别的达标情况
    const clusterStats: any = {};

    hostCompliance.forEach(hostInfo => {
      hostInfo.clusters.forEach(clusterName => {
        if (!clusterStats[clusterName]) {
          clusterStats[clusterName] = {
            hosts: [],
            compliantHosts: 0,
            nonCompliantHosts: 0
          };
        }
        // 避免同一主机在同一集群中重复计算
        const existingHost = clusterStats[clusterName].hosts.find((h: any) => h.ip === hostInfo.ip);
        if (!existingHost) {
          clusterStats[clusterName].hosts.push(hostInfo);
          if (hostInfo.isCompliant) {
            clusterStats[clusterName].compliantHosts++;
          } else {
            clusterStats[clusterName].nonCompliantHosts++;
          }
        }
      });
    });

    // 第三步：计算整体统计数据
    const totalClusters = Object.keys(clusterStats).length;
    const uniqueHosts = new Set();
    hostCompliance.forEach(hostInfo => {
      uniqueHosts.add(hostInfo.ip);
    });
    const totalHosts = uniqueHosts.size;

    let compliantClusters = 0;
    let nonCompliantClusters = 0;

    // 确定每个集群的达标状态
    const clusterCompliantStatus: any = {};
    Object.entries(clusterStats).forEach(([clusterName, stats]: [string, any]) => {
      clusterCompliantStatus[clusterName] = stats.nonCompliantHosts === 0 && stats.compliantHosts > 0;
      if (clusterCompliantStatus[clusterName]) {
        compliantClusters++;
      } else {
        nonCompliantClusters++;
      }
    });

    // 为每台主机确定归属（避免重复计算）
    const hostFinalStatus: any = {};
    hostCompliance.forEach(hostInfo => {
      const hostKey = hostInfo.ip;

      let belongsToCompliantCluster = false;
      hostInfo.clusters.forEach(clusterName => {
        if (clusterCompliantStatus[clusterName]) {
          belongsToCompliantCluster = true;
        }
      });

      hostFinalStatus[hostKey] = {
        isHostCompliant: hostInfo.isCompliant,
        belongsToCompliantCluster: belongsToCompliantCluster,
        clusters: hostInfo.clusters
      };
    });

    // 统计主机数量（每台主机只算一次）
    let compliantHostsFromCompliantClusters = 0;
    let nonCompliantHostsFromNonCompliantClusters = 0;

    Object.values(hostFinalStatus).forEach((status: any) => {
      if (status.belongsToCompliantCluster) {
        compliantHostsFromCompliantClusters++;
      } else {
        nonCompliantHostsFromNonCompliantClusters++;
      }
    });

    setStats({
      totalClusters,
      totalHosts,
      compliantClusters,
      compliantHosts: compliantHostsFromCompliantClusters,
      nonCompliantClusters,
      nonCompliantHosts: nonCompliantHostsFromNonCompliantClusters
    });
  };

  const handleDateRangeChange = (dates: [moment.Moment, moment.Moment] | null, dateStrings: [string, string]) => {
    setDateRange(dates);
    if (dates) {
      fetchServerResources(dates[0], dates[1]);
      // 只有在磁盘预测数据已被加载过的情况下才更新
      if (diskPredictionLoaded) {
        fetchDiskPrediction(dates[0], dates[1]);
      }
    } else {
      fetchServerResources();
      // 只有在磁盘预测数据已被加载过的情况下才更新
      if (diskPredictionLoaded) {
        fetchDiskPrediction();
      }
    }
  };

  // 处理Tab切换事件
  const handleTabChange = (activeKey: string) => {
    // 当用户点击磁盘空间预测tab时，如果数据尚未加载，则开始加载
    if (activeKey === 'disk-prediction' && !diskPredictionLoaded) {
      if (dateRange) {
        fetchDiskPrediction(dateRange[0], dateRange[1]);
      } else {
        fetchDiskPrediction();
      }
    }
  };

  const filteredData = useMemo(() => {
    let filtered = serverResources.filter(resource => {
      // 基于集群数组结构进行筛选
      const groupMatch = selectedGroups.length === 0 ||
        (resource.clusters && resource.clusters.some(cluster => selectedGroups.includes(cluster.cluster_group_name || '')));

      const clusterMatch = selectedClusters.length === 0 ||
        (resource.clusters && resource.clusters.some(cluster => selectedClusters.includes(cluster.cluster_name || '')));

      // 部门过滤
      const departmentMatch = selectedDepartments.length === 0 || (() => {
        if (!resource.clusters || resource.clusters.length === 0) {
          return false;
        }
        return resource.clusters.some(cluster => {
          return cluster.department_name && selectedDepartments.includes(cluster.department_name);
        });
      })();

      const idcMatch = selectedIdcs.length === 0 ||
        (resource.idc_info && selectedIdcs.includes(resource.idc_info.idc_name || ''));

      return groupMatch && clusterMatch && departmentMatch && idcMatch;
    });

    // 按阈值筛选
    if (showOnlyNonCompliant) {
      filtered = filtered.filter(resource => {
        const cpuUsage = Number(resource.max_cpu_load) || 0;
        const memoryUsage = (Number(resource.max_used_memory) / Number(resource.total_memory)) * 100 || 0;
        const diskUsage = (Number(resource.max_used_disk) / Number(resource.total_disk)) * 100 || 0;

        const cpuCompliant = cpuUsage >= cpuThresholds.min && cpuUsage <= cpuThresholds.max;
        const memoryCompliant = memoryUsage >= memoryThresholds.min && memoryUsage <= memoryThresholds.max;
        const diskCompliant = diskUsage >= diskThresholds.min && diskUsage <= diskThresholds.max;

        return !cpuCompliant || !memoryCompliant || !diskCompliant;
      });
    }

    return filtered;
  }, [serverResources, selectedGroups, selectedClusters, selectedDepartments, selectedIdcs, showOnlyNonCompliant, cpuThresholds, memoryThresholds, diskThresholds]);

  // 过滤磁盘预测数据，使其响应筛选条件
  const filteredDiskPredictionData = useMemo(() => {
    if (!diskPredictionData || diskPredictionData.length === 0) {
      return [];
    }

    const filtered = diskPredictionData.filter(predictionItem => {
      if (!predictionItem || !predictionItem.ip) {
        return false;
      }

      // 基于集群数组结构进行筛选（与主数据筛选逻辑保持一致）
      const groupMatch = selectedGroups.length === 0 ||
        (predictionItem.clusters && predictionItem.clusters.some(cluster => selectedGroups.includes(cluster.cluster_group_name || '')));

      const clusterMatch = selectedClusters.length === 0 ||
        (predictionItem.clusters && predictionItem.clusters.some(cluster => selectedClusters.includes(cluster.cluster_name || '')));

      // 部门过滤
      const departmentMatch = selectedDepartments.length === 0 || (() => {
        if (!predictionItem.clusters || predictionItem.clusters.length === 0) {
          return false;
        }
        return predictionItem.clusters.some(cluster => {
          return cluster.department_name && selectedDepartments.includes(cluster.department_name);
        });
      })();

      const idcMatch = selectedIdcs.length === 0 ||
        (predictionItem.idc_info && selectedIdcs.includes(predictionItem.idc_info.idc_name || ''));

      return groupMatch && clusterMatch && departmentMatch && idcMatch;
    });

    return filtered;
  }, [diskPredictionData, selectedGroups, selectedClusters, selectedDepartments, selectedIdcs]);

  // 获取过滤后的唯一集群列表
  const filteredClusters = useMemo(() => {
    const uniqueClusters = new Set<string>();
    filteredData.forEach(item => {
      if (item.clusters && Array.isArray(item.clusters) && item.clusters.length > 0) {
        item.clusters.forEach(cluster => {
          if (cluster.cluster_name) {
            uniqueClusters.add(cluster.cluster_name);
          }
        });
      } else if (item.cluster_name) {
        uniqueClusters.add(item.cluster_name);
      } else {
        uniqueClusters.add('未分配集群');
      }
    });
    return Array.from(uniqueClusters);
  }, [filteredData]);

  const handleSendEmail = async () => {
    if (!emailAddress) {
      message.error('请输入邮件地址');
      return;
    }

    if (contentRef.current) {
      try {
        const canvas = await html2canvas(document.body);
        const imageDataUrl = canvas.toDataURL('image/png');

        const emailContent = `
          <html>
            <body style="font-family: Arial, sans-serif;">
              <h1 style="color: #333;">服务器资源使用情况报告</h1>
              <p>以下是当前服务器资源使用情况的截图：</p>
              <img src="${imageDataUrl}" alt="Server Resources" style="max-width: 100%;" />
            </body>
          </html>
        `;

        const response = await apiClient.axiosPost('cmdb/v1/send-email', {
          to: emailAddress,
          subject: '服务器资源使用情况报告',
          content: emailContent
        });

        if (response.data.success) {
          message.success('邮件发送成功');
        } else {
          message.error('邮件发送失败');
        }
      } catch (error) {
        console.error('发送邮件时出错：', error);
        message.error('邮件发送失败');
      }
    }
  };

  // 构建可用部门列表
  const availableDepartments = useMemo(() => {
    const departments = new Set<string>();

    serverResources.forEach((resource) => {
      if (resource.clusters && Array.isArray(resource.clusters)) {
        resource.clusters.forEach(cluster => {
          // 如果选择了集群组，只显示选中集群组对应的部门
          if (selectedGroups.length > 0) {
            if (selectedGroups.includes(cluster.cluster_group_name || '') && cluster.department_name) {
              departments.add(cluster.department_name);
            }
          } else {
            // 没有选择集群组时，显示所有部门
            if (cluster.department_name) {
              departments.add(cluster.department_name);
            }
          }
        });
      }
    });

    return Array.from(departments).sort();
  }, [serverResources, selectedGroups]);

  let uniqueClusterGroups = Array.from(new Set(clusterGroups
    .filter(group => group && (group.group_name || group.groupName || group.name))
    .map(group => group.group_name || group.groupName || group.name)
    .filter(Boolean)
  ));

  // 如果集群组数据为空，尝试从服务器资源数据中提取
  if (uniqueClusterGroups.length === 0 && serverResources.length > 0) {
    const groupsFromData = new Set<string>();
    serverResources.forEach(resource => {
      if (resource.clusters && Array.isArray(resource.clusters)) {
        resource.clusters.forEach(cluster => {
          if (cluster.cluster_group_name) {
            groupsFromData.add(cluster.cluster_group_name);
          }
        });
      }
    });
    uniqueClusterGroups = Array.from(groupsFromData).sort();
  }

  const uniqueClusters = Array.from(new Set([...filteredClusters]));
  const uniqueIdcs = Array.from(new Set(serverResources
    .filter(item => item.idc_info && item.idc_info.idc_name)
    .map(item => item.idc_info!.idc_name!)
    .filter(Boolean)
  )).sort();

  // 导出功能
  const exportToExcel = (data: any[], filename: string, columns: any[]) => {
    const exportData = data.map(item => {
      const row: any = {};
      columns.forEach(col => {
        if (col.dataIndex) {
          let value = item[col.dataIndex];
          if (col.render && typeof col.render === 'function') {
            // 对于render函数，尝试获取渲染后的纯文本
            const rendered = col.render(value, item);
            if (typeof rendered === 'string') {
              value = rendered;
            }
          }
          row[col.title] = value;
        }
      });
      return row;
    });

    const ws = XLSX.utils.json_to_sheet(exportData);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
    XLSX.writeFile(wb, filename);
  };

  const handleExportResourceAlerts = () => {
    exportToExcel(filteredData, 'resource_alerts.xlsx', getResourceAlertsColumns());
  };

  const handleExportDiskPrediction = () => {
    exportToExcel(filteredDiskPredictionData, 'disk_prediction.xlsx', getDiskPredictionColumns());
  };

  const handleExportServerResource = () => {
    exportToExcel(filteredData, 'server_resources.xlsx', []);
  };

  const renderExportButton = (onExport: () => void) => (
    <Button type="primary" onClick={onExport}>
      导出Excel
    </Button>
  );

  // 更新统计数据
  useEffect(() => {
    if (filteredData.length > 0) {
      updateStats(filteredData);
    }
  }, [filteredData, cpuThresholds, memoryThresholds, diskThresholds]);

  const tabItems: TabsProps['items'] = [
    {
      key: 'resource-alerts',
      label: '资源警报',
      children: (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="资源警报概览">
              <Alert
                message="资源监控"
                description={`正在监控 ${serverResources.length} 台主机的资源使用情况`}
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Row gutter={16}>
                <Col span={8}>
                  <Card size="small" title="CPU警报">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 20, color: '#1890ff' }}>
                        {serverResources.filter(item =>
                          (item.max_cpu_load || 0) < cpuThresholds.min || (item.max_cpu_load || 0) > cpuThresholds.max
                        ).length}
                      </div>
                      <div>台主机</div>
                    </div>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" title="内存警报">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 20, color: '#52c41a' }}>
                        {serverResources.filter(item => {
                          const usage = (item.max_used_memory && item.total_memory) ? (item.max_used_memory / item.total_memory) * 100 : 0;
                          return usage < memoryThresholds.min || usage > memoryThresholds.max;
                        }).length}
                      </div>
                      <div>台主机</div>
                    </div>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" title="磁盘警报">
                    <div style={{ textAlign: 'center' }}>
                      <div style={{ fontSize: 20, color: '#fa8c16' }}>
                        {serverResources.filter(item => {
                          const usage = (item.max_used_disk && item.total_disk) ? (item.max_used_disk / item.total_disk) * 100 : 0;
                          return usage < diskThresholds.min || usage > diskThresholds.max;
                        }).length}
                      </div>
                      <div>台主机</div>
                    </div>
                  </Card>
                </Col>
              </Row>
              <div style={{ marginTop: 16 }}>
                <Alerts
                  data={serverResources}
                  cpuThresholds={cpuThresholds}
                  memoryThresholds={memoryThresholds}
                  diskThresholds={diskThresholds}
                  triggerUpdate={triggerUpdate}
                  selectedGroups={selectedGroups}
                />
              </div>
            </Card>
          </Col>
          <Col span={24}>
            <Card
              title={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>资源警报详情</span>
                  {renderExportButton(handleExportResourceAlerts)}
                </div>
              }
            >
              <ResourceAlerts
                data={serverResources}
                cpuThresholds={cpuThresholds}
                memoryThresholds={memoryThresholds}
                diskThresholds={diskThresholds}
                triggerUpdate={triggerUpdate}
                pagination={true}
              />
            </Card>
          </Col>
        </Row>
      ),
    },
    {
      key: 'disk-prediction',
      label: '磁盘空间预测',
      children: (
        <Card
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>磁盘空间预测</span>
              {diskPredictionLoaded && renderExportButton(handleExportDiskPrediction)}
            </div>
          }
        >
          {isDiskPredictionLoading ? (
            <div style={{ textAlign: 'center', padding: 50 }}>
              <Spin size="large" />
              <p>正在加载磁盘预测数据...</p>
            </div>
          ) : (
            <DiskFullPrediction
              data={filteredDiskPredictionData}
              pagination={true}
            />
          )}
        </Card>
      ),
    },
    {
      key: 'geographic-distribution',
      label: '地域资源分布',
      children: (
        <Card title="地域资源分布">
          <GeographicDistribution data={serverResources} />
        </Card>
      ),
    },
    {
      key: 'server-resource-details',
      label: '服务器资源详情',
      children: (
        <Card
          title={
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span>服务器资源详情</span>
              {renderExportButton(handleExportServerResource)}
            </div>
          }
        >
          <HostResourceDetail
            data={serverResources}
            pagination={true}
            dateRange={dateRange}
            onDateChange={handleDateRangeChange}
            refreshData={() => fetchServerResources(
              dateRange ? dateRange[0] : undefined,
              dateRange ? dateRange[1] : undefined
            )}
            error={null}
            loading={isLoading}
          />
        </Card>
      ),
    },
  ];

  return (
    <ConfigProvider locale={zhCN}>
      <Layout>
        <Content style={{ padding: '20px' }}>
          <Card title="筛选条件" style={{ marginBottom: 16 }}>
            <Row gutter={16}>
              <Col span={8}>
                <label>集群组:</label>
                <Select
                  mode="multiple"
                  style={{ width: '100%' }}
                  placeholder="选择集群组"
                  value={selectedGroups}
                  onChange={handleGroupChange}
                >
                  {uniqueClusterGroups.map(group => (
                    <Option key={group} value={group}>
                      {group}
                    </Option>
                  ))}
                </Select>
              </Col>

              <Col span={8}>
                <label>集群:</label>
                <Select
                  mode="multiple"
                  style={{ width: '100%' }}
                  placeholder="选择集群"
                  value={selectedClusters}
                  onChange={handleClusterChange}
                >
                  {uniqueClusters.map(cluster => (
                    <Option key={cluster} value={cluster}>
                      {cluster}
                    </Option>
                  ))}
                </Select>
              </Col>

              <Col span={8}>
                <label>部门:</label>
                <Select
                  mode="multiple"
                  style={{ width: '100%' }}
                  placeholder="选择部门"
                  value={selectedDepartments}
                  onChange={handleDepartmentChange}
                >
                  {availableDepartments.map(department => (
                    <Option key={department} value={department}>
                      {department}
                    </Option>
                  ))}
                </Select>
              </Col>
            </Row>

            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={8}>
                <label>IDC机房:</label>
                <Select
                  mode="multiple"
                  style={{ width: '100%' }}
                  placeholder="选择IDC机房"
                  value={selectedIdcs}
                  onChange={handleIdcChange}
                >
                  {uniqueIdcs.map(idc => (
                    <Option key={idc} value={idc}>
                      {idc}
                    </Option>
                  ))}
                </Select>
              </Col>

              <Col span={8}>
                <label>时间范围:</label>
                <RangePicker
                  style={{ width: '100%' }}
                  value={dateRange}
                  onChange={handleDateRangeChange}
                  showTime={false}
                  format="YYYY-MM-DD"
                  locale={zhCN}
                />
              </Col>

              <Col span={8}>
                <div style={{ height: '22px' }}></div>
                <Button
                  type="primary"
                  onClick={() => {
                    const startDate = dateRange ? dateRange[0] : undefined;
                    const endDate = dateRange ? dateRange[1] : undefined;
                    fetchServerResources(startDate, endDate);
                    if (diskPredictionLoaded) {
                      fetchDiskPrediction(startDate, endDate);
                    }
                  }}
                  loading={isLoading}
                >
                  查询数据
                </Button>
              </Col>
            </Row>
          </Card>

          <div ref={contentRef}>
            <Tabs
              defaultActiveKey="resource-alerts"
              type="card"
              onChange={handleTabChange}
              items={tabItems}
            />
          </div>
        </Content>
      </Layout>
    </ConfigProvider>
  );
};

export default HostResourceUsageAnalysis;
