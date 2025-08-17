import { useEffect, useState } from 'react';
import type { SizeType } from 'antd/es/config-provider/SizeContext';

/**
 * 响应式尺寸 Hook
 * 根据设备类型自动返回对应的 Ant Design 组件尺寸
 * 
 * 设计理念：
 * - 手机端 (< 768px): small (24px) - 节省空间
 * - 平板端 (768px - 1024px): middle (32px) - 平衡体验
 * - 桌面端 (> 1024px): large (40px) - 舒适操作
 */
export const useResponsiveSize = (): {
  size: SizeType;
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
} => {
  const [size, setSize] = useState<SizeType>('middle');
  const [deviceType, setDeviceType] = useState({
    isMobile: false,
    isTablet: false,
    isDesktop: true
  });

  useEffect(() => {
    const checkSize = () => {
      const width = window.innerWidth;
      
      if (width < 768) {
        // 手机端
        setSize('small');
        setDeviceType({
          isMobile: true,
          isTablet: false,
          isDesktop: false
        });
      } else if (width >= 768 && width < 1024) {
        // 平板端
        setSize('middle');
        setDeviceType({
          isMobile: false,
          isTablet: true,
          isDesktop: false
        });
      } else {
        // 桌面端
        setSize('large');
        setDeviceType({
          isMobile: false,
          isTablet: false,
          isDesktop: true
        });
      }
    };

    // 初始检查
    checkSize();

    // 监听窗口大小变化
    window.addEventListener('resize', checkSize);
    
    // 清理事件监听
    return () => {
      window.removeEventListener('resize', checkSize);
    };
  }, []);

  return {
    size,
    ...deviceType
  };
};