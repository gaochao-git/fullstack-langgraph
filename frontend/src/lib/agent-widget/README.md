# Agent Chat Widget

Embeddable chat widget that reuses the existing Agent Chat (AgentChat/ChatEngine) features.

## Usage (React)

```tsx
import { AgentChatWidget } from '@/lib/agent-widget';

export default function Example() {
  return <AgentChatWidget agentId="diagnostic_agent" height="100%" />;
}
```

## Programmatic Mounting

```ts
import { mountAgentChatWidget } from '@/lib/agent-widget';

const unmount = mountAgentChatWidget(document.getElementById('agent-chat')!, {
  agentId: 'diagnostic_agent',
  height: '100%'
});

// later: unmount()
```

The widget preserves all features provided by the project’s AI Agent (streaming, tools, files, models, histories). It will evolve automatically as core components evolve.

  - 组件库
      - frontend/src/lib/agent-widget/AgentChatWidget.tsx:1
      - frontend/src/lib/agent-widget/index.ts:1
      - frontend/src/lib/agent-widget/mount.tsx:1
      - frontend/src/lib/agent-widget/README.md:1
  - IDC 研究页集成
      - frontend/src/pages/idc_research/IDCAnalysisPage.tsx:3 引入库组件
      - frontend/src/pages/idc_research/IDCAnalysisPage.tsx:141 在右侧面板渲染 <AgentChatWidget agentId="diagnostic_agent" height="100%" />
      - frontend/src/pages/idc_research/IDCAnalysisPage.tsx:286 最小化时显示“打开AI助手”按钮
      - 移除了无用的 handleQuerySubmit，保留最小化开关逻辑

  库组件用法

  - React 直接使用
      - import { AgentChatWidget } from '@/lib/agent-widget'
      - <AgentChatWidget agentId="diagnostic_agent" height="100%" />
  - 程序化挂载
      - import { mountAgentChatWidget } from '@/lib/agent-widget'
      - const unmount = mountAgentChatWidget(el, { agentId: 'diagnostic_agent', height: '100%' });

  说明

  - 组件基于现有 ChatEngine、useStream、agentApi 等，继承了历史会话、工具调用审批、文件上传/预览/下载、多模型切换、线程管理等全部能力；后续功能迭代会自然继承。
  - IDC 页默认展示 diagnostic_agent。如需切换为其他智能体，可把 agentId 改为目标 ID，或提供一个下拉选择 UI。
  - 之前 IDC 页“用户提问驱动标签切换”的逻辑（handleQuerySubmit）已移除。如需要保留此联动，可在库外对消息进行监听/联动，或在库组件上扩展回调（我可以继续加）。

 下一步：

  - 把 agentId 做成可配置（环境变量/系统配置/URL 参数）？
  - 在 IDC 页加一个智能体选择器，动态切换 agentId？
  - 运行前端构建/启动验证一遍并调整样式细节？