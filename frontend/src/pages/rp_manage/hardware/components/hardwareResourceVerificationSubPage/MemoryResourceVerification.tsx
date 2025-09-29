// @ts-nocheck
import React, { useState, useEffect } from 'react';
import apiClient from '../../services/apiClient';
import ExecutionDetailModal from '../common/ExecutionDetailModal';
import { 
  Card, 
  InputNumber, 
  Button, 
  Upload, 
  message, 
  Table, 
  Modal, 
  Tag, 
  Typography, 
  Spin,
  Icon,
  Row,
  Col,
  Input
} from 'antd';
import { InboxOutlined, PlayCircleOutlined } from '@ant-design/icons';
import { ReloadOutlined } from '@ant-design/icons';

const { Title, Text } = Typography;
const { Dragger } = Upload;

const MemoryResourceVerification = () => {
  const [loading, setLoading] = useState(false);
  const [statusLoading, setStatusLoading] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState([]);
  const [historyModalVisible, setHistoryModalVisible] = useState(false);
  const [historyData, setHistoryData] = useState([]);
  const [selectedHostIp, setSelectedHostIp] = useState('');
  const [historyLoading, setHistoryLoading] = useState(false);
  
  // 表单状态
  const [targetPercent, setTargetPercent] = useState(30);
  const [duration, setDuration] = useState(600);
  const [hostIpList, setHostIpList] = useState([]);
  const [fileUploaded, setFileUploaded] = useState(false);

  // 获取验证状态
  const fetchVerificationStatus = async () => {
    setStatusLoading(true);
    try {
      const result = await apiClient.get('/api/cmdb/v1/hardware-resource-verification-status', { resource_type: 'memory' });
      
      if (result.data.success) {
        setVerificationStatus(result.data.verification_records || []);
      } else {
        message.error(result.data.message || '获取验证状态失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    } finally {
      setStatusLoading(false);
    }
  };

  // 获取历史记录
  const fetchHistoryData = async (hostIp) => {
    setHistoryLoading(true);
    try {
      const result = await apiClient.get('/api/cmdb/v1/hardware-resource-verification-history', { host_ip: hostIp, resource_type: 'memory' });
      
      if (result.data.success) {
        setHistoryData(result.data.history_records || []);
      } else {
        message.error(result.data.message || '获取历史记录失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchVerificationStatus();
    // 定时刷新状态
    const interval = setInterval(() => {
      fetchVerificationStatus();
    }, 10000); // 每10秒刷新一次

    return () => clearInterval(interval);
  }, []);

  // 处理文件上传
  const handleFileUpload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      const lines = text.split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0);
      
      // 简单IP格式验证
      const validIpPattern = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/;
      const validIps = lines.filter(line => validIpPattern.test(line));
      
      if (validIps.length === 0) {
        message.error('文件中没有找到有效的IP地址');
        return;
      }
      
      setHostIpList(validIps);
      setFileUploaded(true);
      message.success(`成功读取到 ${validIps.length} 个有效IP地址`);
    };
    reader.readAsText(file);
    return false; // 阻止自动上传
  };

  // 提交验证请求
  const handleSubmit = async () => {
    // 验证表单数据
    if (!targetPercent || targetPercent < 1 || targetPercent > 100) {
      message.error('请输入有效的内存占用率 (1-100)');
      return;
    }
    
    if (!duration || duration < 60) {
      message.error('执行持续时间至少60秒');
      return;
    }
    
    if (!fileUploaded || hostIpList.length === 0) {
      message.error('请先上传包含主机IP的文件');
      return;
    }

    setLoading(true);
    try {
      const result = await apiClient.post('/api/cmdb/v1/hardware-resource-verification', {
        host_ip_list: hostIpList,
        resource_type: 'memory',
        target_percent: targetPercent,
        duration: duration,
        script_params: JSON.stringify({
          nice_level: "19"
        })
      });
      
      if (result.data.success) {
        message.success(`内存验证任务已提交，任务ID: ${result.data.task_id}`);
        // 重置表单
        setTargetPercent(30);
        setDuration(600);
        setHostIpList([]);
        setFileUploaded(false);
        setTimeout(() => {
          fetchVerificationStatus();
        }, 1000);
      } else {
        message.error(result.data.message || '提交失败');
      }
    } catch (error) {
      message.error('请求失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 查看历史记录
  const showHistory = (hostIp) => {
    setSelectedHostIp(hostIp);
    setHistoryModalVisible(true);
    fetchHistoryData(hostIp);
  };

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

  // 验证状态表格列定义
  const statusColumns = [
    {
      title: '主机IP',
      dataIndex: 'host_ip',
      key: 'host_ip',
      sorter: (a, b) => a.host_ip.localeCompare(b.host_ip),
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索主机IP"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ width: 188, marginBottom: 8, display: 'block' }}
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
      render: (text) => (
        <Button type="link" onClick={() => showHistory(text)}>
          {text}
        </Button>
      ),
    },
    {
      title: '执行状态',
      dataIndex: 'execution_status',
      key: 'execution_status',
      sorter: (a, b) => a.execution_status.localeCompare(b.execution_status),
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
      sorter: (a, b) => a.target_percent - b.target_percent,
      render: (percent) => `${percent}%`,
    },
    {
      title: '执行结果',
      dataIndex: 'result_summary',
      key: 'result_summary',
      filters: [
        { text: '成功', value: 'success' },
        { text: '失败', value: 'failed' },
      ],
      onFilter: (value, record) => {
        if (!record.result_summary) return false;
        try {
          const result = JSON.parse(record.result_summary);
          return value === 'success' ? result.success : !result.success;
        } catch {
          return false;
        }
      },
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
          return '-';
        }
      },
    },
    {
      title: '最后执行时间',
      dataIndex: 'create_time',
      key: 'create_time',
      sorter: (a, b) => new Date(a.create_time) - new Date(b.create_time),
      render: (time) => time ? new Date(time).toLocaleString() : '-',
    },
  ];

  // 执行详情Modal状态
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentRecord, setCurrentRecord] = useState(null);
  
  // 显示执行详情
  const showExecutionDetail = (record) => {
    setCurrentRecord(record);
    setDetailModalVisible(true);
  };

  // 历史记录表格列定义
  const historyColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      ellipsis: true,
      width: 180,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="搜索任务ID"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ width: 188, marginBottom: 8, display: 'block' }}
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
      onFilter: (value, record) => record.task_id.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '目标阈值',
      dataIndex: 'target_percent',
      key: 'target_percent',
      sorter: (a, b) => a.target_percent - b.target_percent,
      render: (percent) => `${percent}%`,
      width: 80,
    },
    {
      title: '持续时间',
      dataIndex: 'duration',
      key: 'duration',
      sorter: (a, b) => a.duration - b.duration,
      render: (duration) => `${duration}秒`,
      width: 80,
    },
    {
      title: '执行状态',
      dataIndex: 'execution_status',
      key: 'execution_status',
      sorter: (a, b) => a.execution_status.localeCompare(b.execution_status),
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
      width: 90,
    },
    {
      title: '退出代码',
      dataIndex: 'exit_code',
      key: 'exit_code',
      sorter: (a, b) => (a.exit_code || 0) - (b.exit_code || 0),
      render: (code) => code || '-',
      width: 80,
    },
    {
      title: '执行时间',
      dataIndex: 'create_time',
      key: 'create_time',
      sorter: (a, b) => new Date(a.create_time) - new Date(b.create_time),
      render: (time) => time ? new Date(time).toLocaleString() : '-',
      width: 150,
    },
    {
      title: '操作',
      key: 'action',
      render: (text, record) => (
        <Button 
          type="link" 
          size="small" 
          onClick={() => showExecutionDetail(record)}
          disabled={!record.stdout_log && !record.stderr_log && !record.result_summary}
        >
          查看详情
        </Button>
      ),
      width: 80,
    },
  ];

  return (
    <div>
      <Card title="内存资源验证配置" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
              预期内存资源占用率 (%)
            </label>
            <InputNumber
              value={targetPercent}
              onChange={setTargetPercent}
              style={{ width: '100%' }}
              placeholder="请输入1-100之间的数值"
              min={1}
              max={100}
            />
          </Col>
          
          <Col span={24}>
            <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
              执行持续时间 (秒)
            </label>
            <InputNumber
              value={duration}
              onChange={setDuration}
              style={{ width: '100%' }}
              placeholder="默认600秒（10分钟）"
              min={60}
            />
          </Col>
          
          <Col span={24}>
            <label style={{ fontWeight: 'bold', marginBottom: '8px', display: 'block' }}>
              主机IP列表文件 {fileUploaded && <Tag color="green">已上传 {hostIpList.length} 个IP</Tag>}
            </label>
            <Dragger
              name="file"
              accept=".txt,.csv"
              beforeUpload={handleFileUpload}
              showUploadList={false}
            >
              <p className="ant-upload-drag-icon">
                <InboxOutlined />
              </p>
              <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
              <p className="ant-upload-hint">
                支持单个文件上传，文件格式为 .txt 或 .csv，每行一个IP地址
              </p>
            </Dragger>
          </Col>
          
          <Col span={24}>
            <Button 
              type="primary" 
              onClick={handleSubmit}
              loading={loading}
              size="large"
              style={{ width: '100%' }}
              disabled={!fileUploaded}
            >
              <PlayCircleOutlined />
              提交内存验证任务
            </Button>
          </Col>
        </Row>
      </Card>

      <Card title="验证状态" extra={
        <Button onClick={fetchVerificationStatus} loading={statusLoading}>
          <ReloadOutlined />
          刷新状态
        </Button>
      }>
        <Spin spinning={statusLoading}>
          <Table
            dataSource={verificationStatus}
            columns={statusColumns}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: '暂无验证记录' }}
          />
        </Spin>
      </Card>

      <Modal
        title={`主机 ${selectedHostIp} 的内存验证历史记录`}
        visible={historyModalVisible}
        onCancel={() => setHistoryModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setHistoryModalVisible(false)}>
            关闭
          </Button>
        ]}
        width={1000}
      >
        <Spin spinning={historyLoading}>
          <Table
            dataSource={historyData}
            columns={historyColumns}
            rowKey="id"
            pagination={{ pageSize: 10 }}
            locale={{ emptyText: '暂无历史记录' }}
          />
        </Spin>
      </Modal>

      {/* 执行详情Modal */}
      <ExecutionDetailModal
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        record={currentRecord}
      />
    </div>
  );
};

export default MemoryResourceVerification;