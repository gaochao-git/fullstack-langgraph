"""JSONL文件中char_interval的修复工具"""

import json
import logging
from typing import List, Dict, Tuple, Optional
import difflib

logger = logging.getLogger(__name__)


def find_text_position(text: str, extraction_text: str) -> Optional[Tuple[int, int]]:
    """
    尝试在文本中找到提取文本的位置
    
    Args:
        text: 原始文本
        extraction_text: 提取的文本
        
    Returns:
        (start_pos, end_pos) 或 None
    """
    # 1. 尝试精确匹配
    pos = text.find(extraction_text)
    if pos >= 0:
        return (pos, pos + len(extraction_text))
    
    # 2. 去除空格再匹配
    normalized_extraction = extraction_text.replace(" ", "")
    normalized_text = text.replace(" ", "")
    pos = normalized_text.find(normalized_extraction)
    
    if pos >= 0:
        # 映射回原始位置
        original_pos = 0
        normalized_pos = 0
        
        # 找开始位置
        while normalized_pos < pos and original_pos < len(text):
            if text[original_pos] != " ":
                normalized_pos += 1
            original_pos += 1
        start = original_pos
        
        # 找结束位置
        while normalized_pos < pos + len(normalized_extraction) and original_pos < len(text):
            if text[original_pos] != " ":
                normalized_pos += 1
            original_pos += 1
        end = original_pos
        
        return (start, end)
    
    # 3. 模糊匹配
    best_ratio = 0
    best_pos = None
    min_ratio = 0.85  # 相似度阈值
    
    # 尝试不同长度的子串
    for length_delta in range(-2, 3):  # 允许长度偏差±2
        target_len = len(extraction_text) + length_delta
        if target_len < 1 or target_len > len(text):
            continue
            
        for i in range(len(text) - target_len + 1):
            substr = text[i:i + target_len]
            ratio = difflib.SequenceMatcher(None, substr, extraction_text).ratio()
            
            if ratio > best_ratio and ratio >= min_ratio:
                best_ratio = ratio
                best_pos = (i, i + target_len)
    
    if best_pos:
        logger.info(f"模糊匹配成功: '{extraction_text}' -> 位置{best_pos}, 相似度{best_ratio:.2f}")
    
    return best_pos


def fix_jsonl_file(jsonl_path: str, output_path: Optional[str] = None) -> int:
    """
    修复JSONL文件中缺失的char_interval
    
    Args:
        jsonl_path: 输入JSONL文件路径
        output_path: 输出文件路径，如果为None则覆盖原文件
        
    Returns:
        修复的提取数量
    """
    if output_path is None:
        output_path = jsonl_path
    
    fixed_count = 0
    
    # 读取JSONL
    documents = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                documents.append(json.loads(line))
    
    # 修复每个文档
    for doc in documents:
        text = doc.get('text', '')
        extractions = doc.get('extractions', [])
        
        for extraction in extractions:
            # 检查是否需要修复
            char_interval = extraction.get('char_interval')
            if char_interval is None or (isinstance(char_interval, dict) and char_interval.get('start_pos') is None):
                # 尝试找到位置
                extraction_text = extraction.get('extraction_text', '')
                position = find_text_position(text, extraction_text)
                
                if position:
                    extraction['char_interval'] = {
                        'start_pos': position[0],
                        'end_pos': position[1]
                    }
                    extraction['alignment_status'] = 'match_fuzzy'
                    fixed_count += 1
                    
                    logger.info(f"修复了 '{extraction_text}' 的位置: {position}")
    
    # 保存修复后的JSONL
    with open(output_path, 'w', encoding='utf-8') as f:
        for doc in documents:
            json.dump(doc, f, ensure_ascii=False)
            f.write('\n')
    
    logger.info(f"修复完成: 共修复 {fixed_count} 个提取的位置信息")
    return fixed_count


def fix_jsonl_content(jsonl_content: str) -> str:
    """
    修复JSONL内容字符串
    
    Args:
        jsonl_content: JSONL内容字符串
        
    Returns:
        修复后的JSONL内容
    """
    documents = []
    for line in jsonl_content.strip().split('\n'):
        if line.strip():
            documents.append(json.loads(line))
    
    # 修复逻辑同上
    for doc in documents:
        text = doc.get('text', '')
        extractions = doc.get('extractions', [])
        
        for extraction in extractions:
            char_interval = extraction.get('char_interval')
            if char_interval is None or (isinstance(char_interval, dict) and char_interval.get('start_pos') is None):
                extraction_text = extraction.get('extraction_text', '')
                position = find_text_position(text, extraction_text)
                
                if position:
                    extraction['char_interval'] = {
                        'start_pos': position[0],
                        'end_pos': position[1]
                    }
                    extraction['alignment_status'] = 'match_fuzzy'
    
    # 重新生成JSONL
    lines = []
    for doc in documents:
        lines.append(json.dumps(doc, ensure_ascii=False))
    
    return '\n'.join(lines)