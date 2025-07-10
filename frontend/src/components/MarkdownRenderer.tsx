import { Typography } from 'antd';
import React from 'react';
import MarkdownIt from 'markdown-it';

const md: MarkdownIt = new MarkdownIt({ 
  html: true, 
  breaks: false,
  // 配置代码高亮
  highlight: function (str: string, lang: string): string {
    return '<pre class="bg-neutral-800 p-3 rounded-md overflow-x-auto font-mono text-sm my-2">' +
           '<code class="text-neutral-100">' +
           md.utils.escapeHtml(str) +
           '</code></pre>';
  }
});

// 自定义渲染规则
md.renderer.rules.table_open = () => '<div class="my-4 overflow-x-auto"><table class="border-collapse w-full">';
md.renderer.rules.table_close = () => '</table></div>';
md.renderer.rules.th_open = () => '<th class="border border-neutral-700 bg-neutral-800 px-4 py-2 text-left font-bold text-neutral-100">';
md.renderer.rules.td_open = () => '<td class="border border-neutral-700 px-4 py-2 text-neutral-300">';

// 添加自定义样式
const markdownStyles = `
  .markdown-body {
    color: #374151;
    line-height: 1.5;
    white-space: normal;
    word-break: normal;
    overflow-wrap: break-word;
    max-width: 100%;
    word-wrap: break-word;
  }
  .markdown-body h1 { 
    @apply text-xl font-bold mt-3 mb-2;
    color: #1F2937;
    border-bottom: 2px solid #3B82F6;
    padding-bottom: 4px;
  }
  .markdown-body h2 { 
    @apply text-lg font-bold mt-3 mb-2;
    color: #1F2937;
    border-bottom: 1px solid #D1D5DB;
    padding-bottom: 2px;
  }
  .markdown-body h3 { 
    @apply text-base font-bold mt-2 mb-1;
    color: #374151;
  }
  .markdown-body p { 
    @apply mb-2 leading-relaxed;
    color: #4B5563;
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
    background-color: #F3F4F6;
    color: #DC2626;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    font-size: 0.875em;
    border: 1px solid #E5E7EB;
    white-space: nowrap;
    overflow-wrap: break-word;
  }
  .markdown-body pre { 
    background-color: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 12px;
    overflow-x: auto;
    margin: 8px 0;
    white-space: pre;
    word-break: normal;
  }
  .markdown-body pre code {
    color: #1F2937;
    font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    background: transparent;
    padding: 0;
    border: none;
    white-space: pre;
    word-break: normal;
  }
  .markdown-body ul {
    @apply list-disc list-inside mb-2;
    color: #4B5563;
    padding-left: 12px;
  }
  .markdown-body ol {
    @apply list-decimal list-inside mb-2;
    color: #4B5563;
    padding-left: 12px;
  }
  .markdown-body li {
    @apply mb-1;
    color: #4B5563;
  }
  .markdown-body blockquote {
    border-left: 4px solid #3B82F6;
    padding-left: 12px;
    margin: 8px 0;
    color: #6B7280;
    font-style: italic;
    background-color: #F8FAFC;
    padding: 8px 12px;
    border-radius: 4px;
  }
  .markdown-body hr {
    border: none;
    height: 1px;
    background-color: #D1D5DB;
    margin: 12px 0;
  }
  .markdown-body table { 
    @apply border-collapse w-full my-2;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    overflow: hidden;
  }
  .markdown-body th { 
    background-color: #F9FAFB;
    color: #1F2937;
    padding: 8px 12px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #D1D5DB;
  }
  .markdown-body td { 
    color: #4B5563;
    padding: 8px 12px;
    border-bottom: 1px solid #E5E7EB;
  }
  .markdown-body tr:last-child td {
    border-bottom: none;
  }
  .markdown-body tr:nth-child(even) {
    background-color: #F9FAFB;
  }
  .markdown-body strong {
    color: #1F2937;
    font-weight: 600;
  }
  .markdown-body em {
    color: #6B7280;
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