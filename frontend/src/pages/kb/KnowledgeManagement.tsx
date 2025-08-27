/**
 * 知识库管理页面 - 重定向到新的知识库列表页面
 * @deprecated 使用 KnowledgeBaseList 替代
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Spin } from 'antd';

const KnowledgeManagement: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // 重定向到新的知识库列表页面
    navigate('/kb/list', { replace: true });
  }, [navigate]);

  return (
    <div style={{ textAlign: 'center', padding: '50px' }}>
      <Spin size="large" />
      <div style={{ marginTop: 16 }}>正在跳转到知识库列表...</div>
    </div>
  );
};

export default KnowledgeManagement;