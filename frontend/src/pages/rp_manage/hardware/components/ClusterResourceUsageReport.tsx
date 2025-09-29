// @ts-nocheck
// 集群资源用量报告页面
import React, { useState, useEffect } from 'react';
import { Table, Card, Row, Col, Select, DatePicker, Input, Checkbox, Spin, Button, Statistic } from 'antd';
import { WarningOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import apiClient from '../services/apiClient';
import moment from '../vendor/moment';
//import ClusterResourceDetail from './clusterResourceSubPage/ClusterResourceDetail';
import ClusterResourceUsage from './clusterResourceSubPage/ClusterResourceUsage';
import ClusterResourceOverview from './clusterResourceSubPage/ClusterResourceOverview';
//import { getClusterResourceDetailColumns } from './clusterResourceSubPage/ClusterResourceDetail';
import { getClusterResourceColumns } from './clusterResourceSubPage/ClusterResourceUsage';
import XLSX from '../vendor/xlsx';

const { Option } = Select;
const { RangePicker } = DatePicker;

const ClusterResourceReport = ({ onShowValidityReport }) => {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8888';
    const [loading, setLoading] = useState(true);
    const [clusterGroups, setClusterGroups] = useState([]);
    const [clusterData, setClusterData] = useState([]);
    const [filteredData, setFilteredData] = useState([]);
    
    // 筛选条件状态
    const [selectedGroups, setSelectedGroups] = useState([]);
    const [selectedClusters, setSelectedClusters] = useState([]);
    const [selectedDepartments, setSelectedDepartments] = useState([]);
    const [dateRange, setDateRange] = useState(null);
    const [cpuThresholds, setCpuThresholds] = useState({ min: 10, max: 80 });
    const [memoryThresholds, setMemoryThresholds] = useState({ min: 10, max: 80 });
    const [diskThresholds, setDiskThresholds] = useState({ min: 10, max: 80 });
    const [showOnlyNonCompliant, setShowOnlyNonCompliant] = useState(false);
    
    // 统计数据
    const [stats, setStats] = useState({
        totalClusters: 0,
        totalHosts: 0,
        compliantClusters: 0,
        compliantHosts: 0,
        nonCompliantClusters: 0,
        nonCompliantHosts: 0
    });

    useEffect(() => {
        // 获取集群组数据
        apiClient.axiosGet('/api/cmdb/v1/cluster-groups')
            .then(response => {
                // console.log('Cluster Groups API Response:', response.data);
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
                
                // console.log('Processed Cluster Groups List:', clusterGroupsList);
                // console.log('Sample cluster group:', clusterGroupsList[0]);
                setClusterGroups(clusterGroupsList);
            })
            .catch(error => {
                console.error('获取集群组数据失败:', error);
                setClusterGroups([]);
            });
        
        // 获取服务器资源数据
        fetchServerResources();
    }, []);

    // 设置默认日期范围为最近3个月
    useEffect(() => {
        const endDate = moment();
        const startDate = moment().subtract(3, 'months');
        setDateRange([startDate, endDate]);
    }, []);

    useEffect(() => {
        // 当筛选条件变化时，过滤数据
        filterData();
    }, [selectedGroups, selectedClusters, selectedDepartments, dateRange, cpuThresholds, memoryThresholds, diskThresholds, showOnlyNonCompliant, clusterData]);



    const fetchServerResources = () => {
        setLoading(true);
        const params = {
            startDate: moment().subtract(3, 'months').format('YYYY-MM-DD'),
            endDate: moment().format('YYYY-MM-DD')
        };
        
        // 使用新的集群专用接口
        apiClient.axiosGet('/api/cmdb/v1/cluster-resources-max', { params })
            .then(response => {
                let clusterResourcesList = [];
                
                if (Array.isArray(response.data)) {
                    clusterResourcesList = response.data;
                } else if (response.data && response.data.list) {
                    clusterResourcesList = response.data.list;
                } else {
                    console.warn('未知的集群资源数据格式:', response.data);
                    clusterResourcesList = [];
                }
                
                setClusterData(clusterResourcesList);
                setLoading(false);
            })
            .catch(error => {
                console.error('获取服务器资源数据失败:', error);
                setClusterData([]);
                setLoading(false);
            });
    };

    const filterData = () => {
        try {
            // 确保 clusterData 是数组
            if (!Array.isArray(clusterData)) {
                console.warn('filterData: clusterData is not an array:', clusterData);
                setFilteredData([]);
                return;
            }

            let filtered = [...clusterData];
            
            // 按集群组筛选
            if (selectedGroups.length > 0) {
                filtered = filtered.filter(item => item && selectedGroups.includes(item.cluster_group_name));
            }
            
            // 按集群名称筛选
            if (selectedClusters.length > 0) {
                filtered = filtered.filter(item => item && selectedClusters.includes(item.cluster_name));
            }
            
            // 按部门筛选
            if (selectedDepartments.length > 0) {
                filtered = filtered.filter(item => item && selectedDepartments.includes(item.department_name));
            }
            
            // 按日期范围筛选（这里假设数据中有日期字段，实际可能需要调整）
            if (dateRange && dateRange.length === 2) {
                // 日期筛选逻辑，根据实际数据结构调整
            }
            
            // 按阈值筛选
            if (showOnlyNonCompliant) {
                filtered = filtered.filter(item => {
                    if (!item) return false;
                    
                    const cpuUsage = Number(item.max_cpu_load) || 0;
                    const memoryUsage = Number(item.max_memory_usage) || 0;
                    const diskUsage = Number(item.max_disk_usage) || 0;
                    
                    const cpuCompliant = cpuUsage >= cpuThresholds.min && cpuUsage <= cpuThresholds.max;
                    const memoryCompliant = memoryUsage >= memoryThresholds.min && memoryUsage <= memoryThresholds.max;
                    const diskCompliant = diskUsage >= diskThresholds.min && diskUsage <= diskThresholds.max;
                    
                    return !cpuCompliant || !memoryCompliant || !diskCompliant;
                });
            }
            
            // console.log('filterData: filtered result length:', filtered.length);
            setFilteredData(filtered);
        } catch (error) {
            console.error('Error in filterData:', error);
            setFilteredData([]);
        }
    };

    const updateStats = (summaryData) => {
        // 检查数据是否有效
        if (!summaryData || summaryData.length === 0) {
            setStats({
                totalClusters: 0,
                totalHosts: 0,
                compliantClusters: 0,
                compliantHosts: 0,
                nonCompliantClusters: 0,
                nonCompliantHosts: 0
            });
            return;
        }
        
        const compliantClusters = summaryData.filter(item => {
            const cpuCompliant = item.max_cpu >= cpuThresholds.min && item.max_cpu <= cpuThresholds.max;
            const memoryCompliant = item.max_memory >= memoryThresholds.min && item.max_memory <= memoryThresholds.max;
            const diskCompliant = item.max_disk >= diskThresholds.min && item.max_disk <= diskThresholds.max;
            
            return cpuCompliant && memoryCompliant && diskCompliant;
        });
        
        const nonCompliantClusters = summaryData.filter(item => {
            const cpuCompliant = item.max_cpu >= cpuThresholds.min && item.max_cpu <= cpuThresholds.max;
            const memoryCompliant = item.max_memory >= memoryThresholds.min && item.max_memory <= memoryThresholds.max;
            const diskCompliant = item.max_disk >= diskThresholds.min && item.max_disk <= diskThresholds.max;
            
            return !cpuCompliant || !memoryCompliant || !diskCompliant;
        });
        
        // 计算实际主机数量（根据集群IP数量）
        const totalHosts = summaryData.reduce((total, item) => {
            const ipCount = item.cluster_ips ? item.cluster_ips.split(',').length : 1;
            return total + ipCount;
        }, 0);
        
        const compliantHosts = compliantClusters.reduce((total, item) => {
            const ipCount = item.cluster_ips ? item.cluster_ips.split(',').length : 1;
            return total + ipCount;
        }, 0);
        
        const nonCompliantHosts = nonCompliantClusters.reduce((total, item) => {
            const ipCount = item.cluster_ips ? item.cluster_ips.split(',').length : 1;
            return total + ipCount;
        }, 0);
        
        setStats({
            totalClusters: summaryData.length,
            totalHosts: totalHosts,
            compliantClusters: compliantClusters.length,
            compliantHosts: compliantHosts,
            nonCompliantClusters: nonCompliantClusters.length,
            nonCompliantHosts: nonCompliantHosts
        });
    };

    const handleGroupChange = (value) => {
        setSelectedGroups(value);
    };

    const handleClusterChange = (value) => {
        setSelectedClusters(value);
    };

    const handleDepartmentChange = (value) => {
        setSelectedDepartments(value);
    };

    const handleDateRangeChange = (dates) => {
        setDateRange(dates);
    };

    const handleCpuThresholdChange = (type, value) => {
        setCpuThresholds(prev => ({
            ...prev,
            [type]: value
        }));
    };

    const handleMemoryThresholdChange = (type, value) => {
        setMemoryThresholds(prev => ({
            ...prev,
            [type]: value
        }));
    };

    const handleDiskThresholdChange = (type, value) => {
        setDiskThresholds(prev => ({
            ...prev,
            [type]: value
        }));
    };

    const handleShowNonCompliantChange = (e) => {
        setShowOnlyNonCompliant(e.target.checked);
    };

    const handleShowValidityReport = (clusterName) => {
        if (onShowValidityReport) {
            onShowValidityReport(clusterName);
        }
    };



    // 计算集群汇总数据用于主表格显示  
    // 由于现在直接获取集群维度的数据，简化处理逻辑
    const clusterSummaryData = React.useMemo(() => {
        try {
            if (!Array.isArray(filteredData)) {
                return [];
            }
            
            // 直接使用集群资源数据，无需重新聚合
            return filteredData.map(cluster => ({
                id: cluster.cluster_name,
                cluster_name: cluster.cluster_name,
                team: cluster.cluster_group_name,
                department: cluster.department_name,
                max_cpu: cluster.max_cpu_load,
                max_memory: cluster.max_memory_usage,
                max_disk: cluster.max_disk_usage,
                node_count: cluster.node_count,
                cluster_ips: cluster.member_nodes ? 
                    cluster.member_nodes.map(node => node.ip).join(',') : ''
            }));
        } catch (error) {
            console.error('Error calculating clusterSummaryData:', error);
            return [];
        }
    }, [filteredData]);

    // 当 clusterSummaryData 变化时，更新统计数据
    React.useEffect(() => {
        updateStats(clusterSummaryData);
    }, [clusterSummaryData, cpuThresholds, memoryThresholds, diskThresholds]);

    // 获取唯一的集群组、集群和部门列表
    let uniqueGroups = [...new Set(clusterGroups
        .filter(item => item && (item.group_name || item.groupName || item.name))
        .map(item => item.group_name || item.groupName || item.name)
        .filter(Boolean)
    )];
    
    // 如果集群组数据为空，尝试从服务器资源数据中提取
    if (uniqueGroups.length === 0 && clusterData.length > 0) {
        uniqueGroups = [...new Set(clusterData
            .filter(item => item && item.cluster_group_name)
            .map(item => item.cluster_group_name)
            .filter(Boolean)
        )];
    }
    
    const uniqueClusters = [...new Set(clusterData
        .filter(item => item && item.cluster_name)
        .map(item => item.cluster_name)
        .filter(Boolean)
    )];
    const uniqueDepartments = [...new Set(clusterData
        .filter(item => item && item.department_name)
        .map(item => item.department_name)
        .filter(Boolean)
    )];
    

    // 修改导出函数，使其使用表格组件的实际数据和列
    const exportToExcel = (columns, dataSource, fileName) => {
        const exportData = dataSource.map(record => {
            const row = {};
            columns.forEach(col => {
                if (col.dataIndex) {
                    let value;
                    if (Array.isArray(col.dataIndex)) {
                        // 处理复合字段
                        value = col.render ? col.render(null, record) : record[col.dataIndex[0]];
                    } else {
                        // 处理单一字段
                        value = col.render ? col.render(record[col.dataIndex], record) : record[col.dataIndex];
                    }
                    // 如果值是 React 元素（带有颜色的 span），则提取其文本内容
                    if (value && value.props && value.props.children) {
                        value = value.props.children;
                    }
                    row[col.title] = value;
                }
            });
            return row;
        });
        
        const ws = XLSX.utils.json_to_sheet(exportData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');
        XLSX.writeFile(wb, `${fileName}.xlsx`);
    };

    // 为每个表格添加导出按钮的渲染函数
    const renderExportButton = (onClick) => (
        <Button
            type="primary"
            size="small"
            onClick={onClick}
            style={{ float: 'right', marginLeft: '10px' }}
        >
            导出Excel
        </Button>
    );

    // 导出处理函数
    const handleExportClusterResource = () => {
        const columns = getClusterResourceColumns();
        exportToExcel(columns, clusterResourceData, '集群资源使用情况');
    };

    // const handleExportServerResource = () => {
    //     const columns = getClusterResourceDetailColumns();
    //     exportToExcel(columns, filteredData, '服务器资源详情');
    // };

    // 计算集群资源数据
    const clusterResourceData = React.useMemo(() => {
        const aggregated = filteredData.reduce((acc, resource) => {
            const clusterName = resource.cluster_name || '未分配集群';
            const groupName = resource.team || resource.group_name || '未分组';
            // 直接使用API返回的百分比数据
            const memoryUsage = Number(resource.max_memory_usage) || 0;
            const diskUsage = Number(resource.max_disk_usage) || 0;
            const cpuLoad = Number(resource.max_cpu_load) || 0;

            // 保留原始数据用于显示
            const totalMem = Number(resource.total_memory) || 0;
            const totalDisk = Number(resource.total_disk) || 0;
            const usedMem = Number(resource.max_used_memory) || 0;
            const usedDisk = Number(resource.max_used_disk) || 0;

            const baseCluster = {
                clusterName: clusterName,
                groupName: groupName,
                memory: memoryUsage,
                memoryTotal: totalMem,
                memoryUsed: usedMem,
                disk: diskUsage,
                diskTotal: totalDisk,
                diskUsed: usedDisk,
                cpu: cpuLoad,
                rawData: resource
            };

            const existingCluster = acc.find(item => item.clusterName === clusterName);
            if (existingCluster) {
                // 累加用于计算平均值的数据
                existingCluster.memory += memoryUsage;
                existingCluster.memoryTotal += totalMem;
                existingCluster.memoryUsed += usedMem;
                existingCluster.disk += diskUsage;
                existingCluster.diskTotal += totalDisk;
                existingCluster.diskUsed += usedDisk;
                existingCluster.cpu += cpuLoad;
                existingCluster.count += 1;

                // 🔧 修复：正确计算最大使用率（取百分比的最大值）
                existingCluster.maxMemory = Math.max(existingCluster.maxMemory, memoryUsage);
                existingCluster.maxDisk = Math.max(existingCluster.maxDisk, diskUsage);
                existingCluster.maxCPU = Math.max(existingCluster.maxCPU, cpuLoad);
                existingCluster.minMemory = Math.min(existingCluster.minMemory, memoryUsage);
                existingCluster.minDisk = Math.min(existingCluster.minDisk, diskUsage);
                existingCluster.minCPU = Math.min(existingCluster.minCPU, cpuLoad);

                // 调试：显示异常数据，特别标注集群归属
                if (memoryUsage > 100 || diskUsage > 100 || cpuLoad > 100 || clusterName.includes('payment') || clusterName === 'payment-mysql-cluster-01') {
                    console.log(`🚨 [${clusterName || '未分配集群'}] 发现${memoryUsage > 100 || diskUsage > 100 ? '异常' : ''}数据:`, {
                        ip: resource.ip,
                        host_name: resource.host_name,
                        原始集群名: resource.cluster_name,
                        显示集群名: clusterName || '未分配集群',
                        组名: groupName,
                        cpu: `${cpuLoad}%`,
                        memory: `${memoryUsage.toFixed(2)}%`,
                        disk: `${diskUsage.toFixed(2)}%`,
                        当前最大值: {
                            maxCPU: existingCluster.maxCPU.toFixed(2),
                            maxMemory: existingCluster.maxMemory.toFixed(2),
                            maxDisk: existingCluster.maxDisk.toFixed(2)
                        }
                    });
                }

                existingCluster.cpuDetails.push(cpuLoad);
                existingCluster.memoryDetails.push(memoryUsage);
                existingCluster.diskDetails.push(diskUsage);
                existingCluster.rawServers.push(resource);
            } else {
                // 调试：显示新集群初始化数据
                if (memoryUsage > 100 || diskUsage > 100 || cpuLoad > 100 || clusterName.includes('payment') || clusterName === 'payment-mysql-cluster-01') {
                    console.log(`🆕 [${clusterName}] 新集群初始化${memoryUsage > 100 || diskUsage > 100 ? '（包含异常数据）' : ''}:`, {
                        ip: resource.ip,
                        host_name: resource.host_name,
                        cpu: `${cpuLoad}%`,
                        memory: `${memoryUsage.toFixed(2)}%`,
                        disk: `${diskUsage.toFixed(2)}%`,
                        初始最大值: {
                            maxCPU: cpuLoad.toFixed(2),
                            maxMemory: memoryUsage.toFixed(2),
                            maxDisk: diskUsage.toFixed(2)
                        }
                    });
                }

                acc.push({
                    ...baseCluster,
                    count: 1,
                    maxMemory: memoryUsage,
                    maxDisk: diskUsage,
                    maxCPU: cpuLoad,
                    minMemory: memoryUsage,
                    minDisk: diskUsage,
                    minCPU: cpuLoad,
                    cpuDetails: [cpuLoad],
                    memoryDetails: [memoryUsage],
                    diskDetails: [diskUsage],
                    rawServers: [resource]
                });
            }
            return acc;
        }, []);

        aggregated.forEach(cluster => {
            if (cluster.count > 0) {
                cluster.memory /= cluster.count;
                cluster.disk /= cluster.count;
                cluster.cpu /= cluster.count;
            }

            // 调试：显示最终汇总结果
            if (cluster.maxMemory > 100 || cluster.maxDisk > 100 || cluster.maxCPU > 100 || cluster.clusterName.includes('payment')) {
                console.log(`📊 [${cluster.clusterName}] 最终汇总结果${cluster.maxMemory > 100 || cluster.maxDisk > 100 ? '（包含异常值）' : ''}:`, {
                    服务器数量: cluster.count,
                    平均值: {
                        cpu: cluster.cpu.toFixed(2),
                        memory: cluster.memory.toFixed(2),
                        disk: cluster.disk.toFixed(2)
                    },
                    最大值: {
                        maxCPU: cluster.maxCPU.toFixed(2),
                        maxMemory: cluster.maxMemory.toFixed(2),
                        maxDisk: cluster.maxDisk.toFixed(2)
                    },
                    所有内存使用率: cluster.memoryDetails.map(v => v.toFixed(2)),
                    所有磁盘使用率: cluster.diskDetails.map(v => v.toFixed(2)),
                    所有CPU使用率: cluster.cpuDetails.map(v => v.toFixed(2))
                });
            }
        });

        // 最终调试：列出所有集群的最大值
        console.log('🎯 所有集群最终结果汇总:', 
            aggregated.map(cluster => ({
                集群名: cluster.clusterName,
                组名: cluster.groupName,
                服务器数量: cluster.count,
                CPU最大值: cluster.maxCPU.toFixed(2) + '%',
                内存最大值: cluster.maxMemory.toFixed(2) + '%',
                磁盘最大值: cluster.maxDisk.toFixed(2) + '%'
            }))
        );

        return aggregated;
    }, [filteredData]);

    return (
        <div className="cluster-resource-report">
            <Spin spinning={loading}>
                <Card title="筛选条件" style={{ marginBottom: 16 }}>
                    <Row gutter={[16, 16]}>
                        <Col span={8}>
                            <div>集群组</div>
                            <Select
                                mode="multiple"
                                style={{ width: '100%' }}
                                placeholder="选择集群组"
                                value={selectedGroups}
                                onChange={handleGroupChange}
                                loading={uniqueGroups.length === 0 && clusterGroups.length === 0}
                                notFoundContent={
                                    uniqueGroups.length === 0 
                                        ? '没有可用的集群组' 
                                        : '未找到匹配的集群组'
                                }
                            >
                                {uniqueGroups.map(group => (
                                    <Option key={group} value={group}>{group}</Option>
                                ))}
                            </Select>
                        </Col>
                        <Col span={8}>
                            <div>集群</div>
                            <Select
                                mode="multiple"
                                style={{ width: '100%' }}
                                placeholder="选择集群"
                                value={selectedClusters}
                                onChange={handleClusterChange}
                            >
                                {uniqueClusters.map(cluster => (
                                    <Option key={cluster} value={cluster}>{cluster}</Option>
                                ))}
                            </Select>
                        </Col>
                        <Col span={8}>
                            <div>部门</div>
                            <Select
                                mode="multiple"
                                style={{ width: '100%' }}
                                placeholder="选择部门"
                                value={selectedDepartments}
                                onChange={handleDepartmentChange}
                            >
                                {uniqueDepartments.map(department => (
                                    <Option key={department} value={department}>{department}</Option>
                                ))}
                            </Select>
                        </Col>
                        <Col span={8}>
                            <div>日期范围</div>
                            <RangePicker 
                                style={{ width: '100%' }}
                                onChange={handleDateRangeChange}
                                value={dateRange}
                            />
                        </Col>
                        <Col span={8}>
                            <div>CPU利用率阈值 (%)</div>
                            <Input.Group compact>
                                <Input
                                    style={{ width: '45%' }}
                                    placeholder="最低"
                                    type="number"
                                    value={cpuThresholds.min}
                                    onChange={(e) => handleCpuThresholdChange('min', parseFloat(e.target.value))}
                                />
                                <Input
                                    style={{ width: '10%', textAlign: 'center', pointerEvents: 'none' }}
                                    placeholder="~"
                                    disabled
                                    value="~"
                                />
                                <Input
                                    style={{ width: '45%' }}
                                    placeholder="最高"
                                    type="number"
                                    value={cpuThresholds.max}
                                    onChange={(e) => handleCpuThresholdChange('max', parseFloat(e.target.value))}
                                />
                            </Input.Group>
                        </Col>
                        <Col span={8}>
                            <div>内存利用率阈值 (%)</div>
                            <Input.Group compact>
                                <Input
                                    style={{ width: '45%' }}
                                    placeholder="最低"
                                    type="number"
                                    value={memoryThresholds.min}
                                    onChange={(e) => handleMemoryThresholdChange('min', parseFloat(e.target.value))}
                                />
                                <Input
                                    style={{ width: '10%', textAlign: 'center', pointerEvents: 'none' }}
                                    placeholder="~"
                                    disabled
                                    value="~"
                                />
                                <Input
                                    style={{ width: '45%' }}
                                    placeholder="最高"
                                    type="number"
                                    value={memoryThresholds.max}
                                    onChange={(e) => handleMemoryThresholdChange('max', parseFloat(e.target.value))}
                                />
                            </Input.Group>
                        </Col>
                        <Col span={8}>
                            <div>磁盘利用率阈值 (%)</div>
                            <Input.Group compact>
                                <Input
                                    style={{ width: '45%' }}
                                    placeholder="最低"
                                    type="number"
                                    value={diskThresholds.min}
                                    onChange={(e) => handleDiskThresholdChange('min', parseFloat(e.target.value))}
                                />
                                <Input
                                    style={{ width: '10%', textAlign: 'center', pointerEvents: 'none' }}
                                    placeholder="~"
                                    disabled
                                    value="~"
                                />
                                <Input
                                    style={{ width: '45%' }}
                                    placeholder="最高"
                                    type="number"
                                    value={diskThresholds.max}
                                    onChange={(e) => handleDiskThresholdChange('max', parseFloat(e.target.value))}
                                />
                            </Input.Group>
                        </Col>
                        <Col span={8}>
                            <Checkbox 
                                checked={showOnlyNonCompliant}
                                onChange={handleShowNonCompliantChange}
                            >
                                只显示不达标集群的数据
                            </Checkbox>
                        </Col>
                    </Row>
                </Card>

                <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="集群数量"
                                value={stats.totalClusters}
                                prefix={<WarningOutlined />}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="主机数量"
                                value={stats.totalHosts}
                                prefix={<WarningOutlined />}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="达标集群数量/主机数量"
                                value={`${stats.compliantClusters}/${stats.compliantHosts}`}
                                prefix={<CheckCircleOutlined style={{ color: 'green' }} />}
                            />
                        </Card>
                    </Col>
                    <Col span={6}>
                        <Card>
                            <Statistic
                                title="不达标集群数量/主机数量"
                                value={`${stats.nonCompliantClusters}/${stats.nonCompliantHosts}`}
                                prefix={<CloseCircleOutlined style={{ color: 'red' }} />}
                            />
                        </Card>
                    </Col>
                </Row>

                <Card title="集群资源用量数据">
                    <ClusterResourceOverview
                        data={clusterSummaryData}
                        cpuThresholds={cpuThresholds}
                        memoryThresholds={memoryThresholds}
                        diskThresholds={diskThresholds}
                        handleShowValidityReport={handleShowValidityReport}
                    />
                </Card>
                
                <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                    <Col span={24} key="cluster-resource-usage">
                        <Card 
                            title={
                                <div>
                                    集群资源使用情况
                                    {renderExportButton(handleExportClusterResource)}
                                </div>
                            }
                        >
                            <ClusterResourceUsage dateRange={dateRange} data={clusterResourceData} />
                        </Card>
                    </Col>
                    {/* <Col span={24} key="server-resource-details">
                        <Card 
                            title={
                                <div>
                                    服务器资源详情
                                    {renderExportButton(handleExportServerResource)}
                                </div>
                            }
                        >
                            <ClusterResourceDetail data={filteredData} pagination={false} />
                        </Card>
                    </Col> */}
                </Row>
            </Spin>
        </div>
    );
};

export default ClusterResourceReport;
