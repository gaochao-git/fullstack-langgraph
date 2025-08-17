import React, { useEffect, useRef, useState, useCallback } from 'react';
import mermaid from 'mermaid';
import { useTheme } from '@/hooks/ThemeContext';
import { Button, message, Slider, Dropdown } from 'antd';
import { Code2, ChartLine, Copy, Check, ZoomIn, ZoomOut, Maximize2, Download, MoreVertical } from 'lucide-react';

interface MermaidDiagramProps {
  chart: string;
  id: string;
}

export const MermaidDiagram: React.FC<MermaidDiagramProps> = ({ chart, id }) => {
  const { isDark } = useTheme();
  const containerRef = useRef<HTMLDivElement>(null);
  const diagramRef = useRef<HTMLDivElement>(null);
  const [svg, setSvg] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [showCode, setShowCode] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);
  
  // 缩放和拖动状态
  const [scale, setScale] = useState<number>(0.6);
  const [position, setPosition] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    // 配置 mermaid
    mermaid.initialize({
      startOnLoad: false,
      theme: isDark ? 'dark' : 'default',
      themeVariables: {
        primaryColor: isDark ? '#6366f1' : '#818cf8',
        primaryTextColor: isDark ? '#fff' : '#000',
        primaryBorderColor: isDark ? '#4f46e5' : '#6366f1',
        lineColor: isDark ? '#6b7280' : '#9ca3af',
        secondaryColor: isDark ? '#374151' : '#e5e7eb',
        tertiaryColor: isDark ? '#1f2937' : '#f3f4f6',
        background: isDark ? '#111827' : '#ffffff',
        mainBkg: isDark ? '#1f2937' : '#f5f3ff',
        secondBkg: isDark ? '#374151' : '#e9d5ff',
        tertiaryBkg: isDark ? '#4b5563' : '#f3f4f6',
        textColor: isDark ? '#e5e7eb' : '#111827',
        taskBorderColor: isDark ? '#4b5563' : '#d1d5db',
        taskBkgColor: isDark ? '#374151' : '#f3f4f6',
        activeTaskBorderColor: isDark ? '#3b82f6' : '#2563eb',
        activeTaskBkgColor: isDark ? '#1e40af' : '#dbeafe',
        fontSize: '12px'
      },
      flowchart: {
        htmlLabels: true,
        curve: 'basis',
        padding: 8,
        nodeSpacing: 20,
        rankSpacing: 30,
        diagramPadding: 8
      },
      securityLevel: 'loose'
    });

    renderDiagram();
  }, [chart, isDark]);

  // 处理鼠标按下事件
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({
      x: e.clientX - position.x,
      y: e.clientY - position.y
    });
    e.preventDefault();
  }, [position]);

  // 处理鼠标移动事件
  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y
    });
  }, [isDragging, dragStart]);

  // 处理鼠标松开事件
  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  // 处理滚轮缩放
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.05 : 0.05;
    setScale(prev => Math.min(Math.max(0.1, prev + delta), 2));
  }, []);

  // 重置视图
  const resetView = useCallback(() => {
    setScale(0.6);
    setPosition({ x: 0, y: 0 });
  }, []);

  // 导出为SVG
  const exportSVG = useCallback(() => {
    if (!svg) return;
    
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mermaid-diagram-${Date.now()}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    message.success('SVG 导出成功');
  }, [svg]);

  // 导出为PNG
  const exportPNG = useCallback(async () => {
    if (!diagramRef.current) return;
    
    try {
      // 获取SVG元素
      const svgElement = diagramRef.current.querySelector('svg');
      if (!svgElement) return;

      // 克隆SVG元素以避免修改原始元素
      const clonedSvg = svgElement.cloneNode(true) as SVGElement;
      
      // 获取SVG的尺寸
      const bbox = svgElement.getBoundingClientRect();
      const width = bbox.width;
      const height = bbox.height;
      
      // 设置viewBox确保正确渲染
      if (!clonedSvg.getAttribute('viewBox')) {
        clonedSvg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      }
      clonedSvg.setAttribute('width', String(width));
      clonedSvg.setAttribute('height', String(height));
      
      // 内联所有样式以避免跨域问题
      const styleElement = document.createElement('style');
      styleElement.textContent = `
        text { font-family: Arial, sans-serif; }
        .node rect { fill: #f9f9f9; stroke: #333; stroke-width: 1.5px; }
        .node polygon { fill: #f9f9f9; stroke: #333; stroke-width: 1.5px; }
        .node circle { fill: #f9f9f9; stroke: #333; stroke-width: 1.5px; }
        .edgePath path { stroke: #333; stroke-width: 1.5px; fill: none; }
        .label { color: #333; }
        ${isDark ? `
          .node rect { fill: #374151; stroke: #6b7280; }
          .node polygon { fill: #374151; stroke: #6b7280; }
          .node circle { fill: #374151; stroke: #6b7280; }
          .edgePath path { stroke: #6b7280; }
          .label { color: #e5e7eb; }
          text { fill: #e5e7eb; }
        ` : ''}
      `;
      clonedSvg.insertBefore(styleElement, clonedSvg.firstChild);
      
      // 创建canvas
      const canvas = document.createElement('canvas');
      const scale = 2; // 提高分辨率
      canvas.width = width * scale;
      canvas.height = height * scale;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      // 设置背景色
      ctx.fillStyle = isDark ? '#111827' : 'white';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      
      // 将SVG转换为data URL（避免跨域问题）
      const svgData = new XMLSerializer().serializeToString(clonedSvg);
      const svgBase64 = btoa(unescape(encodeURIComponent(svgData)));
      const dataUrl = `data:image/svg+xml;base64,${svgBase64}`;
      
      const img = new Image();
      
      img.onload = () => {
        try {
          ctx.scale(scale, scale);
          ctx.drawImage(img, 0, 0, width, height);
          
          // 导出PNG
          canvas.toBlob((blob) => {
            if (!blob) {
              message.error('无法生成PNG文件');
              return;
            }
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `mermaid-diagram-${Date.now()}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            message.success('PNG 导出成功');
          }, 'image/png');
        } catch (err) {
          console.error('Canvas操作失败:', err);
          message.error('PNG 导出失败');
        }
      };
      
      img.onerror = () => {
        console.error('图片加载失败');
        message.error('PNG 导出失败：无法加载图片');
      };
      
      img.src = dataUrl;
    } catch (error) {
      console.error('导出PNG失败:', error);
      message.error('PNG 导出失败');
    }
  }, [isDark]);

  // 导出代码
  const exportCode = useCallback(() => {
    const blob = new Blob([chart], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `mermaid-diagram-${Date.now()}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    message.success('代码导出成功');
  }, [chart]);

  const renderDiagram = async () => {
    if (!chart) return;

    try {
      setError('');
      
      // 生成唯一ID
      const graphId = `mermaid-${id}-${Date.now()}`;
      
      // 渲染图表
      const { svg } = await mermaid.render(graphId, chart);
      setSvg(svg);
      
      // 重置位置到中心
      setPosition({ x: 0, y: 0 });
    } catch (err) {
      console.error('Mermaid 渲染错误:', err);
      setError(err instanceof Error ? err.message : '图表渲染失败');
    }
  };

  if (error) {
    return (
      <div className="relative">
        <div className="absolute top-2 right-2 z-10">
          <Button
            size="small"
            icon={showCode ? <ChartLine className="h-4 w-4" /> : <Code2 className="h-4 w-4" />}
            onClick={() => setShowCode(!showCode)}
            className="flex items-center gap-1"
          >
            {showCode ? '显示图表' : '查看代码'}
          </Button>
        </div>
        <div className="p-4 border border-red-300 rounded-md bg-red-50 dark:bg-red-900/20 dark:border-red-800">
          <p className="text-red-600 dark:text-red-400 text-sm mb-2">
            Mermaid 图表渲染错误: {error}
          </p>
          <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-auto p-3 bg-gray-100 dark:bg-gray-800 rounded">
            {chart}
          </pre>
        </div>
      </div>
    );
  }

  // 下载菜单项
  const downloadMenuItems = [
    {
      key: 'svg',
      label: '下载 SVG',
      icon: <Download className="h-4 w-4" />,
      onClick: exportSVG
    },
    {
      key: 'png',
      label: '下载 PNG',
      icon: <Download className="h-4 w-4" />,
      onClick: exportPNG
    },
    {
      key: 'code',
      label: '下载代码',
      icon: <Code2 className="h-4 w-4" />,
      onClick: exportCode
    }
  ];

  return (
    <div className="mermaid-container my-4">
      <div className={`border rounded-lg ${
        isDark 
          ? 'bg-gray-900 border-gray-700' 
          : 'bg-white border-gray-200'
      }`}>
        {/* 统一的工具栏 - 始终显示 */}
        <div className="flex items-center justify-between p-3 border-b border-gray-200 dark:border-gray-700">
          {/* 左侧：视图切换按钮 */}
          <div className="flex items-center gap-2">
            <Button
              size="small"
              type={showCode ? 'default' : 'primary'}
              icon={<ChartLine className="h-4 w-4" />}
              onClick={() => setShowCode(false)}
              className="flex items-center gap-1"
            >
              图表
            </Button>
            <Button
              size="small"
              type={showCode ? 'primary' : 'default'}
              icon={<Code2 className="h-4 w-4" />}
              onClick={() => setShowCode(true)}
              className="flex items-center gap-1"
            >
              代码
            </Button>
          </div>
          
          {/* 右侧：根据视图显示不同的操作按钮 */}
          <div className="flex items-center gap-2">
            {showCode ? (
              // 代码视图的操作按钮
              <>
                <Button
                  size="small"
                  type="text"
                  icon={copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                  onClick={() => {
                    navigator.clipboard.writeText(chart);
                    setCopied(true);
                    message.success('代码已复制到剪贴板');
                    setTimeout(() => setCopied(false), 2000);
                  }}
                >
                  {copied ? '已复制' : '复制'}
                </Button>
                <Button
                  size="small"
                  type="text"
                  icon={<Download className="h-4 w-4" />}
                  onClick={exportCode}
                >
                  下载代码
                </Button>
              </>
            ) : (
              // 图表视图的操作按钮
              <>
                {/* 缩放控制 */}
                <div className="flex items-center gap-2">
                  <Button
                    size="small"
                    type="text"
                    icon={<ZoomOut className="h-4 w-4" />}
                    onClick={() => setScale(prev => Math.max(0.1, prev - 0.1))}
                  />
                  <Slider
                    min={10}
                    max={200}
                    value={scale * 100}
                    onChange={(value) => setScale(value / 100)}
                    style={{ width: 100 }}
                  />
                  <Button
                    size="small"
                    type="text"
                    icon={<ZoomIn className="h-4 w-4" />}
                    onClick={() => setScale(prev => Math.min(2, prev + 0.1))}
                  />
                  <span className="text-xs text-gray-500">{Math.round(scale * 100)}%</span>
                </div>
                <Button
                  size="small"
                  type="text"
                  icon={<Maximize2 className="h-4 w-4" />}
                  onClick={resetView}
                  title="重置视图"
                />
              </>
            )}
            {/* 下载菜单 - 始终显示 */}
            <Dropdown
              menu={{ items: downloadMenuItems }}
              placement="bottomRight"
            >
              <Button
                size="small"
                type="text"
                icon={<MoreVertical className="h-4 w-4" />}
              />
            </Dropdown>
          </div>
        </div>
        
        {/* 内容区域 */}
        {showCode ? (
          // 代码视图内容
          <div className="p-4">
            <pre className={`text-sm font-mono overflow-auto ${
              isDark 
                ? 'text-gray-300' 
                : 'text-gray-700'
            }`}>
              <code>{chart}</code>
            </pre>
          </div>
        ) : (
          // 图表视图内容
          <div 
            className="overflow-hidden p-2"
            style={{ 
              height: '450px', 
              position: 'relative',
              cursor: isDragging ? 'grabbing' : 'grab',
              overflow: 'hidden'
            }}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onWheel={handleWheel}
          >
          <style>{`
            .mermaid-diagram-${id} svg {
              max-width: none !important;
              height: auto !important;
            }
            .mermaid-diagram-${id} .node rect,
            .mermaid-diagram-${id} .node polygon,
            .mermaid-diagram-${id} .node circle,
            .mermaid-diagram-${id} .node ellipse {
              rx: 4 !important;
              ry: 4 !important;
            }
            .mermaid-diagram-${id} .edgePath path {
              stroke-width: 1px !important;
            }
            .mermaid-diagram-${id} text {
              font-size: 12px !important;
              font-weight: 500 !important;
            }
            .mermaid-diagram-${id} .label {
              font-size: 11px !important;
            }
            .mermaid-diagram-${id} .nodeLabel {
              padding: 2px 4px !important;
            }
          `}</style>
            <div 
              ref={diagramRef}
              className={`mermaid-content mermaid-diagram-${id}`}
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: `translate(calc(-50% + ${position.x}px), calc(-50% + ${position.y}px)) scale(${scale})`,
                transformOrigin: 'center center',
                transition: isDragging ? 'none' : 'transform 0.2s ease',
                userSelect: 'none'
              }}
              dangerouslySetInnerHTML={{ __html: svg }}
            />
          </div>
        )}
      </div>
    </div>
  );
};