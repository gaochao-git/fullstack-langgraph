import React from 'react';
import { createRoot, Root } from 'react-dom/client';
import AgentChatWidget, { type AgentChatWidgetProps } from './AgentChatWidget';

const roots = new WeakMap<HTMLElement, Root>();

export function mountAgentChatWidget(container: HTMLElement, props: AgentChatWidgetProps) {
  let root = roots.get(container);
  if (!root) {
    root = createRoot(container);
    roots.set(container, root);
  }
  root.render(
    <React.StrictMode>
      <AgentChatWidget {...props} />
    </React.StrictMode>
  );
  return () => {
    root?.unmount();
    roots.delete(container);
  };
}

