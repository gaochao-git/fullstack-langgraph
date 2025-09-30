// @ts-nocheck
// 集群有效性报告页面
import React, { useState, useEffect } from 'react';
import { Table, Card, Spin, Button, Modal, Typography, Tag } from 'antd';
import { CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons';
import apiClient from '../services/apiClient';

const { Title } = Typography;

const renderJsonBlock = (value: any) => {
    let parsed = value;

    if (typeof value === 'string') {
        try {
            parsed = JSON.parse(value);
        } catch (error) {
            parsed = { 原始数据: value };
        }
    }

    const isObjectLike = parsed && typeof parsed === 'object';
    const text = isObjectLike ? JSON.stringify(parsed, null, 2) : String(parsed ?? '');

    return (
        <pre
            style={{
                background: '#0f172a',
                color: '#e2e8f0',
                borderRadius: 8,
                padding: 16,
                overflowX: 'auto',
                fontSize: 12,
                lineHeight: 1.6,
            }}
        >
            {text}
        </pre>
    );
};

const ClusterValidityReport = ({ clusterName }) => {
    const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8888';
    const [loading, setLoading] = useState(true);
    const [reportData, setReportData] = useState([]);
    const [detailModalVisible, setDetailModalVisible] = useState(false);
    const [currentDetail, setCurrentDetail] = useState(null);

    useEffect(() => {
        if (clusterName) {
            fetchReportData();
        }
    }, [clusterName]);

    const fetchReportData = () => {
        setLoading(true);
        apiClient.axiosGet('cmdb/v1/backup-restore-check-info', {
            params: { cluster_name: clusterName }
        })
            .then(response => {
                console.log('Backup-restore-check-info API Response:', response.data);
                // 处理 API 返回的数据结构 { "list": [...] }
                let reportList = [];
                if (response.data && Array.isArray(response.data.list)) {
                    reportList = response.data.list;
                } else if (Array.isArray(response.data)) {
                    // 兼容直接返回数组的情况
                    reportList = response.data;
                } else {
                    console.warn('未知的报告数据格式:', response.data);
                    reportList = [];
                }
                console.log('Processed report data:', reportList);
                setReportData(reportList);
                setLoading(false);
            })
            .catch(error => {
                console.error('获取集群有效性报告数据失败:', error);
                setReportData([]);
                setLoading(false);
            });
    };

    const handleViewDetail = (checkSeq) => {
        setLoading(true);
        apiClient.axiosGet('cmdb/v1/cluster-confirm-summary', {
            params: { check_seq: checkSeq }
        })
            .then(response => {
                console.log('Cluster-confirm-summary API Response:', response.data);
                // 处理详情数据结构
                let detailData = null;
                if (response.data && response.data.list && response.data.list.length > 0) {
                    // 如果返回的是 { "list": [...] } 格式，取第一个元素
                    detailData = response.data.list[0];
                } else if (response.data && !response.data.list) {
                    // 如果直接返回对象
                    detailData = response.data;
                } else {
                    console.warn('未知的详情数据格式:', response.data);
                    detailData = response.data;
                }
                console.log('Processed detail data:', detailData);
                setCurrentDetail(detailData);
                setDetailModalVisible(true);
                setLoading(false);
            })
            .catch(error => {
                console.error('获取详情数据失败:', error);
                setCurrentDetail(null);
                setLoading(false);
            });
    };

    const handleCloseDetailModal = () => {
        setDetailModalVisible(false);
    };

    const formatDateTime = (dateTimeStr) => {
        const date = new Date(dateTimeStr);
        return date.toLocaleString();
    };

    // 表格列定义
    const columns = [
        {
            title: 'ID',
            dataIndex: 'id',
            key: 'id',
        },
        {
            title: '检查序列',
            dataIndex: 'check_seq',
            key: 'check_seq',
        },
        {
            title: '集群名称',
            dataIndex: 'check_db',
            key: 'check_db',
        },
        {
            title: '检查源IP',
            dataIndex: 'check_src_ip',
            key: 'check_src_ip',
        },
        {
            title: '备份时间',
            dataIndex: 'db_backup_time',
            key: 'db_backup_time',
            render: (text) => formatDateTime(text),
        },
        {
            title: '备份集名称',
            dataIndex: 'backup_name',
            key: 'backup_name',
        },
        {
            title: '恢复时间',
            dataIndex: 'db_restore_begin_time',
            key: 'db_restore_begin_time',
            render: (text) => formatDateTime(text),
        },
        {
            title: '检查目标IP',
            dataIndex: 'check_dst_ip',
            key: 'check_dst_ip',
        },
        {
            title: '应用名称',
            dataIndex: 'check_app',
            key: 'check_app',
        },
        {
            title: '业务名称',
            dataIndex: 'db_app_line',
            key: 'db_app_line',
        },
        {
            title: '恢复结束时间',
            dataIndex: 'db_restore_end_time',
            key: 'db_restore_end_time',
            render: (text) => formatDateTime(text),
        },
        {
            title: '恢复验证结果',
            dataIndex: 'backup_check_result',
            key: 'backup_check_result',
            render: (text) => {
                if (text === 'OK') {
                    return (
                        <Tag color="green">
                            <CheckCircleOutlined /> 成功
                        </Tag>
                    );
                } else {
                    return (
                        <Tag color="red">
                            <CloseCircleOutlined /> 失败
                        </Tag>
                    );
                }
            },
        },
        {
            title: '其他详情',
            key: 'detail',
            render: (_, record) => (
                <Button 
                    type="primary" 
                    onClick={() => handleViewDetail(record.check_seq)}
                >
                    查看详情
                </Button>
            ),
        },
    ];

    return (
        <div className="cluster-validity-report">
            <Spin spinning={loading}>
                <Card 
                    title={`集群有效性报告 - ${clusterName || '未选择集群'}`}
                    extra={<Button type="primary" onClick={fetchReportData}>刷新数据</Button>}
                >
                    <Table
                        columns={columns}
                        dataSource={Array.isArray(reportData) ? reportData : []}
                        rowKey={(record, index) => {
                            // 安全的 rowKey 生成
                            if (record && record.id) {
                                return record.id;
                            }
                            if (record && record.check_seq) {
                                return record.check_seq;
                            }
                            return `row-${index}`;
                        }}
                        pagination={{
                            showSizeChanger: true,
                            showQuickJumper: true,
                            pageSizeOptions: ['10', '20', '50', '100'],
                            defaultPageSize: 10,
                        }}
                        locale={{
                            emptyText: !loading && Array.isArray(reportData) && reportData.length === 0 ? '暂无报告数据' : '数据加载中...'
                        }}
                    />
                </Card>

                <Modal
                    title="插件运行结果详情"
                    visible={detailModalVisible}
                    onCancel={handleCloseDetailModal}
                    footer={[
                        <Button key="close" onClick={handleCloseDetailModal}>
                            关闭
                        </Button>,
                        <Button 
                            key="download" 
                            type="primary" 
                            onClick={() => window.open(currentDetail?.reportFileURL)}
                            disabled={!currentDetail?.reportFileURL}
                        >
                            下载报告文件
                        </Button>,
                    ]}
                    width={800}
                >
                    {currentDetail && (
                        <div>
                            <Title level={4}>报告文件</Title>
                            <p>
                                {currentDetail.reportFileURL ? (
                                    <a href={currentDetail.reportFileURL} target="_blank" rel="noopener noreferrer">
                                        {currentDetail.reportFileURL}
                                    </a>
                                ) : (
                                    <span style={{ color: '#999' }}>暂无报告文件</span>
                                )}
                            </p>
                            
                            <Title level={4}>插件运行结果</Title>
                            {currentDetail.pluginResults && typeof currentDetail.pluginResults === 'object' ? (
                                Object.keys(currentDetail.pluginResults).map(pluginName => (
                                    <div key={pluginName} style={{ marginBottom: 20 }}>
                                        <Title level={5}>{pluginName}</Title>
                                        {renderJsonBlock(currentDetail.pluginResults[pluginName])}
                                    </div>
                                ))
                            ) : (
                                <div style={{ color: '#999' }}>暂无插件运行结果</div>
                            )}
                        </div>
                    )}
                </Modal>
            </Spin>
        </div>
    );
};

export default ClusterValidityReport; 
