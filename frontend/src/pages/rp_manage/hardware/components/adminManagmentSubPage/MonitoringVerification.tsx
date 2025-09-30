// @ts-nocheck
import React, { useState } from 'react';
import { Button, Card, Typography, message, Spin, Alert, DatePicker, Table, Tag, Statistic, Row, Col } from 'antd';
import { EyeOutlined, DesktopOutlined, CheckCircleOutlined, PieChartOutlined, WarningOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import moment from '../../vendor/moment';
import { getTextColumnSearchProps } from '../../utils/tableUtils';

const { Title, Paragraph, Text } = Typography;
const { RangePicker } = DatePicker;

const MonitoringVerification = () => {
  const [loading, setLoading] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [timeRange, setTimeRange] = useState([
    moment().subtract(7, 'days'),
    moment()
  ]);

  const handleVerifyMonitoring = async () => {
    if (!timeRange || timeRange.length !== 2) {
      message.warning('请选择时间范围');
      return;
    }

    setLoading(true);
    setVerificationResult(null);
    
    try {
      const response = await apiClient.post('cmdb/v1/verify-monitoring-data', {
        start_time: timeRange[0].format('YYYY-MM-DD HH:mm:ss'),
        end_time: timeRange[1].format('YYYY-MM-DD HH:mm:ss')
      });
      
      if (response.data.success === true) {
        setVerificationResult(response.data.data);
        message.success('监控数据核对完成！');
      } else {
        throw new Error(response.data.message || '核对失败');
      }
    } catch (error) {
      console.error('核对失败:', error);
      message.error('核对失败，请检查后端服务');
    } finally {
      setLoading(false);
    }
  };

  const hostsWithoutMonitoringColumns = [
    {
      title: '主机IP',
      dataIndex: 'host_ip',
      key: 'host_ip',
      width: 150,
      ...getTextColumnSearchProps('host_ip', '主机IP'),
    },
    {
      title: '主机名',
      dataIndex: 'host_name',
      key: 'host_name',
      width: 200,
      ...getTextColumnSearchProps('host_name', '主机名'),
    },
    {
      title: '所属资源池',
      dataIndex: 'pool_name',
      key: 'pool_name',
      width: 150,
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 180,
      render: (text) => moment(text).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: () => <Tag color="red">无监控数据</Tag>,
    },
  ];

  return (
    <>
      <Card 
        title={
          <div>
            <EyeOutlined style={{ marginRight: '8px' }} />
            监控数据核对
          </div>
        }
        style={{ marginBottom: '16px' }}
      >
        <Paragraph>
          <Text strong>功能说明：</Text>
          <br />
          此功能用于核对hosts_pool表中的主机是否都有对应的监控数据。
          系统将检查指定时间范围内，哪些主机在server_resource表中没有监控数据记录。
        </Paragraph>

        <div style={{ marginBottom: '16px' }}>
          <div style={{ marginBottom: '8px' }}>• 检查hosts_pool表中的所有主机</div>
          <div style={{ marginBottom: '8px' }}>• 查询server_resource表中的监控数据</div>
          <div style={{ marginBottom: '8px' }}>• 找出在指定时间范围内没有监控数据的主机</div>
          <div style={{ marginBottom: '8px' }}>• 显示详细的核对结果和统计信息</div>
        </div>

        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={12}>
            <div style={{ marginBottom: '8px' }}>
              <Text strong>选择时间范围：</Text>
            </div>
            <RangePicker
              style={{ width: '100%' }}
              showTime
              value={timeRange}
              onChange={(dates) => setTimeRange(dates)}
              format="YYYY-MM-DD HH:mm:ss"
              placeholder={['开始时间', '结束时间']}
            />
          </Col>
          <Col span={12}>
            <div style={{ marginBottom: '8px' }}>
              <Text strong>操作：</Text>
            </div>
            <Button 
              type="primary" 
              size="large"
              loading={loading}
              onClick={handleVerifyMonitoring}
              disabled={loading}
              style={{ width: '100%' }}
            >
              {loading ? '核对中...' : '开始核对监控数据'}
            </Button>
          </Col>
        </Row>
      </Card>

      {loading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>
              <Text>正在核对监控数据，请稍等...</Text>
            </div>
          </div>
        </Card>
      )}

      {verificationResult && (
        <>
          <Card style={{ marginBottom: '16px' }}>
            <Row gutter={16}>
              <Col span={6}>
                <Statistic
                  title="总主机数"
                  value={verificationResult.total_hosts}
                  prefix={<DesktopOutlined />}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="有监控数据"
                  value={verificationResult.hosts_with_monitoring}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="无监控数据"
                  value={verificationResult.hosts_without_monitoring}
                  prefix={<Icon type="exclamation-circle" />}
                  valueStyle={{ color: '#cf1322' }}
                />
              </Col>
              <Col span={6}>
                <Statistic
                  title="监控覆盖率"
                  value={(verificationResult.monitoring_coverage * 100).toFixed(1)}
                  suffix="%"
                  prefix={<PieChartOutlined />}
                  valueStyle={{ 
                    color: verificationResult.monitoring_coverage > 0.8 ? '#3f8600' : '#cf1322' 
                  }}
                />
              </Col>
            </Row>
          </Card>

          {verificationResult.hosts_without_monitoring_list && 
           verificationResult.hosts_without_monitoring_list.length > 0 && (
            <Card
              title={
                <div>
                  <WarningOutlined style={{ marginRight: '8px', color: '#faad14' }} />
                  无监控数据的主机列表
                </div>
              }
            >
              <Table
                dataSource={verificationResult.hosts_without_monitoring_list}
                columns={hostsWithoutMonitoringColumns}
                rowKey="host_ip"
                pagination={{
                  pageSize: 10,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total, range) => 
                    `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`,
                }}
                scroll={{ x: 800 }}
              />
            </Card>
          )}

          {verificationResult.hosts_without_monitoring === 0 && (
            <Card>
              <Alert
                type="success"
                message="监控数据完整"
                description="所有主机在指定时间范围内都有监控数据，监控覆盖率为100%。"
                showIcon
              />
            </Card>
          )}
        </>
      )}
    </>
  );
};

export default MonitoringVerification;
