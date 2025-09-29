// @ts-nocheck
import React, { useState } from 'react';
import { Button, Card, Typography, message, Spin, Alert, Row, Col } from 'antd';
import { SyncOutlined, HddOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';

const { Paragraph, Text } = Typography;

const ClusterGroupSync = () => {
  const [clusterGroupLoading, setClusterGroupLoading] = useState(false);
  const [hostSyncLoading, setHostSyncLoading] = useState(false);
  const [clusterGroupSyncResult, setClusterGroupSyncResult] = useState(null);
  const [hostSyncResult, setHostSyncResult] = useState(null);

  // 暂时注释掉认证检查，允许未登录用户使用
  // if (!isAuthenticated || !token) {
  //   return (
  //     <Card>
  //       <Alert
  //         type="warning"
  //         message="认证失败"
  //         description="请先登录后再使用此功能"
  //         showIcon
  //       />
  //     </Card>
  //   );
  // }

  const handleSyncClusterGroups = async () => {
    setClusterGroupLoading(true);
    setClusterGroupSyncResult(null);
    
    try {
      const response = await apiClient.post('/api/cmdb/v1/sync-cluster-groups');
      
      // 处理成功响应 - 适配实际的API响应格式
      if (response.data.success === true) {
        setClusterGroupSyncResult({
          success: true,
          message: response.data.message,
          syncCount: response.data.synced_count,
          details: response.data.details // 添加详细信息支持
        });
        message.success('集群组数据同步成功！');
      } else {
        throw new Error(response.data.message || '同步失败');
      }
    } catch (error) {
      console.error('同步失败:', error);
      let errorMessage = '网络请求失败';
      
      // 检查是否是认证错误
      if (error.message && error.message.includes('401')) {
        errorMessage = '认证失败，请重新登录';
        message.error('认证已过期，请重新登录');
      } else if (error.response?.status === 401) {
        errorMessage = '认证失败，请重新登录';
        message.error('认证已过期，请重新登录');
      } else {
        errorMessage = error.response?.data?.message || error.message || '网络请求失败';
        message.error('同步失败，请检查后端服务');
      }
      
      setClusterGroupSyncResult({
        success: false,
        message: errorMessage
      });
    } finally {
      setClusterGroupLoading(false);
    }
  };

  const handleSyncHostsFromClusters = async () => {
    setHostSyncLoading(true);
    setHostSyncResult(null);
    
    try {
      const response = await apiClient.post('/api/cmdb/v1/sync-hosts-from-clusters');
      
      // 处理成功响应 - 适配实际的API响应格式
      if (response.data.success === true) {
        setHostSyncResult({
          success: true,
          message: response.data.message,
          syncCount: response.data.synced_count,
          details: response.data.details // 添加详细信息支持
        });
        message.success('主机数据同步成功！');
      } else {
        throw new Error(response.data.message || '同步失败');
      }
    } catch (error) {
      console.error('主机同步失败:', error);
      let errorMessage = '网络请求失败';
      
      // 检查是否是认证错误
      if (error.message && error.message.includes('401')) {
        errorMessage = '认证失败，请重新登录';
        message.error('认证已过期，请重新登录');
      } else if (error.response?.status === 401) {
        errorMessage = '认证失败，请重新登录';
        message.error('认证已过期，请重新登录');
      } else {
        errorMessage = error.response?.data?.message || error.message || '网络请求失败';
        message.error('主机同步失败，请检查后端服务');
      }
      
      setHostSyncResult({
        success: false,
        message: errorMessage
      });
    } finally {
      setHostSyncLoading(false);
    }
  };

  return (
    <>
      <Row gutter={16}>
        <Col span={12}>
          <Card 
            title={
              <div>
                <SyncOutlined style={{ marginRight: '8px' }} />
                集群组数据同步
              </div>
            }
            style={{ marginBottom: '16px' }}
          >
            <Paragraph>
              <Text strong>功能说明：</Text>
              <br />
              此功能将从各个集群表（MySQL、MSSQL、TiDB、GoldenDB）中提取集群信息，
              并同步到cluster_groups表中。同步过程包括：
            </Paragraph>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ marginBottom: '8px' }}>• 从mysql_cluster表提取MySQL集群数据</div>
              <div style={{ marginBottom: '8px' }}>• 从mssql_cluster表提取MSSQL集群数据</div>
              <div style={{ marginBottom: '8px' }}>• 从tidb_cluster表提取TiDB集群数据</div>
              <div style={{ marginBottom: '8px' }}>• 从goldendb_cluster表提取GoldenDB集群数据</div>
              <div style={{ marginBottom: '8px' }}>• 根据cluster_group_name查询对应的部门信息</div>
              <div style={{ marginBottom: '8px' }}>• 更新或插入cluster_groups表记录</div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '24px' }}>
              <Button 
                type="primary" 
                size="large"
                loading={clusterGroupLoading}
                onClick={handleSyncClusterGroups}
                disabled={clusterGroupLoading}
              >
                {clusterGroupLoading ? '同步中...' : '开始同步集群组数据'}
              </Button>
            </div>
          </Card>
        </Col>

        <Col span={12}>
          <Card 
            title={
              <div>
                <HddOutlined style={{ marginRight: '8px' }} />
                主机数据同步
              </div>
            }
            style={{ marginBottom: '16px' }}
          >
            <Paragraph>
              <Text strong>功能说明：</Text>
              <br />
              此功能将从各个数据库实例表中提取主机IP信息，并同步到hosts_pool和hosts_applications表中。
              同步过程包括：
            </Paragraph>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ marginBottom: '8px' }}>• 从mysql_cluster_instance表提取MySQL主机IP</div>
              <div style={{ marginBottom: '8px' }}>• 从mssql_cluster_instance表提取MSSQL主机IP</div>
              <div style={{ marginBottom: '8px' }}>• 从tidb_cluster_instance表提取TiDB主机IP</div>
              <div style={{ marginBottom: '8px' }}>• 从goldendb_cluster_instance表提取GoldenDB主机IP</div>
              <div style={{ marginBottom: '8px' }}>• 结合集群和业务线信息创建主机记录</div>
              <div style={{ marginBottom: '8px' }}>• 同步应用部署信息到hosts_applications表</div>
            </div>

            <div style={{ textAlign: 'center', marginTop: '24px' }}>
              <Button 
                type="primary" 
                size="large"
                loading={hostSyncLoading}
                onClick={handleSyncHostsFromClusters}
                disabled={hostSyncLoading}
                style={{ backgroundColor: '#52c41a', borderColor: '#52c41a' }}
              >
                {hostSyncLoading ? '同步中...' : '开始同步主机数据'}
              </Button>
            </div>
          </Card>
        </Col>
      </Row>

      {clusterGroupLoading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>
              <Text>正在同步集群组数据，请稍等...</Text>
            </div>
          </div>
        </Card>
      )}

      {hostSyncLoading && (
        <Card style={{ marginTop: 16 }}>
          <div style={{ textAlign: 'center', padding: '20px' }}>
            <Spin size="large" />
            <div style={{ marginTop: '16px' }}>
              <Text>正在同步主机数据，请稍等...</Text>
            </div>
          </div>
        </Card>
      )}

      {clusterGroupSyncResult && (
        <Card
          style={{ marginTop: 16 }}
          type={clusterGroupSyncResult.success ? 'success' : 'error'}
        >
          <Alert
            type={clusterGroupSyncResult.success ? 'success' : 'error'}
            message={clusterGroupSyncResult.success ? '集群组同步成功' : '集群组同步失败'}
            description={
              <div>
                <p>{clusterGroupSyncResult.message}</p>
                {clusterGroupSyncResult.success && clusterGroupSyncResult.syncCount > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <p><strong>同步详情：</strong></p>
                    <div style={{ paddingLeft: 16 }}>
                      <p>总同步记录数：<strong>{clusterGroupSyncResult.syncCount}</strong></p>
                      {clusterGroupSyncResult.details && clusterGroupSyncResult.details.length > 0 && (
                        <div>
                          <p>各数据库类型同步情况：</p>
                          <ul style={{ paddingLeft: 20 }}>
                            {clusterGroupSyncResult.details.map((detail, index) => (
                              detail.synced_count > 0 && (
                                <li key={index} style={{ marginBottom: 4 }}>
                                  <strong>{detail.database_type.toUpperCase()}</strong>: 
                                  {detail.synced_count} 个集群组
                                  {detail.cluster_groups && detail.cluster_groups.length > 0 && (
                                    <span style={{ color: '#666', fontSize: '12px' }}>
                                      {' '}({detail.cluster_groups.join(', ')})
                                    </span>
                                  )}
                                </li>
                              )
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            }
            showIcon
          />
        </Card>
      )}

      {hostSyncResult && (
        <Card
          style={{ marginTop: 16 }}
          type={hostSyncResult.success ? 'success' : 'error'}
        >
          <Alert
            type={hostSyncResult.success ? 'success' : 'error'}
            message={hostSyncResult.success ? '主机同步成功' : '主机同步失败'}
            description={
              <div>
                <p>{hostSyncResult.message}</p>
                {hostSyncResult.success && hostSyncResult.syncCount > 0 && (
                  <div style={{ marginTop: 12 }}>
                    <p><strong>同步详情：</strong></p>
                    <div style={{ paddingLeft: 16 }}>
                      <p>总同步主机数：<strong>{hostSyncResult.syncCount}</strong></p>
                      {hostSyncResult.details && hostSyncResult.details.length > 0 && (
                        <div>
                          <p>各数据库类型同步情况：</p>
                          <ul style={{ paddingLeft: 20 }}>
                            {hostSyncResult.details.map((detail, index) => (
                              detail.synced_count > 0 && (
                                <li key={index} style={{ marginBottom: 4 }}>
                                  <strong>{detail.database_type.toUpperCase()}</strong>: 
                                  {detail.synced_count} 个主机
                                </li>
                              )
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            }
            showIcon
          />
        </Card>
      )}
    </>
  );
};

export default ClusterGroupSync;
