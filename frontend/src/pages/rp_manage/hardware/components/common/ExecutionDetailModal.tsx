// @ts-nocheck
import React from 'react';
import { 
  Modal, 
  Row, 
  Col, 
  Typography, 
  Tag, 
  Button 
} from 'antd';

const { Text } = Typography;

/**
 * 通用执行详情Modal组件
 * @param {boolean} visible - Modal是否可见
 * @param {function} onCancel - 关闭Modal的回调函数
 * @param {object} record - 执行记录数据
 * @param {object} additionalInfo - 额外信息（如任务名称等）
 */
const ExecutionDetailModal = ({ visible, onCancel, record, additionalInfo = {} }) => {
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

  if (!record) {
    return null;
  }

  return (
    <Modal
      title={`主机 ${record.host_ip} 执行详情`}
      visible={visible}
      onCancel={onCancel}
      footer={[
        <Button key="close" onClick={onCancel}>
          关闭
        </Button>
      ]}
      width={800}
    >
      <div>
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Text strong>任务信息:</Text>
            <div style={{ marginLeft: 16, marginTop: 8 }}>
              {/* 显示任务名称（如果提供） */}
              {additionalInfo.taskName && (
                <p><Text strong>任务名称:</Text> {additionalInfo.taskName}</p>
              )}
              {/* 显示执行ID（如果提供） */}
              {additionalInfo.executionTaskId && (
                <p><Text strong>执行ID:</Text> {additionalInfo.executionTaskId}</p>
              )}
              {/* 显示任务ID */}
              {record.task_id && (
                <p><Text strong>任务ID:</Text> {record.task_id}</p>
              )}
              <p><Text strong>主机IP:</Text> {record.host_ip}</p>
              {/* 显示资源类型（如果有） */}
              {record.resource_type && (
                <p><Text strong>资源类型:</Text> 
                  <Tag color={getResourceTypeColor(record.resource_type)} style={{ marginLeft: 8 }}>
                    {record.resource_type.toUpperCase()}
                  </Tag>
                </p>
              )}
              <p><Text strong>执行状态:</Text> 
                <Tag color={getStatusColor(record.execution_status)} style={{ marginLeft: 8 }}>
                  {getStatusText(record.execution_status)}
                </Tag>
              </p>
              {/* 显示目标阈值（如果有） */}
              {record.target_percent !== undefined && record.target_percent !== null && (
                <p><Text strong>目标阈值:</Text> {record.target_percent}%</p>
              )}
              {/* 显示持续时间（如果有） */}
              {record.duration !== undefined && record.duration !== null && (
                <p><Text strong>持续时间:</Text> {record.duration}秒</p>
              )}
              <p><Text strong>退出代码:</Text> {record.exit_code !== undefined && record.exit_code !== null ? record.exit_code : '-'}</p>
              <p><Text strong>开始时间:</Text> {record.start_time || '-'}</p>
              <p><Text strong>结束时间:</Text> {record.end_time || '-'}</p>
              {/* 显示创建时间（如果有） */}
              {record.create_time && (
                <p><Text strong>创建时间:</Text> {record.create_time}</p>
              )}
            </div>
          </Col>
          
          {/* 执行结果摘要 */}
          {record.result_summary && (
            <Col span={24}>
              <Text strong>执行结果摘要:</Text>
              <div style={{ marginTop: 8, padding: 12, backgroundColor: '#f5f5f5', borderRadius: 4 }}>
                <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                  {record.result_summary}
                </pre>
              </div>
            </Col>
          )}
          
          {/* 标准输出 */}
          {record.stdout_log && (
            <Col span={24}>
              <Text strong>标准输出:</Text>
              <div style={{ 
                marginTop: 8, 
                padding: 12, 
                backgroundColor: '#f6ffed', 
                border: '1px solid #b7eb8f', 
                borderRadius: 4, 
                maxHeight: 300, 
                overflow: 'auto' 
              }}>
                <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                  {record.stdout_log}
                </pre>
              </div>
            </Col>
          )}
          
          {/* 标准错误 */}
          {record.stderr_log && (
            <Col span={24}>
              <Text strong>标准错误:</Text>
              <div style={{ 
                marginTop: 8, 
                padding: 12, 
                backgroundColor: '#fff2f0', 
                border: '1px solid #ffccc7', 
                borderRadius: 4, 
                maxHeight: 300, 
                overflow: 'auto' 
              }}>
                <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                  {record.stderr_log}
                </pre>
              </div>
            </Col>
          )}
          
          {/* SSH错误 */}
          {record.ssh_error && (
            <Col span={24}>
              <Text strong>SSH错误:</Text>
              <div style={{ 
                marginTop: 8, 
                padding: 12, 
                backgroundColor: '#fff1f0', 
                border: '1px solid #ffa39e', 
                borderRadius: 4 
              }}>
                <pre style={{ margin: 0, fontSize: 12, whiteSpace: 'pre-wrap' }}>
                  {record.ssh_error}
                </pre>
              </div>
            </Col>
          )}
        </Row>
      </div>
    </Modal>
  );
};

export default ExecutionDetailModal;