import React from 'react';
import { Tag } from 'antd';
import { RobotOutlined } from '@ant-design/icons';
import { useTheme } from '@/hooks/ThemeContext';
import { cn } from '@/utils/lib-utils';
import { type Agent } from '../../../services/agentApi';

// 欢迎页面组件属性
interface GenericAgentWelcomeProps {
  agent: Agent | null;
  onSubmit: (message: string) => void;
}

const GenericAgentWelcome: React.FC<GenericAgentWelcomeProps> = ({ agent, onSubmit }) => {
  const { isDark } = useTheme();
  
  return (
    <div className={cn(
      "flex flex-col items-center justify-center h-full p-8 transition-colors duration-200",
      isDark 
        ? "bg-gradient-to-b from-gray-900 to-gray-800" 
        : "bg-gradient-to-b from-gray-50 to-white"
    )}>
      <div className={cn(
        "max-w-4xl w-full rounded-2xl p-8 border transition-all duration-200",
        isDark 
          ? "border-cyan-400/30 bg-gradient-to-br from-blue-900/50 to-purple-900/50" 
          : "border-blue-300/50 bg-gradient-to-br from-blue-50 to-purple-50"
      )}>
        <div className="text-center mb-8">
          <div className={cn(
            "inline-flex items-center justify-center w-16 h-16 rounded-full mb-4",
            isDark 
              ? "bg-cyan-900/50 text-cyan-400" 
              : "bg-blue-100 text-blue-600"
          )}>
            <RobotOutlined className="text-2xl" />
          </div>
          <h2 className={cn(
            "text-2xl font-bold mb-2",
            isDark ? "text-white" : "text-gray-900"
          )}>
            {agent?.agent_name || '智能助手'}
          </h2>
          <p className={cn(
            "text-lg mb-6",
            isDark ? "text-gray-300" : "text-gray-600"
          )}>
            {agent?.agent_description || '欢迎使用智能助手，我可以帮助您完成各种任务。'}
          </p>
        </div>

        {/* 智能体能力展示 */}
        {agent?.agent_capabilities && agent.agent_capabilities.length > 0 && (
          <div className="mb-6">
            <h3 className={cn(
              "text-sm font-medium mb-3",
              isDark ? "text-blue-300" : "text-gray-700"
            )}>
              我的能力
            </h3>
            <div className="flex flex-wrap gap-2">
              {agent.agent_capabilities.map((capability, index) => (
                <Tag 
                  key={index}
                  className={cn(
                    "px-3 py-1 rounded-full text-sm transition-colors duration-200",
                    isDark 
                      ? "bg-cyan-900/30 text-cyan-400 border-cyan-700" 
                      : "bg-blue-100 text-blue-700 border-blue-300"
                  )}
                >
                  {capability}
                </Tag>
              ))}
            </div>
          </div>
        )}

        {/* 快速开始提示 */}
        <div className={cn(
          "text-center text-sm",
          isDark ? "text-blue-300" : "text-gray-600"
        )}>
          请在下方输入框中描述您的问题，我会尽力为您解答
        </div>
      </div>
    </div>
  );
};

export default GenericAgentWelcome;