// @ts-nocheck
import React, { useState } from 'react';
import { Button, Card, Typography, message, Spin, Form, InputNumber, Switch, Collapse, Table, Tag, Progress } from 'antd';
import apiClient from '../../services/apiClient';

const { Title, Paragraph, Text } = Typography;
const { Panel } = Collapse;
const FormItem = Form.Item;

const ExternalCmdbSync = () => {
  const [loading, setLoading] = useState(false);
  const [syncResult, setSyncResult] = useState(null);
  const [formValues, setFormValues] = useState({
    pageSize: 100,
    hostOwner: 0,
    forceUpdate: false
  });

  const handleSync = async () => {
    try {
      setLoading(true);
      setSyncResult(null);

      const requestData = {
        page_size: formValues.pageSize || 100,
        host_owner: formValues.hostOwner || 0,
        force_update: formValues.forceUpdate || false
      };

      const response = await apiClient.post('/api/cmdb/v1/sync-external-cmdb', requestData);
      
      if (response.data.success === true) {
        setSyncResult(response.data);
        message.success('外部CMDB同步成功！');
      } else {
        throw new Error(response.data.message || '同步失败');
      }
    } catch (error) {
      console.error('同步失败:', error);
      let errorMessage = '网络请求失败';
      
      if (error.response && error.response.data) {
        errorMessage = error.response.data.message || errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setSyncResult({
        success: false,
        message: errorMessage
      });
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  // 表格列定义
  const columns = [
    {
      title: '主机名',
      dataIndex: 'host_name',
      key: 'host_name',
      width: 150,
    },
    {
      title: '主机IP',
      dataIndex: 'host_ip',
      key: 'host_ip',
      width: 120,
    },
    {
      title: '主机类型',
      dataIndex: 'host_type',
      key: 'host_type',
      width: 100,
    },
    {
      title: '所有者',
      dataIndex: 'host_owner',
      key: 'host_owner',
      width: 80,
    },
    {
      title: '配置',
      key: 'config',
      width: 150,
      render: (text, record) => (
        <span>
          {record.vcpus}C/{Math.round(record.ram/1024)}G/{record.disk}G
        </span>
      ),
    },
    {
      title: '应用名称',
      dataIndex: 'app_name',
      key: 'app_name',
      width: 120,
    },
    {
      title: '业务组',
      dataIndex: 'biz_group',
      key: 'biz_group',
      width: 100,
    },
    {
      title: '同步状态',
      key: 'status',
      width: 100,
      render: (text, record) => (
        <Tag color={record.success ? 'green' : 'red'}>
          {record.success ? '成功' : '失败'}
        </Tag>
      ),
    },
    {
      title: '同步结果',
      dataIndex: 'message',
      key: 'message',
      ellipsis: true,
    },
  ];

  return (
    <div style={{ padding: 16 }}>
      <Card>
        <Title level={3}>外部CMDB数据同步</Title>
        <Paragraph type="secondary">
          从外部CMDB系统同步主机信息到本地hosts_pool表，支持新增主机和更新已存在主机的配置信息。
        </Paragraph>

        <Form layout="inline" style={{ marginBottom: 24 }}>
          <FormItem label="每页数量">
            <InputNumber 
              min={1} 
              max={500} 
              style={{ width: 120 }} 
              value={formValues.pageSize}
              onChange={(value) => setFormValues({...formValues, pageSize: value})}
              placeholder="单次同步的主机数量"
            />
          </FormItem>

          <FormItem label="主机所有者ID">
            <InputNumber 
              min={0} 
              style={{ width: 150 }} 
              value={formValues.hostOwner}
              onChange={(value) => setFormValues({...formValues, hostOwner: value})}
              placeholder="0表示同步所有"
            />
          </FormItem>

          <FormItem label="强制更新">
            <Switch 
              checked={formValues.forceUpdate}
              onChange={(checked) => setFormValues({...formValues, forceUpdate: checked})}
            />
          </FormItem>

          <FormItem>
            <Button 
              type="primary" 
              onClick={handleSync} 
              loading={loading}
              disabled={loading}
            >
              开始同步
            </Button>
          </FormItem>
        </Form>

        {loading && (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text>正在同步外部CMDB数据，请稍候...</Text>
            </div>
          </div>
        )}

        {syncResult && (
          <Card 
            title="同步结果" 
            type="inner" 
            style={{ marginTop: 16 }}
            headStyle={{ backgroundColor: syncResult.success ? '#f6ffed' : '#fff2f0' }}
          >
            <Alert
              type={syncResult.success ? 'success' : 'error'}
              message={syncResult.message}
              style={{ marginBottom: 16 }}
              showIcon
            />

            {syncResult.success && syncResult.total_hosts > 0 && (
              <>
                <div style={{ marginBottom: 16 }}>
                  <Text strong>同步统计：</Text>
                  <div style={{ marginTop: 8 }}>
                    <Text>总主机数：{syncResult.total_hosts}</Text>
                    <span style={{ margin: '0 16px' }}>|</span>
                    <Text>新增：<Text type="success">{syncResult.synced_hosts}</Text></Text>
                    <span style={{ margin: '0 16px' }}>|</span>
                    <Text>更新：<Text type="warning">{syncResult.updated_hosts}</Text></Text>
                    <span style={{ margin: '0 16px' }}>|</span>
                    <Text>失败：<Text type="danger">{syncResult.failed_hosts}</Text></Text>
                  </div>
                  
                  <Progress
                    percent={Math.round(((syncResult.synced_hosts + syncResult.updated_hosts) / syncResult.total_hosts) * 100)}
                    status={syncResult.failed_hosts > 0 ? 'active' : 'success'}
                    style={{ marginTop: 8 }}
                  />
                </div>

                {syncResult.sync_results && syncResult.sync_results.length > 0 && (
                  <Collapse>
                    <Panel header={`查看详细结果 (${syncResult.sync_results.length}条)`} key="1">
                      <Table
                        dataSource={syncResult.sync_results}
                        columns={columns}
                        pagination={{
                          pageSize: 10,
                          showSizeChanger: true,
                          showQuickJumper: true,
                          showTotal: (total, range) => 
                            `第 ${range[0]}-${range[1]} 条，共 ${total} 条记录`
                        }}
                        scroll={{ x: 1200 }}
                        size="small"
                        rowKey="host_ip"
                      />
                    </Panel>
                  </Collapse>
                )}
              </>
            )}
          </Card>
        )}

        <Card 
          title="使用说明" 
          type="inner" 
          style={{ marginTop: 24, backgroundColor: '#fafafa' }}
        >
          <ul>
            <li><Text strong>每页数量：</Text>控制单次同步的主机数量，数量越大同步速度越快，但对系统压力也越大</li>
            <li><Text strong>主机所有者ID：</Text>可以指定特定所有者的主机进行同步，设置为0表示同步所有主机</li>
            <li><Text strong>强制更新：</Text>开启后会更新已存在主机的配置信息，关闭则跳过已存在的主机</li>
            <li><Text strong>数据来源：</Text>从外部CMDB接口 https://api.cmdb.local.numc.int/v1/host/page 获取数据</li>
            <li><Text strong>同步内容：</Text>主机基础信息、硬件配置、H3C信息和应用部署信息</li>
          </ul>
        </Card>
      </Card>
    </div>
  );
};

export default ExternalCmdbSync;
