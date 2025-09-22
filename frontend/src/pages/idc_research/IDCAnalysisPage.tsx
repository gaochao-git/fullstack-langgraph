import React, { useState } from 'react';
import { Card, Badge, Tabs, Button, Space } from 'antd';
import { DatabaseOutlined, DesktopOutlined, ReloadOutlined } from '@ant-design/icons';
import { IDCOverviewCard } from './components/IDCOverviewCard';
import { PerformanceComparison } from './components/PerformanceComparison';
import { RealTimeStatus } from './components/RealTimeStatus';
import { ApplicationMonitoring } from './components/ApplicationMonitoring';
import { ChatDialog } from './components/ChatDialog';
import { mockIDCData } from './data/mockData';
import { IDCData } from './types/idc';


const IDCAnalysisPage: React.FC = () => {
  const [selectedIDCs, setSelectedIDCs] = useState<IDCData[]>([]);
  const [currentView, setCurrentView] = useState<'overview' | 'comparison' | 'applications'>('overview');

  const handleIDCSelect = (idc: IDCData) => {
    setSelectedIDCs(prev => {
      const isSelected = prev.some(selected => selected.id === idc.id);
      if (isSelected) {
        return prev.filter(selected => selected.id !== idc.id);
      } else {
        return [...prev, idc];
      }
    });
  };

  const handleQuerySubmit = (query: string) => {
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('比对') || lowerQuery.includes('对比')) {
      setCurrentView('comparison');
    } else if (lowerQuery.includes('应用') || lowerQuery.includes('业务') || lowerQuery.includes('服务')) {
      setCurrentView('applications');
    } else {
      setCurrentView('overview');
    }
  };

  const clearSelection = () => {
    setSelectedIDCs([]);
  };

  const getTotalStats = () => {
    return {
      totalServers: mockIDCData.reduce((sum, idc) => sum + idc.serverCount, 0),
      avgCpuUsage: Math.round(mockIDCData.reduce((sum, idc) => sum + idc.cpuUsage, 0) / mockIDCData.length),
      avgStability: Math.round(mockIDCData.reduce((sum, idc) => sum + idc.stabilityScore, 0) / mockIDCData.length * 10) / 10,
      healthyCount: mockIDCData.filter(idc => idc.status === 'healthy').length,
    };
  };

  const stats = getTotalStats();

  return (
    <div style={{ minHeight: '100vh', background: '#f0f2f5' }}>
      {/* 头部 */}
      <Card style={{ marginBottom: 24, borderRadius: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <DatabaseOutlined style={{ fontSize: 32, color: '#1890ff' }} />
            <div>
              <h1 style={{ margin: 0, fontSize: 24, fontWeight: 'bold' }}>IDC运行状况监控平台</h1>
              <p style={{ margin: 0, color: '#666', marginTop: 4 }}>多数据中心性能分析与比对系统</p>
            </div>
          </div>
          <ChatDialog onQuerySubmit={handleQuerySubmit} />
        </div>

        {/* 统计概览 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginTop: 16, fontSize: 14 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <DesktopOutlined style={{ color: '#666' }} />
            <span>总服务器: {stats.totalServers.toLocaleString()}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <DesktopOutlined style={{ color: '#666' }} />
            <span>平均CPU: {stats.avgCpuUsage}%</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <DesktopOutlined style={{ color: '#666' }} />
            <span>平均稳定性: {stats.avgStability}</span>
          </div>
          <Badge
            status={stats.healthyCount === mockIDCData.length ? 'success' : 'warning'}
            text={`${stats.healthyCount}/${mockIDCData.length} 数据中心正常运行`}
          />
        </div>
      </Card>

      {/* 主内容区域 */}
      <div style={{ padding: '0 24px' }}>
        <Card>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
            <Tabs
              activeKey={currentView}
              onChange={(key) => setCurrentView(key as 'overview' | 'comparison' | 'applications')}
              type="card"
              items={[
                {
                  label: '数据中心概览',
                  key: 'overview',
                },
                {
                  label: '性能比对分析',
                  key: 'comparison',
                },
                {
                  label: '应用程序监控',
                  key: 'applications',
                },
              ]}
            />

            <Space>
              {selectedIDCs.length > 0 && (
                <>
                  <span style={{ color: '#666', fontSize: 14 }}>
                    已选择 {selectedIDCs.length} 个数据中心
                  </span>
                  <Button size="small" onClick={clearSelection}>
                    清除选择
                  </Button>
                </>
              )}
              <Button icon={<ReloadOutlined />} onClick={() => window.location.reload()}>
                刷新
              </Button>
            </Space>
          </div>

          {currentView === 'overview' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              {/* 实时状态监控 */}
              <RealTimeStatus />

              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                gap: 24
              }}>
                {mockIDCData.map(idc => (
                  <IDCOverviewCard
                    key={idc.id}
                    idc={idc}
                    isSelected={selectedIDCs.some(selected => selected.id === idc.id)}
                    onSelect={() => handleIDCSelect(idc)}
                  />
                ))}
              </div>

              {selectedIDCs.length > 0 && (
                <div>
                  <h3 style={{ marginBottom: 16 }}>已选择数据中心快速比对</h3>
                  <PerformanceComparison selectedIDCs={selectedIDCs} />
                </div>
              )}
            </div>
          )}

          {currentView === 'comparison' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div>
                <h3 style={{ marginBottom: 8 }}>选择要比对的数据中心</h3>
                <p style={{ color: '#666', marginBottom: 16 }}>
                  点击数据中心卡片来选择或取消选择，最多可同时比对5个数据中心
                </p>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                  gap: 16
                }}>
                  {mockIDCData.map(idc => (
                    <IDCOverviewCard
                      key={idc.id}
                      idc={idc}
                      isSelected={selectedIDCs.some(selected => selected.id === idc.id)}
                      onSelect={() => handleIDCSelect(idc)}
                    />
                  ))}
                </div>
              </div>

              <PerformanceComparison selectedIDCs={selectedIDCs} />
            </div>
          )}

          {currentView === 'applications' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <div>
                <h3 style={{ marginBottom: 8 }}>应用程序运行状况监控</h3>
                <p style={{ color: '#666', marginBottom: 16 }}>
                  监控和比较不同数据中心中的应用程序运行情况，包括跨数据中心业务和独有业务的性能分析
                </p>
                {selectedIDCs.length === 0 && (
                  <div style={{
                    marginBottom: 16,
                    padding: 16,
                    backgroundColor: '#e6f7ff',
                    borderRadius: 6,
                    border: '1px solid #91d5ff'
                  }}>
                    <p style={{ margin: 0, color: '#0050b3', fontSize: 14 }}>
                      💡 提示：选择数据中心可以查看特定数据中心的应用运行情况，或查看所有数据中心的应用概览
                    </p>
                  </div>
                )}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
                  gap: 16
                }}>
                  {mockIDCData.map(idc => (
                    <IDCOverviewCard
                      key={idc.id}
                      idc={idc}
                      isSelected={selectedIDCs.some(selected => selected.id === idc.id)}
                      onSelect={() => handleIDCSelect(idc)}
                    />
                  ))}
                </div>
              </div>

              <ApplicationMonitoring selectedIDCs={selectedIDCs} />
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default IDCAnalysisPage;