import { Typography, theme } from 'antd';
import React, { useMemo } from 'react';
import MarkdownIt from 'markdown-it';
import hljs from 'highlight.js';
import 'highlight.js/styles/github-dark.css';
import { MermaidDiagram } from './MermaidDiagram';

const md: MarkdownIt = new MarkdownIt({ 
  html: true, 
  breaks: false,
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

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  const { token } = theme.useToken();
  
  // 根据主题动态设置表格渲染规则
  md.renderer.rules.table_open = () => '<div class="my-4 overflow-x-auto"><table class="markdown-table">';
  md.renderer.rules.table_close = () => '</table></div>';
  md.renderer.rules.th_open = () => '<th class="markdown-th">';
  md.renderer.rules.td_open = () => '<td class="markdown-td">';
  
  // 动态生成 Markdown 样式
  const markdownStyles = `
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
  `;
  
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

  // 分割内容为 Markdown 和 Mermaid 部分
  const parts = useMemo(() => {
    const result: Array<{ type: 'markdown' | 'mermaid'; content: string; id?: string }> = [];
    let currentContent = processedContent;
    let mermaidIndex = 0;
    
    // 正则匹配 mermaid 代码块
    const mermaidRegex = /```mermaid\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;
    
    while ((match = mermaidRegex.exec(processedContent)) !== null) {
      // 添加之前的 Markdown 内容
      if (match.index > lastIndex) {
        const mdContent = processedContent.slice(lastIndex, match.index);
        if (mdContent.trim()) {
          result.push({ type: 'markdown', content: mdContent });
        }
      }
      
      // 添加 Mermaid 图表
      result.push({
        type: 'mermaid',
        content: match[1].trim(),
        id: `mermaid-${mermaidIndex++}`
      });
      
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
        } else {
          return (
            <div key={part.id} className="my-4">
              <MermaidDiagram id={part.id!} chart={part.content} />
            </div>
          );
        }
      })}
    </Typography>
  );
};

export default MarkdownRenderer; 