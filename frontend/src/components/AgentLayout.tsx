import React from 'react';
import { Outlet } from 'react-router-dom';

const AgentLayout: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  return (
    <div style={{ 
      width: '100vw', 
      height: '100vh',
      padding: '5px',
      boxSizing: 'border-box',
      overflow: 'hidden'
    }}>
      {children || <Outlet />}
    </div>
  );
};

export default AgentLayout;