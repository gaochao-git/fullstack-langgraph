import React from 'react';
import { Card } from 'antd';
import { FileSearchOutlined } from '@ant-design/icons';
import ScanTaskList from './ScanTaskList';

/**
 * 敏感数据扫描管理主页面
 * 用于查看扫描任务进度和结果
 */
const SensitiveScanManagement: React.FC = () => {
  return (
    <div>
      <Card>
        <h2 style={{ marginBottom: 24 }}>
          <FileSearchOutlined style={{ marginRight: 8 }} />
          敏感数据扫描任务
        </h2>
        <ScanTaskList />
      </Card>
    </div>
  );
};

export default SensitiveScanManagement;