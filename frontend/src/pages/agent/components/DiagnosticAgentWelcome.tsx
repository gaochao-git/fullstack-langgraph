import { 
  MessageCircle,
  Activity,
  Stethoscope,
  Zap,
  Shield,
  Brain
} from "lucide-react";
import { useTheme } from '@/hooks/ThemeContext';
import { cn } from '@/utils/lib-utils';

interface DiagnosticAgentWelcomeProps {
  onSwitchToChat: () => void;
}

export default function DiagnosticAgentWelcome({ onSwitchToChat }: DiagnosticAgentWelcomeProps) {
  const { isDark } = useTheme();

  const features = [
    {
      icon: <Stethoscope className="w-6 h-6" />,
      title: "故障诊断",
      description: "深度分析系统问题，快速定位故障根源",
      color: "text-blue-500"
    },
    {
      icon: <Brain className="w-6 h-6" />,
      title: "智能分析",
      description: "基于AI的智能诊断，提供专业解决方案",
      color: "text-purple-500"
    },
    {
      icon: <Activity className="w-6 h-6" />,
      title: "实时监控",
      description: "全方位监控系统状态，及时发现异常",
      color: "text-green-500"
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "快速响应",
      description: "毫秒级响应时间，即时诊断分析",
      color: "text-yellow-500"
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: "安全可靠",
      description: "企业级安全保障，数据隐私保护",
      color: "text-red-500"
    },
    {
      icon: <MessageCircle className="w-6 h-6" />,
      title: "交互式对话",
      description: "自然语言交互，简单易用的诊断体验",
      color: "text-indigo-500"
    }
  ];

  return (
    <div className="min-h-[600px] flex flex-col items-center justify-center p-8">
      <div className="max-w-4xl w-full space-y-8">
        {/* 标题区域 */}
        <div className="text-center space-y-4">
          <div className="flex justify-center">
            <div className={cn(
              "w-20 h-20 rounded-full flex items-center justify-center",
              isDark 
                ? "bg-gradient-to-br from-blue-600 to-purple-600" 
                : "bg-gradient-to-br from-blue-500 to-purple-500"
            )}>
              <Stethoscope className="w-10 h-10 text-white" />
            </div>
          </div>
          <h1 className={cn(
            "text-4xl font-bold",
            isDark ? "text-white" : "text-gray-900"
          )}>
            智能运维诊断助手
          </h1>
          <p className={cn(
            "text-xl max-w-2xl mx-auto",
            isDark ? "text-slate-400" : "text-gray-600"
          )}>
            基于人工智能的智能运维诊断平台，帮助您快速定位和解决系统问题
          </p>
        </div>

        {/* 功能特性网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((feature, index) => (
            <div
              key={index}
              className={cn(
                "p-6 rounded-2xl border transition-all duration-300 hover:scale-105",
                isDark 
                  ? "bg-slate-800/50 border-slate-700 hover:border-slate-600" 
                  : "bg-white/50 border-gray-200 hover:border-gray-300"
              )}
            >
              <div className={cn("mb-4", feature.color)}>
                {feature.icon}
              </div>
              <h3 className={cn(
                "text-lg font-semibold mb-2",
                isDark ? "text-white" : "text-gray-900"
              )}>
                {feature.title}
              </h3>
              <p className={cn(
                "text-sm",
                isDark ? "text-slate-400" : "text-gray-600"
              )}>
                {feature.description}
              </p>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}