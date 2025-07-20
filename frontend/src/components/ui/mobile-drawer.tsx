import React from 'react';
import { Drawer } from 'antd';

interface MobileDrawerProps {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  placement?: 'top' | 'right' | 'bottom' | 'left';
  height?: number | string;
  width?: number | string;
}

export const MobileDrawer: React.FC<MobileDrawerProps> = ({
  open,
  onClose,
  title,
  children,
  placement = 'bottom',
  height = '70vh',
  width = '100vw',
}) => {
  return (
    <Drawer
      title={title}
      placement={placement}
      closable={true}
      onClose={onClose}
      open={open}
      height={placement === 'top' || placement === 'bottom' ? height : undefined}
      width={placement === 'left' || placement === 'right' ? width : undefined}
      styles={{
        body: { 
          padding: '12px',
          height: '100%',
          overflow: 'auto',
        },
        header: {
          padding: '12px 16px',
          borderBottom: '1px solid #f0f0f0',
        }
      }}
      // 移动端优化
      destroyOnClose={false}
      maskClosable={true}
      keyboard={true}
    >
      {children}
    </Drawer>
  );
};