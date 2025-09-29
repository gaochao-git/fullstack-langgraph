// @ts-nocheck
import React, { useState, useEffect } from 'react';
import apiClient from '../../services/apiClient';
import ExecutionDetailModal from '../common/ExecutionDetailModal';
import { 
  Card, 
  Table, 
  Button, 
  Modal, 
  Tag, 
  Typography, 
  Row,
  Col,
  Divider,
  Spin,
  Alert
} from 'antd';

const { Title, Text } = Typography;

const ScheduledTaskExecutionDetails = ({ executionTaskId, visible, onCancel }) => {
  const [loading, setLoading] = useState(false);
  const [executionData, setExecutionData] = useState(null);
  const [error, setError] = useState(null);
  
  // 执行详情Modal状态
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentRecord, setCurrentRecord] = useState(null);

  // 状态标签颜色映射
  const getStatusColor = (status) => {
    switch (status) {
      case 'pending': return 'blue';
      case 'running': return 'orange';
      case 'completed': return 'green';
      case 'failed': return 'red';
      default: return 'default';
    }
  };

  // 状态文本映射
  const getStatusText = (status) => {
    switch (status) {
      case 'pending': return '待执行';
      case 'running': return '执行中';
      case 'completed': return '已完成';
      case 'failed': return '执行失败';
      default: return status;
    }
  };

  // 资源类型标签颜色映射
  const getResourceTypeColor = (type) => {
    switch (type) {
      case 'cpu': return 'blue';
      case 'memory': return 'green';
      case 'disk': return 'orange';
      default: return 'default';
    }
  };

  // 获取执行详情
  const fetchExecutionDetails = async () => {
    if (!executionTaskId) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiClient.get(`/api/cmdb/v1/scheduled-tasks/execution-details/${executionTaskId}`);
      
      if (result.data.success) {
        setExecutionData(result.data.data);
      } else {
        setError(result.data.message || '获取执行详情失败');
      }
    } catch (error) {
      setError('请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (visible && executionTaskId) {
      fetchExecutionDetails();
    }
  }, [visible, executionTaskId]);

  // 主机详情表格列定义
  const hostColumns = [
    {
      title: '主机IP',
      dataIndex: 'host_ip',
      key: 'host_ip',
      width: 120,
      sorter: (a, b) => a.host_ip.localeCompare(b.host_ip),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <input
            placeholder="搜索IP"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ width: 188, marginBottom: 8, display: 'block', border: '1px solid #d9d9d9', borderRadius: 4, padding: '8px' }}
          />
          <Button
            type="primary"
            onClick={() => confirm()}
            size="small"
            style={{ width: 90, marginRight: 8 }}
          >
            搜索
          </Button>
          <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
            重置
          </Button>
        </div>
      ),
      onFilter: (value, record) => record.host_ip.toLowerCase().includes(value.toLowerCase()),
      render: (text, record) => (
        <Button 
          type="link" 
          onClick={() => showExecutionDetail(record)}
          style={{ padding: 0, height: 'auto' }}
        >
          {text}
        </Button>
      ),
    },
    {
      title: '资源类型',
      dataIndex: 'resource_type',
      key: 'resource_type',
      width: 100,
      filters: [
        { text: 'CPU', value: 'cpu' },
        { text: '内存', value: 'memory' },
        { text: '磁盘', value: 'disk' },
      ],
      onFilter: (value, record) => record.resource_type === value,
      render: (type) => (
        <Tag color={getResourceTypeColor(type)}>
          {type.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: '执行状态',
      dataIndex: 'execution_status',
      key: 'execution_status',
      width: 100,
      filters: [
        { text: '待执行', value: 'pending' },
        { text: '执行中', value: 'running' },
        { text: '已完成', value: 'completed' },
        { text: '执行失败', value: 'failed' },
      ],
      onFilter: (value, record) => record.execution_status === value,
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {getStatusText(status)}
        </Tag>
      ),
    },
    {
      title: '目标阈值',
      dataIndex: 'target_percent',
      key: 'target_percent',
      width: 80,
      sorter: (a, b) => a.target_percent - b.target_percent,
      render: (percent) => `${percent}%`,
    },
    {
      title: '持续时间',
      dataIndex: 'duration',
      key: 'duration',
      width: 80,
      sorter: (a, b) => a.duration - b.duration,
      render: (duration) => `${duration}秒`,
    },
    {
      title: '开始时间',
      dataIndex: 'start_time',
      key: 'start_time',
      width: 150,
      sorter: (a, b) => new Date(a.start_time) - new Date(b.start_time),
      render: (time) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '结束时间',
      dataIndex: 'end_time',
      key: 'end_time',
      width: 150,
      sorter: (a, b) => new Date(a.end_time) - new Date(b.end_time),
      render: (time) => time ? new Date(time).toLocaleString() : '-',
    },
    {
      title: '退出代码',
      dataIndex: 'exit_code',
      key: 'exit_code',
      width: 80,
      sorter: (a, b) => (a.exit_code || 0) - (b.exit_code || 0),
      render: (code) => code !== undefined && code !== null ? code : '-',
    },
    {
      title: '执行结果',
      dataIndex: 'result_summary',
      key: 'result_summary',
      ellipsis: true,
      render: (summary) => {
        if (!summary) return '-';
        try {
          const result = JSON.parse(summary);
          return result.success ? (
            <Tag color="green">成功</Tag>
          ) : (
            <Tag color="red">失败</Tag>
          );
        } catch {
          return summary;
        }
      },
    },
    {
      title: 'SSH错误',
      dataIndex: 'ssh_error',
      key: 'ssh_error',
      ellipsis: true,
      render: (error) => error || '-',
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      render: (text, record) => (
        <Button 
          type="link" 
          size="small" 
          onClick={() => showExecutionDetail(record)}
          disabled={!record.stdout_log && !record.stderr_log && !record.result_summary}
        >
          查看日志
        </Button>
      ),
    },
  ];

  // 显示执行详情
  const showExecutionDetail = (record) => {
    setCurrentRecord(record);
    setDetailModalVisible(true);
  };

  return (
    <Modal
      title={`任务执行详情 - ${executionData?.task_name || executionTaskId}`}
      visible={visible}
      onCancel={onCancel}
      footer={[
        <Button key="close" onClick={onCancel}>
          关闭
        </Button>
      ]}
      width={1200}
      bodyStyle={{ maxHeight: '80vh', overflow: 'auto' }}
    >
      {error && (
        <Alert
          message="错误"
          description={error}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}
      
      <Spin spinning={loading}>
        {executionData ? (
          <div>
            {/* 执行摘要信息 */}
            <Card title="执行摘要" style={{ marginBottom: 16 }}>
              <Row gutter={16}>
                <Col span={8}>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>任务名称:</Text> {executionData.task_name}
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>执行时间:</Text> {executionData.execution_time}
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>资源类型:</Text>
                    <Tag color={getResourceTypeColor(executionData.resource_type)} style={{ marginLeft: 8 }}>
                      {executionData.resource_type.toUpperCase()}
                    </Tag>
                  </div>
                </Col>
                <Col span={8}>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>目标阈值:</Text> {executionData.target_percent}%
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>持续时间:</Text> {executionData.duration}秒
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>执行状态:</Text>
                    <Tag color={getStatusColor(executionData.execution_status)} style={{ marginLeft: 8 }}>
                      {getStatusText(executionData.execution_status)}
                    </Tag>
                  </div>
                </Col>
                <Col span={8}>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>总主机数:</Text> {executionData.total_hosts}
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>成功主机数:</Text> 
                    <Tag color="green" style={{ marginLeft: 8 }}>
                      {executionData.success_hosts}
                    </Tag>
                  </div>
                  <div style={{ marginBottom: 8 }}>
                    <Text strong>失败主机数:</Text> 
                    <Tag color="red" style={{ marginLeft: 8 }}>
                      {executionData.failed_hosts}
                    </Tag>
                  </div>
                </Col>
              </Row>
            </Card>

            {/* 主机执行详情 */}
            <Card title="主机执行详情">
              <Table
                dataSource={executionData.host_details}
                columns={hostColumns}
                rowKey={(record, index) => `${record.host_ip}-${index}`}
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
                }}
                scroll={{ x: 1200 }}
                locale={{ emptyText: '暂无主机执行记录' }}
              />
            </Card>
          </div>
        ) : (
          !error && <div style={{ textAlign: 'center', padding: '50px' }}>加载中...</div>
        )}
      </Spin>
      
      {/* 执行详情Modal */}
      <ExecutionDetailModal
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        record={currentRecord}
        additionalInfo={{
          taskName: executionData?.task_name,
          executionTaskId: executionData?.execution_task_id
        }}
      />
    </Modal>
  );
};

export default ScheduledTaskExecutionDetails;