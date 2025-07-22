import React, { createContext, useContext, useState, useEffect } from 'react';
import { theme } from 'antd';

export type ThemeMode = 'light' | 'dark' | 'auto';

interface ThemeContextType {
  mode: ThemeMode;
  isDark: boolean;
  setMode: (mode: ThemeMode) => void;
  antdTheme: any;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // 从 localStorage 读取保存的主题，默认为 auto
  const [mode, setModeState] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem('theme-mode');
    return (saved as ThemeMode) || 'auto';
  });

  // 获取系统主题偏好
  const getSystemTheme = (): boolean => {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  };

  // 计算当前是否应该使用暗黑主题
  const isDark = mode === 'dark' || (mode === 'auto' && getSystemTheme());

  // 监听系统主题变化
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      // 只有在 auto 模式下才需要重新渲染
      if (mode === 'auto') {
        // 强制重新渲染以应用系统主题变化
        setModeState('auto');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [mode]);

  // 设置主题模式并保存到 localStorage
  const setMode = (newMode: ThemeMode) => {
    setModeState(newMode);
    localStorage.setItem('theme-mode', newMode);
    
    // 更新 HTML 类名用于 CSS 样式
    if (newMode === 'dark' || (newMode === 'auto' && getSystemTheme())) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  // 初始化时设置 HTML 类名
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  // Antd 主题配置
  const antdTheme = {
    algorithm: isDark ? theme.darkAlgorithm : theme.defaultAlgorithm,
    token: {
      // 自定义品牌色
      colorPrimary: '#3b82f6', // blue-500
      colorSuccess: '#10b981', // emerald-500
      colorWarning: '#f59e0b', // amber-500
      colorError: '#ef4444',   // red-500
      colorInfo: '#06b6d4',    // cyan-500
      
      // 字体配置
      fontSize: 14,
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
      
      // 圆角配置
      borderRadius: 6,
      
      // 自定义暗黑模式下的背景色
      ...(isDark && {
        colorBgContainer: '#1f2937', // gray-800
        colorBgElevated: '#374151',  // gray-700
        colorBgLayout: '#111827',    // gray-900
        colorBgSpotlight: '#1f2937', // gray-800
        colorBorder: '#4b5563',      // gray-600
        colorBorderSecondary: '#374151', // gray-700
        colorText: '#f9fafb',        // gray-50
        colorTextSecondary: '#d1d5db', // gray-300
        colorTextTertiary: '#9ca3af',  // gray-400
        colorTextQuaternary: '#6b7280', // gray-500
      }),
    },
    components: {
      // 自定义组件样式
      Button: {
        fontSize: 14,
        controlHeight: 36,
      },
      Input: {
        fontSize: 14,
        controlHeight: 36,
      },
      Select: {
        fontSize: 14,
        controlHeight: 36,
      },
      // 其他组件配置...
    },
  };

  const value: ThemeContextType = {
    mode,
    isDark,
    setMode,
    antdTheme,
  };

  return (
    <ThemeContext.Provider value={value}>
      {children}
    </ThemeContext.Provider>
  );
};