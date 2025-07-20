import { Typography } from 'antd';
import React from 'react';
import MarkdownIt from 'markdown-it';

const md: MarkdownIt = new MarkdownIt({ 
  html: true, 
  breaks: false,
  // 配置代码高亮
  highlight: function (str: string, lang: string): string {
    return '<pre class="p-3 rounded-md overflow-x-auto font-mono text-xs my-2" style="background-color: #1F2937; border: 1px solid #374151;">' +
           '<code style="color: #D1D5DB;">' +
           md.utils.escapeHtml(str) +
           '</code></pre>';
  }
});

// 自定义渲染规则
md.renderer.rules.table_open = () => '<div class="my-4 overflow-x-auto"><table class="border-collapse w-full">';
md.renderer.rules.table_close = () => '</table></div>';
md.renderer.rules.th_open = () => '<th class="px-4 py-2 text-left font-bold" style="border: 1px solid #93C5FD; background-color: #3B82F6; color: #FFFFFF;">';
md.renderer.rules.td_open = () => '<td class="px-4 py-2" style="border: 1px solid #93C5FD; color: #1F2937;">';

// 添加自定义样式
const markdownStyles = `
  .markdown-body {
    color: #E5E7EB;
    line-height: 1.5;
    white-space: normal;
    word-break: normal;
    overflow-wrap: break-word;
    max-width: 100%;
    word-wrap: break-word;
  }
  .markdown-body h1 { 
    @apply text-xl font-bold mt-3 mb-2;
    color: #FBBF24;
    border-bottom: 2px solid #3B82F6;
    padding-bottom: 4px;
  }
  .markdown-body h2 { 
    @apply text-lg font-bold mt-3 mb-2;
    color: #FCD34D;
    border-bottom: 1px solid #D1D5DB;
    padding-bottom: 2px;
  }
  .markdown-body h3 { 
    @apply text-base font-bold mt-2 mb-1;
    color: #FDE68A;
  }
  .markdown-body h4 { 
    @apply text-base font-bold mt-2 mb-1;
    color: #FDE68A;
  }
  .markdown-body p { 
    @apply mb-2 leading-relaxed;
    color: #E5E7EB;
    white-space: normal;
    word-break: normal;
    overflow-wrap: break-word;
    hyphens: auto;
  }
  .markdown-body a {
    color: #2563EB;
    text-decoration: underline;
  }
  .markdown-body a:hover {
    color: #1D4ED8;
  }
  .markdown-body code:not(pre code) { 
    background-color: transparent;
    color: inherit;
    padding: 0;
    border-radius: 0;
    font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    font-size: 0.75em;
    border: none;
    white-space: nowrap;
    overflow-wrap: break-word;
  }
  .markdown-body pre { 
    background-color: #1F2937;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
    margin: 8px 0;
    white-space: pre;
    word-break: normal;
  }
  .markdown-body pre code {
    color: #D1D5DB;
    font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    font-size: 0.75em;
    background: transparent;
    padding: 0;
    border: none;
    white-space: pre;
    word-break: normal;
  }
  .markdown-body ul {
    @apply list-disc list-inside mb-2;
    color: #E5E7EB;
    padding-left: 12px;
  }
  .markdown-body ol {
    @apply list-decimal list-inside mb-2;
    color: #E5E7EB;
    padding-left: 12px;
  }
  .markdown-body li {
    @apply mb-1;
    color: #E5E7EB;
  }
  .markdown-body blockquote {
    border-left: 4px solid #3B82F6;
    padding-left: 12px;
    margin: 8px 0;
    color: #1E3A8A;
    font-style: italic;
    background-color: #DBEAFE;
    padding: 8px 12px;
    border-radius: 4px;
  }
  .markdown-body hr {
    border: none;
    height: 1px;
    background-color: #93C5FD;
    margin: 12px 0;
  }
  .markdown-body table { 
    @apply border-collapse w-full my-2;
    border: 1px solid #93C5FD;
    border-radius: 6px;
    overflow: hidden;
  }
  .markdown-body th { 
    background-color: #3B82F6;
    color: #FFFFFF;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #2563EB;
  }
  .markdown-body td { 
    color: #1F2937;
    padding: 8px 12px;
    border-bottom: 1px solid #93C5FD;
  }
  .markdown-body tr:last-child td {
    border-bottom: none;
  }
  .markdown-body tr:nth-child(even) {
    background-color: #F8FAFC;
  }
  .markdown-body tr:nth-child(even) td {
    color: #1F2937;
  }
  .markdown-body tr:nth-child(odd) {
    background-color: #FFFFFF;
  }
  .markdown-body tr:nth-child(odd) td {
    color: #1F2937;
  }
  .markdown-body strong {
    color: #FBBF24;
    font-weight: 600;
  }
  .markdown-body em {
    color: #A78BFA;
    font-style: italic;
  }
`;

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

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  // 处理工具调用和输出内容
  let processedContent = content;
  
  // 如果内容包含工具调用标签，移除它们
  if (content.includes('<function_calls>')) {
    processedContent = content.split('<function_calls>')[0].trim();
  }
  if (processedContent.includes('<function_results>')) {
    processedContent = processedContent.split('<function_results>')[0].trim();
  }
  
  // 如果内容看起来像工具输出的 JSON，不渲染
  if (isToolOutput(processedContent)) {
    return null;
  }
  
  // 如果处理后的内容为空，不渲染
  if (!processedContent.trim()) {
    return null;
  }

  return (
    <Typography>
      <style>{markdownStyles}</style>
      {/* biome-ignore lint/security/noDangerouslySetInnerHtml: used in demo */}
      <div 
        className="markdown-body"
        dangerouslySetInnerHTML={{ __html: md.render(processedContent) }} 
      />
    </Typography>
  );
};

export default MarkdownRenderer; 