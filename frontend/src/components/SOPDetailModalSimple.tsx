import React from 'react';
import {
  Modal,
  Descriptions,
  Tag,
  Typography,
  Card,
  Space,
  Divider
} from 'antd';
import {
  RobotOutlined,
  UserOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { SOPTemplate, SOPSeverity } from '../types/sop';
import { SOPUtils } from '../services/sopApi.real';

const { Text, Paragraph, Title } = Typography;

interface SOPDetailModalSimpleProps {
  visible: boolean;
  onCancel: () => void;
  sopData: SOPTemplate | null;
}

const SOPDetailModalSimple: React.FC<SOPDetailModalSimpleProps> = ({
  visible,
  onCancel,
  sopData
}) => {
  if (!sopData) return null;

  const steps = SOPUtils.parseSteps(sopData.sop_steps);
  const tools = sopData.tools_required ? SOPUtils.parseTools(sopData.tools_required) : [];

  // 严重性颜色映射
  const getSeverityColor = (severity: SOPSeverity): string => {
    const colors = {
      low: 'blue',
      medium: 'orange', 
      high: 'red',
      critical: 'purple'
    };
    return colors[severity];
  };

  // 严重性文本映射
  const getSeverityText = (severity: SOPSeverity): string => {
    const texts = {
      low: '低',
      medium: '中',
      high: '高', 
      critical: '紧急'
    };
    return texts[severity];
  };

  return (
    <Modal
      title={`SOP详情 - ${sopData.sop_id}`}
      open={visible}
      onCancel={onCancel}
      width={900}
      footer={null}
      destroyOnHidden
    >
      <div className="space-y-6">
        {/* 基本信息 */}
        <Card title="基本信息" size="small">
          <Descriptions column={2}>
            <Descriptions.Item label="SOP ID">
              <Text code>{sopData.sop_id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="分类">
              <Tag color="blue">{sopData.sop_category}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="标题" span={2}>
              <Title level={5} style={{ margin: 0 }}>
                {sopData.sop_title}
              </Title>
            </Descriptions.Item>
            <Descriptions.Item label="严重性">
              <Tag color={getSeverityColor(sopData.sop_severity)}>
                {getSeverityText(sopData.sop_severity)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="负责团队">
              {sopData.team_name}
            </Descriptions.Item>
            <Descriptions.Item label="创建者">
              {sopData.create_by}
            </Descriptions.Item>
            <Descriptions.Item label="更新者">
              {sopData.update_by || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="创建时间">
              {sopData.create_time}
            </Descriptions.Item>
            <Descriptions.Item label="更新时间">
              {sopData.update_time}
            </Descriptions.Item>
          </Descriptions>
          
          {sopData.sop_description && (
            <>
              <Divider />
              <div>
                <Text strong>描述：</Text>
                <Paragraph style={{ marginTop: 8 }}>
                  {sopData.sop_description}
                </Paragraph>
              </div>
            </>
          )}
        </Card>

        {/* 所需工具 */}
        {tools.length > 0 && (
          <Card title="所需工具" size="small">
            <Space wrap>
              {tools.map((tool, index) => (
                <Tag key={index} color="green">
                  {tool}
                </Tag>
              ))}
            </Space>
          </Card>
        )}

        {/* 执行步骤 */}
        <Card title={`执行步骤 (${steps.length}步)`} size="small">
          {steps.map((step, index) => (
            <Card 
              key={index}
              size="small" 
              className="mb-4"
              title={
                <Space>
                  <span>步骤 {step.step}</span>
                  {step.ai_generated && (
                    <Tag icon={<RobotOutlined />} color="purple">
                      AI生成
                    </Tag>
                  )}
                  {step.requires_approval && (
                    <Tag icon={<ExclamationCircleOutlined />} color="orange">
                      需要审批
                    </Tag>
                  )}
                </Space>
              }
            >
              <div className="space-y-3">
                <Paragraph>{step.description}</Paragraph>
                
                <div className="pl-4 border-l-2 border-gray-200">
                  <div className="mb-2">
                    <Text strong>工具：</Text>
                    <Tag color="blue" className="ml-2">
                      {step.tool}
                    </Tag>
                  </div>
                  
                  {step.args && (
                    <div>
                      <Text strong>参数：</Text>
                      <div className="mt-1 p-2 bg-gray-50 rounded">
                        <Text code style={{ whiteSpace: 'pre-wrap' }}>
                          {step.args}
                        </Text>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </Card>

        {/* 建议 */}
        {sopData.sop_recommendations && (
          <Card title="相关建议" size="small">
            <Paragraph>
              {sopData.sop_recommendations}
            </Paragraph>
          </Card>
        )}
      </div>
    </Modal>
  );
};

export default SOPDetailModalSimple;