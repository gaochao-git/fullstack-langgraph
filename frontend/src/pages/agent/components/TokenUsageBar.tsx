import { Progress, Tooltip } from "antd";
import { useMemo } from "react";

interface TokenUsageInfo {
  used: number;
  total: number;
  percentage: number;
  remaining: number;
}

interface TokenUsageBarProps {
  tokenUsage: TokenUsageInfo | null;
  className?: string;
  onClick?: () => void;
}

export default function TokenUsageBar({ tokenUsage, className, onClick }: TokenUsageBarProps) {
  if (!tokenUsage) {
    return null;
  }

  const { used, total, percentage, remaining } = tokenUsage;

  // 计算进度条颜色
  const strokeColor = useMemo(() => {
    if (percentage < 60) {
      return "#52c41a"; // 绿色
    } else if (percentage < 80) {
      return "#faad14"; // 橙色
    } else if (percentage < 95) {
      return "#ff7a45"; // 深橙色
    } else {
      return "#f5222d"; // 红色
    }
  }, [percentage]);

  // 格式化数字显示
  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + "M";
    } else if (num >= 1000) {
      return (num / 1000).toFixed(1) + "K";
    }
    return num.toString();
  };

  return (
    <div 
      className={`token-usage-bar ${className || ""} ${onClick ? 'cursor-pointer' : ''}`}
      onClick={onClick}
    >
      <Tooltip 
        title={
          <div>
            <div className="font-semibold mb-1">上下文长度</div>
            <div>当前: {formatNumber(used)} / {formatNumber(total)}</div>
            <div>使用率: {percentage.toFixed(1)}%</div>
            <div className="mt-1 pt-1 border-t border-gray-600">
              <div>当前长度: {used.toLocaleString()} tokens</div>
              <div>最大长度: {total.toLocaleString()} tokens</div>
              <div>剩余空间: {remaining.toLocaleString()} tokens</div>
            </div>
          </div>
        }
        placement="bottom"
      >
        <div className="flex items-center gap-2 h-full">
          <div className="flex-1 min-w-[200px] flex items-center">
            <Progress
              percent={percentage}
              size="small"
              strokeColor={strokeColor}
              format={(percent) => `${percent}%`}
              status={percentage >= 95 ? "exception" : "active"}
              style={{ marginBottom: 0 }}
              showInfo={true}
              trailColor="rgba(82, 196, 26, 0.2)"
            />
          </div>
        </div>
      </Tooltip>
    </div>
  );
}