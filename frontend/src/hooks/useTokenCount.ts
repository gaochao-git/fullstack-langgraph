import { useState, useCallback, useEffect, useRef } from 'react';
import { omind_post } from '@/utils/base_api';
import { debounce } from 'lodash';

interface TokenCountResult {
  text_length: number;
  token_count: number;
  chinese_chars: number;
  english_chars: number;
  avg_chars_per_token: number;
}

interface UseTokenCountReturn {
  getTokenCount: (text: string) => Promise<TokenCountResult | null>;
  getBatchTokenCount: (texts: string[]) => Promise<TokenCountResult[]>;
  cachedTokenCount: (text: string) => number | null;
  estimateTokenCount: (text: string) => number;
}

// Token计数缓存
const tokenCache = new Map<string, TokenCountResult>();
const MAX_CACHE_SIZE = 1000;

// 批处理队列
let batchQueue: { text: string; resolve: (value: TokenCountResult | null) => void }[] = [];
let batchTimer: NodeJS.Timeout | null = null;

export const useTokenCount = (): UseTokenCountReturn => {
  const abortControllerRef = useRef<AbortController | null>(null);

  // 粗略估算token数（用于快速显示）
  const estimateTokenCount = useCallback((text: string): number => {
    // 使用与后端类似的估算逻辑
    const chineseChars = (text.match(/[\u4e00-\u9fff]/g) || []).length;
    const englishChars = text.length - chineseChars;
    // GPT模型中，中文字符平均约1.5-2个字符一个token，英文约3-4个字符一个token
    return Math.ceil(chineseChars / 1.8 + englishChars / 3.5);
  }, []);

  // 从缓存获取token数
  const cachedTokenCount = useCallback((text: string): number | null => {
    const cached = tokenCache.get(text);
    return cached ? cached.token_count : null;
  }, []);

  // 批量获取token计数
  const getBatchTokenCount = useCallback(async (texts: string[]): Promise<TokenCountResult[]> => {
    try {
      // 先检查缓存
      const uncachedTexts: string[] = [];
      const results: TokenCountResult[] = [];
      
      texts.forEach(text => {
        const cached = tokenCache.get(text);
        if (cached) {
          results.push(cached);
        } else {
          uncachedTexts.push(text);
        }
      });

      // 如果都在缓存中，直接返回
      if (uncachedTexts.length === 0) {
        return results;
      }

      // 调用API获取未缓存的
      const response = await omind_post('/api/v1/chat/count-tokens', {
        texts: uncachedTexts
      });

      if (response.status === 'ok' && response.data?.results) {
        response.data.results.forEach((result: TokenCountResult, index: number) => {
          const text = uncachedTexts[index];
          
          // 添加到缓存
          if (tokenCache.size >= MAX_CACHE_SIZE) {
            // 删除最旧的缓存项
            const firstKey = tokenCache.keys().next().value;
            if (firstKey) tokenCache.delete(firstKey);
          }
          tokenCache.set(text, result);
          
          results.push(result);
        });
      }

      return results;
    } catch (error) {
      console.error('获取token计数失败:', error);
      // 返回估算值
      return texts.map(text => ({
        text_length: text.length,
        token_count: estimateTokenCount(text),
        chinese_chars: (text.match(/[\u4e00-\u9fff]/g) || []).length,
        english_chars: text.length - (text.match(/[\u4e00-\u9fff]/g) || []).length,
        avg_chars_per_token: 0
      }));
    }
  }, [estimateTokenCount]);

  // 处理批量请求
  const processBatch = useCallback(async () => {
    if (batchQueue.length === 0) return;

    const currentBatch = [...batchQueue];
    batchQueue = [];

    const texts = currentBatch.map(item => item.text);
    const results = await getBatchTokenCount(texts);

    currentBatch.forEach((item, index) => {
      item.resolve(results[index] || null);
    });
  }, [getBatchTokenCount]);

  // 单个文本的token计数（带批处理优化）
  const getTokenCount = useCallback(async (text: string): Promise<TokenCountResult | null> => {
    // 检查缓存
    const cached = tokenCache.get(text);
    if (cached) {
      return cached;
    }

    // 添加到批处理队列
    return new Promise((resolve) => {
      batchQueue.push({ text, resolve });

      // 清除之前的定时器
      if (batchTimer) {
        clearTimeout(batchTimer);
      }

      // 设置新的定时器，10ms后处理批量请求
      batchTimer = setTimeout(() => {
        processBatch();
      }, 10);
    });
  }, [processBatch]);

  // 组件卸载时清理
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (batchTimer) {
        clearTimeout(batchTimer);
      }
    };
  }, []);

  return {
    getTokenCount,
    getBatchTokenCount,
    cachedTokenCount,
    estimateTokenCount
  };
};