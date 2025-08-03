/**
 * SOP列表管理Hook - 适配新的统一响应格式
 */

import { useState, useEffect, useCallback } from 'react';
import { message } from 'antd';
import { SOPTemplate, SOPListParams } from '../types/sop';
import { SOPApi } from '../../../services/sopApi';

interface UseSOPListReturn {
  // 数据状态
  sops: SOPTemplate[];
  loading: boolean;
  pagination: {
    current: number;
    pageSize: number;
    total: number;
    showSizeChanger: boolean;
    showQuickJumper: boolean;
    showTotal: (total: number, range: [number, number]) => string;
  };
  
  // 操作方法
  fetchSOPs: (params?: SOPListParams) => Promise<void>;
  refreshSOPs: () => Promise<void>;
  handlePageChange: (page: number, size?: number) => void;
  handleSearch: (searchParams: Partial<SOPListParams>) => Promise<void>;
  deleteSOP: (sopId: string) => Promise<void>;
}

export const useSOPList = (initialParams: SOPListParams = {}): UseSOPListReturn => {
  const [sops, setSOPs] = useState<SOPTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentParams, setCurrentParams] = useState<SOPListParams>({
    page: 1,
    size: 10,
    ...initialParams
  });
  const [total, setTotal] = useState(0);

  /**
   * 获取SOP列表
   */
  const fetchSOPs = useCallback(async (params?: SOPListParams) => {
    const queryParams = { ...currentParams, ...params };
    setLoading(true);
    
    try {
      const result = await SOPApi.getSOPs(queryParams);
      
      if (result.success && result.data) {
        setSOPs(result.data.data);
        setTotal(result.data.total);
        setCurrentParams(queryParams);
      } else {
        throw new Error(result.error || '获取SOP列表失败');
      }
    } catch (error) {
      console.error('获取SOP列表失败:', error);
      message.error(error instanceof Error ? error.message : '获取SOP列表失败');
      setSOPs([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [currentParams]);

  /**
   * 刷新SOP列表
   */
  const refreshSOPs = useCallback(async () => {
    await fetchSOPs();
  }, [fetchSOPs]);

  /**
   * 处理分页变化
   */
  const handlePageChange = useCallback((page: number, size?: number) => {
    const newParams = {
      ...currentParams,
      page,
      ...(size && { size })
    };
    fetchSOPs(newParams);
  }, [currentParams, fetchSOPs]);

  /**
   * 处理搜索
   */
  const handleSearch = useCallback(async (searchParams: Partial<SOPListParams>) => {
    const newParams = {
      ...currentParams,
      ...searchParams,
      page: 1 // 搜索时重置到第一页
    };
    await fetchSOPs(newParams);
  }, [currentParams, fetchSOPs]);

  /**
   * 删除SOP
   */
  const deleteSOP = useCallback(async (sopId: string) => {
    try {
      await SOPApi.deleteSOP(sopId);
      message.success('SOP删除成功');
      
      // 如果当前页只有一个项目且不是第一页，则跳转到前一页
      const shouldGoToPrevPage = sops.length === 1 && currentParams.page! > 1;
      const newPage = shouldGoToPrevPage ? currentParams.page! - 1 : currentParams.page;
      
      await fetchSOPs({ ...currentParams, page: newPage });
    } catch (error) {
      console.error('删除SOP失败:', error);
      message.error(error instanceof Error ? error.message : '删除SOP失败');
    }
  }, [sops.length, currentParams, fetchSOPs]);

  // 初始化加载
  useEffect(() => {
    fetchSOPs();
  }, []); // 只在组件挂载时执行一次

  // 构建分页配置
  const pagination = {
    current: currentParams.page || 1,
    pageSize: currentParams.size || 10,
    total,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number, range: [number, number]) => 
      `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`,
  };

  return {
    sops,
    loading,
    pagination,
    fetchSOPs,
    refreshSOPs,
    handlePageChange,
    handleSearch,
    deleteSOP,
  };
};