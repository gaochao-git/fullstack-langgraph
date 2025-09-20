import { Typography, theme } from 'antd';
import React, { useMemo, useState } from 'react';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';
import { MermaidDiagram } from './MermaidDiagram';
import { ExtractModal } from './ExtractModal';

const md: MarkdownIt = new MarkdownIt({ 
  html: true, 
  breaks: true,
  linkify: true,
  typographer: true,
  // 配置代码高亮
  highlight: function (str: string, lang: string): string {
    // 如果是 mermaid 代码块，返回特殊标记
    if (lang === 'mermaid') {
      return `<div class="mermaid-placeholder" data-mermaid="${encodeURIComponent(str)}"></div>`;
    }
    
    if (lang && hljs.getLanguage(lang)) {
      try {
        const highlighted = hljs.highlight(str, { language: lang }).value;
        return `<pre class="markdown-code-block"><code class="hljs language-${lang}">${highlighted}</code></pre>`;
      } catch (__) {}
    }
    // 自动检测语言
    try {
      const highlighted = hljs.highlightAuto(str).value;
      return `<pre class="markdown-code-block"><code class="hljs">${highlighted}</code></pre>`;
    } catch (__) {
      // 如果高亮失败，返回原始代码
      return `<pre class="markdown-code-block"><code>${md.utils.escapeHtml(str)}</code></pre>`;
    }
  }
});

// 注意：这些规则会在组件内部根据主题动态更新


interface MarkdownRendererProps {
  content: string;
}

// 判断内容是否为工具输出
const isToolOutput = (content: string): boolean => {
  // 检查是否为 JSON 格式的工具输出
  try {
    const parsed = JSON.parse(content.trim());
    // 检查是否包含工具输出的典型字段
    return parsed && (
      parsed.success !== undefined || 
      parsed.sops !== undefined ||
      parsed.sop !== undefined ||
      parsed.error !== undefined ||
      (typeof parsed === 'object' && parsed !== null)
    );
  } catch {
    return false;
  }
};

const MarkdownRenderer: React.FC<MarkdownRendererProps> = React.memo(({ content }) => {
  const { token } = theme.useToken();
  const [reportVisible, setReportVisible] = useState(false);
  const [reportType, setReportType] = useState<string>('');
  const [reportPath, setReportPath] = useState<string>('');
  const [reportTitle, setReportTitle] = useState<string>('查看报告');
  
  // 使用 useMemo 缓存表格渲染规则设置
  useMemo(() => {
    md.renderer.rules.table_open = () => '<div class="my-4 overflow-x-auto"><table class="markdown-table">';
    md.renderer.rules.table_close = () => '</table></div>';
    md.renderer.rules.th_open = () => '<th class="markdown-th">';
    md.renderer.rules.td_open = () => '<td class="markdown-td">';
  }, []);
  
  // 使用 useMemo 缓存样式，只有主题改变时才重新计算
  const markdownStyles = useMemo(() => `
    .markdown-body {
      color: ${token.colorText};
      line-height: 1.5;
      white-space: normal;
      word-break: normal;
      overflow-wrap: break-word;
      max-width: 100%;
      word-wrap: break-word;
    }
    .markdown-body h1 { 
      font-weight: bold;
      margin-top: 0.75rem;
      margin-bottom: 0.5rem;
      color: ${token.colorTextHeading};
      border-bottom: 2px solid ${token.colorPrimary};
      padding-bottom: 4px;
    }
    .markdown-body h2 { 
      font-weight: bold;
      margin-top: 0.75rem;
      margin-bottom: 0.5rem;
      color: ${token.colorTextHeading};
      border-bottom: 1px solid ${token.colorBorder};
      padding-bottom: 2px;
    }
    .markdown-body h3 { 
      font-weight: bold;
      margin-top: 0.5rem;
      margin-bottom: 0.25rem;
      color: ${token.colorTextHeading};
    }
    .markdown-body h4 { 
      font-weight: bold;
      margin-top: 0.5rem;
      margin-bottom: 0.25rem;
      color: ${token.colorTextHeading};
    }
    .markdown-body p { 
      margin-bottom: 0.5rem;
      line-height: 1.75;
      color: ${token.colorText};
      white-space: normal;
      word-break: normal;
      overflow-wrap: break-word;
      hyphens: auto;
    }
    .markdown-body a {
      color: ${token.colorPrimary};
      text-decoration: underline;
    }
    .markdown-body a:hover {
      color: ${token.colorPrimaryHover};
    }
    .markdown-body code:not(pre code) { 
      background-color: ${token.colorFillTertiary};
      color: ${token.colorText};
      padding: 0.125rem 0.25rem;
      border-radius: 4px;
      font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
      border: none;
      white-space: nowrap;
      overflow-wrap: break-word;
    }
    .markdown-body pre { 
      background-color: ${token.colorBgContainer};
      border: 1px solid ${token.colorBorder};
      border-radius: 6px;
      padding: 0;
      overflow-x: auto;
      margin: 8px 0;
      white-space: pre;
      word-break: normal;
    }
    .markdown-body pre code {
      font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
      background: transparent;
      padding: 0;
      border: none;
      white-space: pre;
      word-break: normal;
    }
    .markdown-body .hljs {
      background: transparent !important;
      padding: 8px !important;
    }
    .markdown-body .markdown-code-block {
      background-color: ${token.colorFillTertiary};
      border: 1px solid ${token.colorBorder};
      border-radius: 6px;
      padding: 12px;
      overflow-x: auto;
      margin: 8px 0;
    }
    .markdown-body .markdown-code-block code {
      color: ${token.colorText};
      background: transparent;
      padding: 0;
    }
    .markdown-body ul {
      list-style: disc;
      list-style-position: inside;
      margin-bottom: 0.5rem;
      color: ${token.colorText};
      padding-left: 12px;
    }
    .markdown-body ol {
      list-style: decimal;
      list-style-position: inside;
      margin-bottom: 0.5rem;
      color: ${token.colorText};
      padding-left: 12px;
    }
    .markdown-body li {
      margin-bottom: 0.25rem;
      color: ${token.colorText};
    }
    .markdown-body blockquote {
      border-left: 4px solid ${token.colorPrimary};
      padding-left: 12px;
      margin: 8px 0;
      color: ${token.colorTextSecondary};
      font-style: italic;
      background-color: ${token.colorFillQuaternary};
      padding: 8px 12px;
      border-radius: 4px;
    }
    .markdown-body hr {
      border: none;
      height: 1px;
      background-color: ${token.colorBorder};
      margin: 12px 0;
    }
    .markdown-body .markdown-table { 
      border-collapse: collapse;
      width: 100%;
      margin: 0.5rem 0;
      border: 1px solid ${token.colorBorder};
      border-radius: 6px;
      overflow: hidden;
    }
    .markdown-body .markdown-th { 
      background-color: ${token.colorFillAlter};
      color: ${token.colorText};
      padding: 8px 12px;
      text-align: left;
      font-weight: 600;
      border: 1px solid ${token.colorBorder};
    }
    .markdown-body .markdown-td { 
      color: ${token.colorText};
      padding: 8px 12px;
      border: 1px solid ${token.colorBorderSecondary};
    }
    .markdown-body tr:last-child td {
      border-bottom: none;
    }
    .markdown-body tr:nth-child(even) {
      background-color: ${token.colorFillQuaternary};
    }
    .markdown-body tr:nth-child(odd) {
      background-color: ${token.colorBgContainer};
    }
    .markdown-body strong {
      color: ${token.colorTextHeading};
      font-weight: 600;
    }
    .markdown-body em {
      color: ${token.colorTextSecondary};
      font-style: italic;
    }
    .markdown-body img {
      max-width: 100%;
      height: auto;
      border-radius: 6px;
      margin: 8px 0;
      display: block;
      box-shadow: 0 2px 8px ${token.colorShadow};
    }
    .markdown-body iframe {
      max-width: 100%;
      border: 1px solid ${token.colorBorder};
      border-radius: 6px;
      margin: 8px 0;
      display: block;
      box-shadow: 0 2px 8px ${token.colorShadow};
    }
  `, [token]);
  
  // 使用 useMemo 处理内容，避免重复计算
  const processedContent = useMemo(() => {
    let processed = content;
    
    // 如果内容包含工具调用标签，移除它们
    if (content.includes('<function_calls>')) {
      processed = content.split('<function_calls>')[0].trim();
    }
    if (processed.includes('<function_results>')) {
      processed = processed.split('<function_results>')[0].trim();
    }
    
    // 如果内容看起来像工具输出的 JSON，返回空
    if (isToolOutput(processed)) {
      return '';
    }
    
    // 如果处理后的内容为空，返回空
    if (!processed.trim()) {
      return '';
    }
    
    return processed;
  }, [content]);
  
  // 提前返回，避免渲染空内容
  if (!processedContent) {
    return null;
  }

  // 分割内容为 Markdown、Mermaid 和报告链接部分
  const parts = useMemo(() => {
    const result: Array<{ type: 'markdown' | 'mermaid' | 'report'; content: string; id?: string; reportData?: { type: string; path: string; title: string } }> = [];
    let currentContent = processedContent;
    let mermaidIndex = 0;
    
    // 合并的正则表达式，同时匹配 mermaid 代码块和报告标识符
    // 报告标识符格式：[REPORT:type:path:title] 或 REPORT:type:path:title
    const combinedRegex = /```mermaid\n([\s\S]*?)```|\[REPORT:([^:]+):([^:]+):([^\]]+)\]|(?<!\[)REPORT:([^:]+):([^:\s]+)(?::([^\s\]]+))?/g;
    let lastIndex = 0;
    let match;
    
    while ((match = combinedRegex.exec(processedContent)) !== null) {
      // 添加之前的 Markdown 内容
      if (match.index > lastIndex) {
        const mdContent = processedContent.slice(lastIndex, match.index);
        if (mdContent.trim()) {
          result.push({ type: 'markdown', content: mdContent });
        }
      }
      
      if (match[0].startsWith('```mermaid')) {
        // 添加 Mermaid 图表
        result.push({
          type: 'mermaid',
          content: match[1].trim(),
          id: `mermaid-${mermaidIndex++}`
        });
      } else if (match[0].startsWith('[REPORT:')) {
        // 添加带方括号的报告链接
        result.push({
          type: 'report',
          content: match[0],
          reportData: {
            type: match[2],
            path: match[3],
            title: match[4]
          }
        });
      } else if (match[0].startsWith('REPORT:')) {
        // 添加不带方括号的报告链接
        result.push({
          type: 'report',
          content: match[0],
          reportData: {
            type: match[5],
            path: match[6],
            title: match[7] || '查看完整可视化报告'  // 如果没有标题，使用默认值
          }
        });
      }
      
      lastIndex = match.index + match[0].length;
    }
    
    // 添加剩余的 Markdown 内容
    if (lastIndex < processedContent.length) {
      const mdContent = processedContent.slice(lastIndex);
      if (mdContent.trim()) {
        result.push({ type: 'markdown', content: mdContent });
      }
    }
    
    return result;
  }, [processedContent]);

  return (
    <Typography>
      <style>{markdownStyles}</style>
      {parts.map((part, index) => {
        if (part.type === 'markdown') {
          return (
            <div 
              key={`md-${index}`}
              className="markdown-body"
              dangerouslySetInnerHTML={{ __html: md.render(part.content) }} 
            />
          );
        } else if (part.type === 'mermaid') {
          return (
            <div key={part.id} className="my-4">
              <MermaidDiagram id={part.id!} chart={part.content} />
            </div>
          );
        } else if (part.type === 'report' && part.reportData) {
          // 渲染报告链接按钮
          return (
            <div key={`report-${index}`} className="my-2">
              <button
                onClick={(e) => {
                  e.preventDefault();
                  // 设置报告信息
                  setReportType(part.reportData.type);
                  setReportPath(part.reportData.path);
                  setReportTitle(part.reportData.title);
                  setReportVisible(true);
                }}
                className="inline-flex items-center gap-2 px-3 py-2 rounded-lg transition-colors cursor-pointer"
                style={{
                  backgroundColor: token.colorPrimaryBg,
                  border: `1px solid ${token.colorPrimaryBorder}`,
                  color: token.colorPrimary,
                  outline: 'none'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = token.colorPrimaryBgHover;
                  e.currentTarget.style.borderColor = token.colorPrimaryBorderHover;
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = token.colorPrimaryBg;
                  e.currentTarget.style.borderColor = token.colorPrimaryBorder;
                }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <span>{part.reportData.title}</span>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                </svg>
              </button>
            </div>
          );
        }
        return null;
      })}
      
      {/* 通用报告查看Modal */}
      <ExtractModal
        visible={reportVisible}
        onClose={() => setReportVisible(false)}
        reportType={reportType}
        reportPath={reportPath}
        title={reportTitle}
      />
    </Typography>
  );
}, (prevProps, nextProps) => {
  // 只有当 content 真正改变时才重新渲染
  return prevProps.content === nextProps.content;
});

export default MarkdownRenderer; 