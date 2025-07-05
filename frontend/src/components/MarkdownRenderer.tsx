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
    color: #E5E5E5;
  }
  .markdown-body h1 { 
    @apply text-2xl font-bold mt-6 mb-4 text-neutral-100;
  }
  .markdown-body h2 { 
    @apply text-xl font-bold mt-5 mb-3 text-neutral-100;
  }
  .markdown-body h3 { 
    @apply text-lg font-bold mt-4 mb-2 text-neutral-100;
  }
  .markdown-body p { 
    @apply mb-4 leading-7 text-neutral-300;
  }
  .markdown-body a {
    @apply text-blue-400 hover:text-blue-300 underline;
  }
  .markdown-body code:not(pre code) { 
    @apply bg-neutral-800 rounded px-2 py-1 font-mono text-sm text-neutral-100;
  }
  .markdown-body pre { 
    @apply bg-neutral-800 p-4 rounded-lg overflow-x-auto font-mono text-sm my-4;
  }
  .markdown-body ul {
    @apply list-disc list-inside mb-4 text-neutral-300;
  }
  .markdown-body ol {
    @apply list-decimal list-inside mb-4 text-neutral-300;
  }
  .markdown-body li {
    @apply mb-2;
  }
  .markdown-body blockquote {
    @apply border-l-4 border-neutral-600 pl-4 my-4 text-neutral-400;
  }
  .markdown-body hr {
    @apply border-neutral-700 my-6;
  }
  .markdown-body table { 
    @apply border-collapse w-full my-4;
  }
  .markdown-body th { 
    @apply border border-neutral-700 bg-neutral-800 px-4 py-2 text-left font-bold text-neutral-100;
  }
  .markdown-body td { 
    @apply border border-neutral-700 px-4 py-2 text-neutral-300;
  }
`;

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  console.log('Markdown content received:', content);
  
  // 如果内容包含工具调用，只显示非工具调用部分
  let processedContent = content;
  if (content.includes('<function_calls>')) {
    const parts = content.split('<function_calls>');
    processedContent = parts[0].trim();
    if (parts.length > 2) {
      processedContent += '\n\n' + parts.slice(2).join('').trim();
    }
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