/**
 * 知识库详情弹窗组件
 */

import React from 'react';
import { Modal, Descriptions, Tag, Space } from 'antd';
import { KnowledgeBase, VISIBILITY_TEXTS, VISIBILITY_COLORS } from '../types/kb';

interface KBDetailModalProps {
  open: boolean;
  onCancel: () => void;
  knowledgeBase: KnowledgeBase | null;
}

const KBDetailModal: React.FC<KBDetailModalProps> = ({
  open,
  onCancel,
  knowledgeBase
}) => {
  if (!knowledgeBase) return null;

  return (
    <Modal
      title={`知识库详情 - ${knowledgeBase.kb_name}`}
      open={open}
      onCancel={onCancel}
      footer={null}
      width={700}
    >
      <Descriptions column={2} bordered>
        <Descriptions.Item label="知识库名称" span={2}>
          {knowledgeBase.kb_name}
        </Descriptions.Item>
        
        <Descriptions.Item label="描述" span={2}>
          {knowledgeBase.kb_description || '暂无描述'}
        </Descriptions.Item>
        
        <Descriptions.Item label="知识库类型">
          <Tag>{knowledgeBase.kb_type}</Tag>
        </Descriptions.Item>
        
        <Descriptions.Item label="可见性">
          <Tag color={VISIBILITY_COLORS[knowledgeBase.visibility as keyof typeof VISIBILITY_COLORS]}>
            {VISIBILITY_TEXTS[knowledgeBase.visibility as keyof typeof VISIBILITY_TEXTS]}
          </Tag>
        </Descriptions.Item>
        
        <Descriptions.Item label="所有者">
          {knowledgeBase.owner_id}
        </Descriptions.Item>
        
        <Descriptions.Item label="所属部门">
          {knowledgeBase.department || '未设置'}
        </Descriptions.Item>
        
        <Descriptions.Item label="文档数量">
          {knowledgeBase.doc_count} 个
        </Descriptions.Item>
        
        <Descriptions.Item label="分块数量">
          {knowledgeBase.total_chunks} 个
        </Descriptions.Item>
        
        <Descriptions.Item label="标签" span={2}>
          {knowledgeBase.tags && knowledgeBase.tags.length > 0 ? (
            <Space wrap>
              {knowledgeBase.tags.map((tag, index) => (
                <Tag key={index}>{tag}</Tag>
              ))}
            </Space>
          ) : (
            '暂无标签'
          )}
        </Descriptions.Item>
        
        <Descriptions.Item label="创建时间">
          {new Date(knowledgeBase.create_time).toLocaleString()}
        </Descriptions.Item>
        
        <Descriptions.Item label="更新时间">
          {new Date(knowledgeBase.update_time).toLocaleString()}
        </Descriptions.Item>
        
        <Descriptions.Item label="创建人">
          {knowledgeBase.create_by}
        </Descriptions.Item>
        
        <Descriptions.Item label="当前权限">
          <Tag color="blue">
            {knowledgeBase.user_permission === 'owner' ? '所有者' : 
             knowledgeBase.user_permission === 'admin' ? '管理员' :
             knowledgeBase.user_permission === 'write' ? '编辑' : '只读'}
          </Tag>
        </Descriptions.Item>
      </Descriptions>
    </Modal>
  );
};

export default KBDetailModal;