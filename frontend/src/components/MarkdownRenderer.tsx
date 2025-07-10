import { Typography } from 'antd';
import React from 'react';
import MarkdownIt from 'markdown-it';

const md: MarkdownIt = new MarkdownIt({ 
  html: true, 
  breaks: true,
  // 配置代码高亮
  highlight: function (str: string, lang: string): string {
    return '<pre class="bg-neutral-800 p-4 rounded-lg overflow-x-auto font-mono text-sm my-4">' +
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
    line-height: 1.6;
  }
  .markdown-body h1 { 
    @apply text-2xl font-bold mt-6 mb-4;
    color: #1F2937;
    border-bottom: 2px solid #3B82F6;
    padding-bottom: 8px;
  }
  .markdown-body h2 { 
    @apply text-xl font-bold mt-5 mb-3;
    color: #1F2937;
    border-bottom: 1px solid #D1D5DB;
    padding-bottom: 4px;
  }
  .markdown-body h3 { 
    @apply text-lg font-bold mt-4 mb-2;
    color: #374151;
  }
  .markdown-body p { 
    @apply mb-4 leading-7;
    color: #4B5563;
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
  }
  .markdown-body pre { 
    background-color: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 16px;
    overflow-x: auto;
    margin: 16px 0;
    white-space: pre;
  }
  .markdown-body pre code {
    color: #1F2937;
    font-family: 'Menlo', 'Monaco', 'Consolas', monospace;
    background: transparent;
    padding: 0;
    border: none;
    white-space: pre;
  }
  .markdown-body ul {
    @apply list-disc list-inside mb-4;
    color: #4B5563;
    padding-left: 16px;
  }
  .markdown-body ol {
    @apply list-decimal list-inside mb-4;
    color: #4B5563;
    padding-left: 16px;
  }
  .markdown-body li {
    @apply mb-2;
    color: #4B5563;
  }
  .markdown-body blockquote {
    border-left: 4px solid #3B82F6;
    padding-left: 16px;
    margin: 16px 0;
    color: #6B7280;
    font-style: italic;
    background-color: #F8FAFC;
    padding: 12px 16px;
    border-radius: 4px;
  }
  .markdown-body hr {
    border: none;
    height: 1px;
    background-color: #D1D5DB;
    margin: 24px 0;
  }
  .markdown-body table { 
    @apply border-collapse w-full my-4;
    border: 1px solid #D1D5DB;
    border-radius: 8px;
    overflow: hidden;
  }
  .markdown-body th { 
    background-color: #F9FAFB;
    color: #1F2937;
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #D1D5DB;
  }
  .markdown-body td { 
    color: #4B5563;
    padding: 12px 16px;
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