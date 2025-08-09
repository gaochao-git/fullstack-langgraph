import React, { useState, useEffect } from 'react';
import { Spin } from 'antd';
import { globalLoadingController } from '@/utils/base_api';

const GlobalLoading: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [delayTimer, setDelayTimer] = useState<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // 设置全局loading控制器
    globalLoadingController.setHandler({
      show: () => {
        // 延迟200ms显示loading，避免闪烁
        const timer = setTimeout(() => {
          setLoading(true);
        }, 200);
        setDelayTimer(timer);
      },
      hide: () => {
        // 清除延迟计时器
        if (delayTimer) {
          clearTimeout(delayTimer);
          setDelayTimer(null);
        }
        setLoading(false);
      }
    });

    // 清理函数
    return () => {
      if (delayTimer) {
        clearTimeout(delayTimer);
      }
    };
  }, [delayTimer]);

  if (!loading) return null;

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.45)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 9999,
      }}
    >
      <Spin size="large" tip="加载中..." />
    </div>
  );
};

export default GlobalLoading;