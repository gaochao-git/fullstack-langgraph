// 表格工具函数 - TypeScript 包装器
import type { ReactNode } from 'react';

// 从 .tsx 文件导入所有内容
import {
  getTextColumnSearchProps as getTextColumnSearchPropsImpl,
  getNumberRangeFilterProps as getNumberRangeFilterPropsImpl,
  getColumnSorter as getColumnSorterImpl,
  getPercentageValue as getPercentageValueImpl,
  getDateRangeFilterProps as getDateRangeFilterPropsImpl
} from './tableUtils.tsx';

// 重新导出所有函数
export const getTextColumnSearchProps = getTextColumnSearchPropsImpl;
export const getNumberRangeFilterProps = getNumberRangeFilterPropsImpl;
export const getColumnSorter = getColumnSorterImpl;
export const getPercentageValue = getPercentageValueImpl;
export const getDateRangeFilterProps = getDateRangeFilterPropsImpl;

// 导出类型定义
export interface TableColumnFilter {
  filterDropdown?: ReactNode;
  filterIcon?: ReactNode;
  filterable?: boolean;
}

export interface TableColumnSorter {
  sorter?: (a: any, b: any) => number;
  sortDirections?: string[];
}