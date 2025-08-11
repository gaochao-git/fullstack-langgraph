import { App } from 'antd';
import type { MessageInstance } from 'antd/es/message/interface';

/**
 * 使用 Ant Design 的 message hook
 * 解决静态方法不能使用动态主题的问题
 */
export const useMessage = (): MessageInstance => {
  const { message } = App.useApp();
  return message;
};