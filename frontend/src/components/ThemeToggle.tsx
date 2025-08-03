import React from 'react';
import { Button, Dropdown, Space } from 'antd';
import { SunOutlined, MoonOutlined, DesktopOutlined, DownOutlined } from '@ant-design/icons';
import { useTheme, ThemeMode } from '../hooks/ThemeContext';

export const ThemeToggle: React.FC = () => {
  const { mode, setMode, isDark } = useTheme();

  const items = [
    {
      key: 'light',
      label: (
        <Space>
          <SunOutlined />
          浅色主题
        </Space>
      ),
      onClick: () => setMode('light'),
    },
    {
      key: 'dark',
      label: (
        <Space>
          <MoonOutlined />
          暗黑主题
        </Space>
      ),
      onClick: () => setMode('dark'),
    },
    {
      key: 'auto',
      label: (
        <Space>
          <DesktopOutlined />
          跟随系统
        </Space>
      ),
      onClick: () => setMode('auto'),
    },
  ];

  const getCurrentIcon = () => {
    switch (mode) {
      case 'light':
        return <SunOutlined />;
      case 'dark':
        return <MoonOutlined />;
      case 'auto':
        return <DesktopOutlined />;
      default:
        return <SunOutlined />;
    }
  };

  const getCurrentLabel = () => {
    switch (mode) {
      case 'light':
        return '浅色';
      case 'dark':
        return '暗黑';
      case 'auto':
        return '自动';
      default:
        return '主题';
    }
  };

  return (
    <Dropdown
      menu={{ items }}
      placement="bottomRight"
      arrow
      trigger={['click']}
    >
      <Button
        type="text"
        size="small"
        className="flex items-center gap-1"
        style={{
          color: isDark ? '#fff' : '#666',
          border: 'none',
          boxShadow: 'none',
        }}
      >
        <Space size={4}>
          {getCurrentIcon()}
          <span className="text-xs md:text-sm">{getCurrentLabel()}</span>
          <DownOutlined style={{ fontSize: '10px' }} />
        </Space>
      </Button>
    </Dropdown>
  );
};

// 简化版主题切换按钮（只有图标）
export const ThemeToggleSimple: React.FC = () => {
  const { mode, setMode, isDark } = useTheme();

  const handleToggle = () => {
    // 简单的三态切换：light → dark → auto → light
    switch (mode) {
      case 'light':
        setMode('dark');
        break;
      case 'dark':
        setMode('auto');
        break;
      case 'auto':
        setMode('light');
        break;
      default:
        setMode('light');
    }
  };

  const getCurrentIcon = () => {
    switch (mode) {
      case 'light':
        return <SunOutlined style={{ color: '#fbbf24' }} />;
      case 'dark':
        return <MoonOutlined style={{ color: '#6366f1' }} />;
      case 'auto':
        return <DesktopOutlined style={{ color: '#10b981' }} />;
      default:
        return <SunOutlined style={{ color: '#fbbf24' }} />;
    }
  };

  return (
    <Button
      type="text"
      size="small"
      icon={getCurrentIcon()}
      onClick={handleToggle}
      className="flex items-center justify-center"
      style={{
        backgroundColor: isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)',
        border: `1px solid ${isDark ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.1)'}`,
        borderRadius: '6px',
        width: '32px',
        height: '32px',
        transition: 'all 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = isDark ? 'rgba(255,255,255,0.15)' : 'rgba(0,0,0,0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.05)';
      }}
      title={`当前主题: ${mode === 'light' ? '浅色' : mode === 'dark' ? '暗黑' : '跟随系统'} (点击切换)`}
    />
  );
};