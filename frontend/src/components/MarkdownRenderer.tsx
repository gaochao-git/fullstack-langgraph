import { Typography } from 'antd';
import React from 'react';
import MarkdownIt from 'markdown-it';

const md: MarkdownIt = new MarkdownIt({ 
  html: true, 
  breaks: true,
  // 配置代码高亮
  highlight: function (str: string, lang: string): string {
    return '<pre class="bg-neutral-900 p-3 rounded-lg overflow-x-auto font-mono text-xs my-3">' +
           '<code class="bg-neutral-900">' +
           md.utils.escapeHtml(str) +
           '</code></pre>';
  }
});

// 自定义渲染规则
md.renderer.rules.table_open = () => '<div class="my-3 overflow-x-auto"><table class="border-collapse w-full">';
md.renderer.rules.table_close = () => '</table></div>';
md.renderer.rules.th_open = () => '<th class="border border-neutral-600 px-3 py-2 text-left font-bold">';
md.renderer.rules.td_open = () => '<td class="border border-neutral-600 px-3 py-2">';

// 添加自定义样式
const markdownStyles = `
  .markdown-body h1 { @apply text-2xl font-bold mt-4 mb-2; }
  .markdown-body h2 { @apply text-xl font-bold mt-3 mb-2; }
  .markdown-body h3 { @apply text-lg font-bold mt-3 mb-1; }
  .markdown-body p { @apply mb-3 leading-7; }
  .markdown-body code { @apply bg-neutral-900 rounded px-1 py-0.5 font-mono text-xs; }
  .markdown-body pre { @apply bg-neutral-900 p-3 rounded-lg overflow-x-auto font-mono text-xs my-3; }
  .markdown-body table { @apply border-collapse w-full; }
  .markdown-body th { @apply border border-neutral-600 px-3 py-2 text-left font-bold; }
  .markdown-body td { @apply border border-neutral-600 px-3 py-2; }
`;

interface MarkdownRendererProps {
  content: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  console.log('Markdown content received:', content);
  return (
    <Typography>
      <style>{markdownStyles}</style>
      {/* biome-ignore lint/security/noDangerouslySetInnerHtml: used in demo */}
      <div 
        className="markdown-body"
        dangerouslySetInnerHTML={{ __html: md.render(content) }} 
      />
    </Typography>
  );
};

export default MarkdownRenderer; 