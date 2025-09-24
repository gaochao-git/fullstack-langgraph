import React, { useState } from 'react';
import '../../globals_xgq.css';
import { EnhancedChatPanel } from './components/EnhancedChatPanel';
import { IDCOverviewCard } from './components/IDCOverviewCard';
import { IDCOverviewDashboard } from './components/IDCOverviewDashboard';
import { PerformanceComparison } from './components/PerformanceComparison';
import { RealTimeStatus } from './components/RealTimeStatus';
import { ApplicationMonitoring } from './components/ApplicationMonitoring';
import { DomesticSubstitutionMonitoring } from './components/DomesticSubstitutionMonitoring';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from './components/ui/resizable';
import { mockIDCData } from './data/mockData';
import { IDCData } from './types/idc';
import { BarChart3, Activity, Database, TrendingUp } from 'lucide-react';

const IDCAnalysisPage: React.FC = () => {
  const [selectedIDCs, setSelectedIDCs] = useState<IDCData[]>([]);
  const [currentView, setCurrentView] = useState<'overview' | 'comparison' | 'applications' | 'substitution'>('overview');
  const [isChatMinimized, setIsChatMinimized] = useState(false);

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
    } else if (lowerQuery.includes('替换') || lowerQuery.includes('替代') || lowerQuery.includes('国产')) {
      setCurrentView('substitution');
    } else {
      setCurrentView('overview');
    }
  };

  const clearSelection = () => {
    setSelectedIDCs([]);
  };

  const handleToggleChatMinimize = () => {
    setIsChatMinimized(!isChatMinimized);
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
    <div className="min-h-screen bg-background flex flex-col">
      {/* 头部 */}
      <header className="border-b bg-card flex-shrink-0">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Database className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-2xl font-bold">IDC运行状况监控平台</h1>
                <p className="text-muted-foreground">智能AI驱动的多数据中心分析系统</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              {/* 统计概览 */}
              <div className="flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <Activity className="h-4 w-4 text-muted-foreground" />
                  <span>总服务器: {stats.totalServers.toLocaleString()}</span>
                </div>
                <div className="flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-muted-foreground" />
                  <span>平均CPU: {stats.avgCpuUsage}%</span>
                </div>
                <div className="flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-muted-foreground" />
                  <span>平均稳定性: {stats.avgStability}</span>
                </div>
                <Badge variant="secondary">
                  {stats.healthyCount}/{mockIDCData.length} 数据中心正常运行
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区域 - 使用可调整大小的面板 */}
      <div className="flex-1 container mx-auto px-6 py-6">
        <ResizablePanelGroup direction="horizontal" className="h-full">
          {/* 左侧主内容面板 */}
          <ResizablePanel defaultSize={isChatMinimized ? 100 : 70} minSize={50}>
            <div className="h-full pr-3">
              <Tabs value={currentView} onValueChange={(value) => setCurrentView(value as 'overview' | 'comparison' | 'applications' | 'substitution')}>
                <div className="flex items-center justify-between mb-6">
                  <TabsList>
                    <TabsTrigger value="overview">数据中心概览</TabsTrigger>
                    <TabsTrigger value="comparison">性能比对分析</TabsTrigger>
                    <TabsTrigger value="applications">应用程序监控</TabsTrigger>
                    <TabsTrigger value="substitution">国产替代监控</TabsTrigger>
                  </TabsList>

                  {selectedIDCs.length > 0 && (
                    <div className="flex items-center gap-4">
                      <span className="text-sm text-muted-foreground">
                        已选择 {selectedIDCs.length} 个数据中心
                      </span>
                      <Button variant="outline" size="sm" onClick={clearSelection}>
                        清除选择
                      </Button>
                    </div>
                  )}
                </div>

                <div className="h-[calc(100vh-200px)] overflow-auto">
                  <TabsContent value="overview" className="space-y-6 mt-0">
                    {/* 实时状态监控 */}
                    <RealTimeStatus />

                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                      {mockIDCData.map(idc => (
                        <IDCOverviewCard
                          key={idc.id}
                          idc={idc}
                          isSelected={selectedIDCs.some(selected => selected.id === idc.id)}
                          onSelect={() => handleIDCSelect(idc)}
                        />
                      ))}
                    </div>

                    {/* IDC综合概览仪表板 */}
                    <IDCOverviewDashboard />
                  </TabsContent>

                  <TabsContent value="comparison" className="space-y-6 mt-0">
                    <div className="mb-6">
                      <h2 className="text-xl font-semibold mb-2">选择要比对的数据中心</h2>
                      <p className="text-muted-foreground mb-4">
                        点击数据中心卡片来选择或取消选择，最多可同时比对5个数据中心
                      </p>
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
                  </TabsContent>

                  <TabsContent value="applications" className="space-y-6 mt-0">
                    <div className="mb-6">
                      <h2 className="text-xl font-semibold mb-2">应用程序运行状况监控</h2>
                      <p className="text-muted-foreground mb-4">
                        监控和比较不同数据中心中的应用程序运行情况，包括跨数据中心业务和独有业务的性能分析
                      </p>
                      {selectedIDCs.length === 0 && (
                        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                          <p className="text-sm text-blue-700 dark:text-blue-300">
                            💡 提示：选择数据中心可以查看特定数据中心的应用运行情况，或查看所有数据中心的应用概览
                          </p>
                        </div>
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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
                  </TabsContent>

                  <TabsContent value="substitution" className="space-y-6 mt-0">
                    <div className="mb-6">
                      <h2 className="text-xl font-semibold mb-2">国产替代监控</h2>
                      <p className="text-muted-foreground mb-4">
                        监控各数据中心的国产硬件软件替代情况，包括服务器、网络、存储、操作系统、数据库等产品的替代率、品牌分布和故障率分析
                      </p>
                      {selectedIDCs.length === 0 && (
                        <div className="mb-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                          <p className="text-sm text-blue-700 dark:text-blue-300">
                            💡 提示：选择数据中心可以查看特定数据中心的国产替代情况，或查看所有数据中心的替代概览
                          </p>
                        </div>
                      )}
                      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
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

                    <DomesticSubstitutionMonitoring selectedIDCs={selectedIDCs} />
                  </TabsContent>
                </div>
              </Tabs>
            </div>
          </ResizablePanel>

          {/* 可调整大小的分隔符 */}
          {!isChatMinimized && (
            <>
              <ResizableHandle withHandle />

              {/* 右侧AI对话面板 */}
              <ResizablePanel defaultSize={30} minSize={25} maxSize={50}>
                <div className="h-full pl-3">
                  <div className="h-[calc(100vh-140px)]">
                    <EnhancedChatPanel
                      onQuerySubmit={handleQuerySubmit}
                      isMinimized={false}
                      onToggleMinimize={handleToggleChatMinimize}
                    />
                  </div>
                </div>
              </ResizablePanel>
            </>
          )}
        </ResizablePanelGroup>

        {/* 最小化的AI助手 */}
        {isChatMinimized && (
          <EnhancedChatPanel
            onQuerySubmit={handleQuerySubmit}
            isMinimized={true}
            onToggleMinimize={handleToggleChatMinimize}
          />
        )}
      </div>
    </div>
  );
};

export default IDCAnalysisPage;
