import React from 'react';
import { Layout } from 'antd';

const { Content } = Layout;

interface MobileLayoutProps {
  children: React.ReactNode;
  className?: string;
  padding?: boolean;
}

export const MobileLayout: React.FC<MobileLayoutProps> = ({
  children,
  className = '',
  padding = true,
}) => {
  return (
    <div className={`mobile-h-screen flex flex-col ${className}`}>
      <Content 
        className={`flex-1 overflow-auto ${padding ? 'mobile-p-safe' : ''}`}
        style={{
          // 使用 CSS 变量确保在不同移动设备上正确显示
          height: 'calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom))',
          maxHeight: '100vh',
        }}
      >
        {children}
      </Content>
    </div>
  );
};

interface MobileCardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
}

export const MobileCard: React.FC<MobileCardProps> = ({
  children,
  className = '',
  padding = 'md',
  onClick,
}) => {
  const paddingClass = {
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  }[padding];

  return (
    <div 
      className={`bg-white rounded-lg shadow-sm border border-gray-200 touch-friendly ${paddingClass} ${className} ${
        onClick ? 'cursor-pointer hover:shadow-md transition-shadow active:scale-[0.98]' : ''
      }`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};