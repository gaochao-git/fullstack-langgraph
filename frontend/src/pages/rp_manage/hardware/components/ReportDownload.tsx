// @ts-nocheck
import React from 'react';
import { Button } from 'antd';
import apiClient from '../services/apiClient';

const ReportDownload = () => {
  const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8888';

  const handleDownloadClusterGroupReport = async () => {
    try {
      const response = await apiClient.axiosGet('/api/cmdb/v1/cluster-group-report', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'cluster_group_report.xlsx');
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('下载 Cluster Group 报告时出错：', error);
    }
  };

  const handleDownloadIDCReport = async () => {
    try {
      const response = await apiClient.axiosGet('/api/cmdb/v1/idc-report', {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'idc_report.xlsx');
      document.body.appendChild(link);
      link.click();
    } catch (error) {
      console.error('下载 IDC 报告时出错：', error);
    }
  };

  return (
    <div>
      <Button onClick={handleDownloadClusterGroupReport} type="default" style={{ marginRight: '10px' }}>
        下载 Cluster Group 报告
      </Button>
      <Button onClick={handleDownloadIDCReport} type="default">
        下载 IDC 报告
      </Button>
    </div>
  );
};

export default ReportDownload;
