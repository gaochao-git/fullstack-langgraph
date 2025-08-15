import React, { Component, ReactNode } from 'react';
import { Result, Button } from 'antd';
import { useAuth } from '@/hooks/useAuth';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: React.ErrorInfo | null;
}

// 错误边界类组件（因为函数组件不支持错误边界）
class AuthErrorBoundaryClass extends Component<Props & { logout: () => void }, State> {
  constructor(props: Props & { logout: () => void }) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Auth Error Boundary caught an error:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
    
    // 如果是认证相关错误，可以在这里处理
    if (error.message.includes('401') || error.message.includes('Unauthorized')) {
      // 可以触发重新登录流程
      console.log('Authentication error detected');
    }
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      const isAuthError = this.state.error?.message.includes('401') || 
                         this.state.error?.message.includes('Unauthorized') ||
                         this.state.error?.message.includes('认证') ||
                         this.state.error?.message.includes('登录');

      if (isAuthError) {
        return (
          <Result
            status="403"
            title="认证错误"
            subTitle="您的登录状态已失效，请重新登录。"
            extra={[
              <Button key="retry" onClick={this.handleReset}>
                重试
              </Button>,
              <Button key="login" type="primary" onClick={this.props.logout}>
                重新登录
              </Button>,
            ]}
          />
        );
      }

      return (
        <Result
          status="error"
          title="出错了"
          subTitle="页面遇到了一些问题，请尝试刷新页面。"
          extra={[
            <Button key="retry" onClick={this.handleReset}>
              重试
            </Button>,
            <Button key="reload" type="primary" onClick={this.handleReload}>
              刷新页面
            </Button>,
          ]}
        >
          {process.env.NODE_ENV === 'development' && (
            <details style={{ whiteSpace: 'pre-wrap', textAlign: 'left', marginTop: 20 }}>
              <summary>错误详情（仅开发环境显示）</summary>
              <p>{this.state.error && this.state.error.toString()}</p>
              <p>{this.state.errorInfo && this.state.errorInfo.componentStack}</p>
            </details>
          )}
        </Result>
      );
    }

    return this.props.children;
  }
}

// 函数组件包装器，用于注入 hooks
export const AuthErrorBoundary: React.FC<Props> = ({ children }) => {
  const { logout } = useAuth();
  
  return (
    <AuthErrorBoundaryClass logout={logout}>
      {children}
    </AuthErrorBoundaryClass>
  );
};