// @ts-nocheck
import React, { useState, Component } from 'react';
import { Input, Button, InputNumber, DatePicker } from 'antd';
import { SearchOutlined, CalendarOutlined } from '@ant-design/icons';
import moment from '../vendor/moment';

const { RangePicker } = DatePicker;

// 数值范围筛选器组件
class NumberRangeFilter extends Component {
  constructor(props) {
    super(props);
    // 从 selectedKeys 中恢复范围筛选值
    const existingFilter = props.selectedKeys && props.selectedKeys[0] && typeof props.selectedKeys[0] === 'object' 
      ? props.selectedKeys[0] 
      : { min: null, max: null };
    
    this.state = {
      minValue: existingFilter.min,
      maxValue: existingFilter.max,
    };
  }

  handleSearch = () => {
    const { minValue, maxValue } = this.state;
    const { setSelectedKeys, confirm } = this.props;
    
    // 创建一个包含范围信息的对象，然后将其作为单个键传递
    const rangeFilter = {
      min: (minValue !== null && minValue !== '' && minValue !== undefined && !isNaN(minValue)) ? minValue : null,
      max: (maxValue !== null && maxValue !== '' && maxValue !== undefined && !isNaN(maxValue)) ? maxValue : null
    };
    
    // 只有当至少有一个值时才设置筛选
    if (rangeFilter.min !== null || rangeFilter.max !== null) {
      setSelectedKeys([rangeFilter]);
    } else {
      setSelectedKeys([]);
    }
    confirm();
  };

  handleReset = () => {
    const { clearFilters, confirm, setSelectedKeys } = this.props;
    this.setState({
      minValue: null,
      maxValue: null,
    });
    // 确保清除筛选键
    setSelectedKeys([]);
    clearFilters();
    confirm();
  };

  render() {
    const { unit } = this.props;
    const { minValue, maxValue } = this.state;

    return (
      <div style={{ padding: 8 }}>
        <div style={{ marginBottom: 8 }}>
          <InputNumber
            placeholder={`最小值${unit}`}
            value={minValue}
            onChange={(value) => this.setState({ minValue: value })}
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ marginBottom: 8 }}>
          <InputNumber
            placeholder={`最大值${unit}`}
            value={maxValue}
            onChange={(value) => this.setState({ maxValue: value })}
            style={{ width: '100%' }}
          />
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            type="primary"
            onClick={this.handleSearch}
            size="small"
            style={{ width: 90 }}
          >
            筛选
          </Button>
          <Button
            onClick={this.handleReset}
            size="small"
            style={{ width: 90 }}
          >
            重置
          </Button>
        </div>
      </div>
    );
  }
}

// 文本筛选组件
export const getTextColumnSearchProps = (dataIndex, placeholder = '搜索') => ({
  filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
    <div style={{ padding: 8 }}>
      <Input
        placeholder={`搜索 ${placeholder}`}
        value={selectedKeys[0]}
        onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
        onPressEnter={() => confirm()}
        style={{ marginBottom: 8, display: 'block' }}
      />
      <div style={{ display: 'flex', gap: '8px' }}>
        <Button
          type="primary"
          onClick={() => confirm()}
          icon="search"
          size="small"
          style={{ width: 90 }}
        >
          搜索
        </Button>
        <Button
          onClick={() => {
            clearFilters();
            confirm();
          }}
          size="small"
          style={{ width: 90 }}
        >
          重置
        </Button>
      </div>
    </div>
  ),
  filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
  onFilter: (value, record) => {
    const cellValue = dataIndex.includes('.') 
      ? dataIndex.split('.').reduce((obj, key) => obj?.[key], record)
      : record[dataIndex];
    // 确保cellValue不为null或undefined，并且可以安全地转换为字符串
    if (cellValue === null || typeof cellValue === 'undefined') {
      return false;
    }
    // 安全转换为字符串
    const strValue = typeof cellValue === 'string' ? cellValue : 
                     typeof cellValue === 'number' ? cellValue.toString() :
                     typeof cellValue.toString === 'function' ? cellValue.toString() : '';
    return strValue.toLowerCase().includes(value.toLowerCase());
  },
});

// 数值范围筛选组件
export const getNumberRangeFilterProps = (dataIndex, unit = '', getValue = null) => ({
  filterDropdown: (props) => (
    <NumberRangeFilter 
      {...props} 
      unit={unit} 
    />
  ),
  filterIcon: filtered => <SearchOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
  onFilter: (value, record) => {
    // 检查 value 是否存在
    if (!value) {
      return true;
    }
    
    // 处理范围筛选对象
    let minFilter = null;
    let maxFilter = null;
    
    if (typeof value === 'object' && !Array.isArray(value)) {
      // 新的对象格式 {min: x, max: y}
      minFilter = value.min;
      maxFilter = value.max;
    } else if (Array.isArray(value) && value.length > 0) {
      // 兼容数组格式 [min, max]
      minFilter = value[0];
      maxFilter = value[1];
    } else {
      // 如果都不是，返回 true（显示所有）
      return true;
    }
    
    // 如果没有有效的筛选条件，显示所有
    if (minFilter === null && maxFilter === null) {
      return true;
    }
    
    const cellValue = getValue 
      ? getValue(record)
      : (dataIndex.includes('.') 
          ? dataIndex.split('.').reduce((obj, key) => obj?.[key], record)
          : record[dataIndex]);
    
    // 临时调试信息
    if (dataIndex === 'memory_usage' || dataIndex === 'disk_usage') {
      console.log(`筛选调试 ${dataIndex}:`, {
        getValue: !!getValue,
        cellValue,
        record: { used_memory: record.used_memory, total_memory: record.total_memory, used_disk: record.used_disk, total_disk: record.total_disk }
      });
    }
    
    // 确保 cellValue 不是 null 或 undefined，并且可以安全地转换为数字
    if (cellValue === null || typeof cellValue === 'undefined') return false;
    
    const numValue = typeof cellValue === 'number' ? cellValue : parseFloat(cellValue || 0);
    if (isNaN(numValue)) return false;
    
    // 应用筛选条件
    if (minFilter !== null && maxFilter !== null) {
      return numValue >= minFilter && numValue <= maxFilter;
    } else if (minFilter !== null) {
      return numValue >= minFilter;
    } else if (maxFilter !== null) {
      return numValue <= maxFilter;
    }
    return true;
  },
});

// 通用排序函数
export const getColumnSorter = (dataIndex, getValue = null) => {
  return {
    sorter: (a, b) => {
      const aValue = getValue 
        ? getValue(a)
        : (dataIndex.includes('.') 
            ? dataIndex.split('.').reduce((obj, key) => obj?.[key], a)
            : a[dataIndex]);
      const bValue = getValue 
        ? getValue(b)
        : (dataIndex.includes('.') 
            ? dataIndex.split('.').reduce((obj, key) => obj?.[key], b)
            : b[dataIndex]);
      
      // 数值排序
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return aValue - bValue;
      }
      
      // 字符串排序
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return aValue.localeCompare(bValue);
      }
      
      // 日期排序
      if (aValue instanceof Date && bValue instanceof Date) {
        return aValue.getTime() - bValue.getTime();
      }
      
      // 转换为字符串后排序
      return String(aValue || '').localeCompare(String(bValue || ''));
    },
    sortDirections: ['descend', 'ascend'],
  };
};

// 百分比值的获取函数
export const getPercentageValue = (record, usedField, totalField) => {
  const used = record[usedField];
  const total = record[totalField];
  return total > 0 ? (used / total) * 100 : 0;
};

// 日期范围筛选器组件
class DateRangeFilter extends Component {
  constructor(props) {
    super(props);
    // 从 selectedKeys 中恢复日期范围筛选值
    const existingFilter = props.selectedKeys && props.selectedKeys[0] && typeof props.selectedKeys[0] === 'object' 
      ? props.selectedKeys[0] 
      : { startDate: null, endDate: null };
    
    console.log('DateRangeFilter 初始化', { props, existingFilter });
    
    this.state = {
      startDate: existingFilter.startDate ? moment(existingFilter.startDate) : null,
      endDate: existingFilter.endDate ? moment(existingFilter.endDate) : null,
    };
  }

  handleSearch = () => {
    const { startDate, endDate } = this.state;
    const { setSelectedKeys, confirm } = this.props;
    
    // 创建一个包含日期范围信息的对象
    const dateRangeFilter = {
      startDate: startDate ? startDate.format('YYYY-MM-DD') : null,
      endDate: endDate ? endDate.format('YYYY-MM-DD') : null
    };
    
    // 只有当至少有一个日期时才设置筛选
    if (dateRangeFilter.startDate || dateRangeFilter.endDate) {
      setSelectedKeys([dateRangeFilter]);
    } else {
      setSelectedKeys([]);
    }
    confirm();
  };

  handleReset = () => {
    const { clearFilters, confirm, setSelectedKeys } = this.props;
    this.setState({
      startDate: null,
      endDate: null,
    });
    // 确保清除筛选键
    setSelectedKeys([]);
    clearFilters();
    confirm();
  };

  handleRangeChange = (dates) => {
    this.setState({
      startDate: dates && dates[0] ? dates[0] : null,
      endDate: dates && dates[1] ? dates[1] : null,
    });
  };

  render() {
    const { startDate, endDate } = this.state;

    return (
      <div style={{ padding: 8 }}>
        <div style={{ marginBottom: 8 }}>
          <RangePicker
            value={[startDate, endDate]}
            onChange={this.handleRangeChange}
            style={{ width: '100%' }}
            placeholder={['开始日期', '结束日期']}
            format="YYYY-MM-DD"
          />
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <Button
            type="primary"
            onClick={this.handleSearch}
            size="small"
            style={{ width: 90 }}
          >
            筛选
          </Button>
          <Button
            onClick={this.handleReset}
            size="small"
            style={{ width: 90 }}
          >
            重置
          </Button>
        </div>
      </div>
    );
  }
}

// 日期范围筛选组件
export const getDateRangeFilterProps = (dataIndex, getValue = null) => ({
  // 添加调试信息
  _debug_info: { dataIndex, hasGetValue: !!getValue },
  filterDropdown: (props) => (
    <DateRangeFilter 
      {...props} 
    />
  ),
  filterIcon: filtered => <CalendarOutlined style={{ color: filtered ? '#1890ff' : undefined }} />,
  onFilter: (value, record) => {
    console.log('DateRangeFilter onFilter 开始', { value, record, dataIndex });
    
    // 检查 value 是否存在
    if (!value) {
      console.log('DateRangeFilter onFilter: value 为空，返回 true');
      return true;
    }
    
    // 处理日期范围筛选对象
    let startDateFilter = null;
    let endDateFilter = null;
    
    if (typeof value === 'object' && !Array.isArray(value)) {
      // 对象格式 {startDate: 'YYYY-MM-DD', endDate: 'YYYY-MM-DD'}
      startDateFilter = value.startDate;
      endDateFilter = value.endDate;
      console.log('DateRangeFilter 解析筛选值', { startDateFilter, endDateFilter });
    } else {
      // 如果不是对象，返回 true（显示所有）
      console.log('DateRangeFilter: value 不是对象，返回 true');
      return true;
    }
    
    // 如果没有有效的筛选条件，显示所有
    if (!startDateFilter && !endDateFilter) {
      console.log('DateRangeFilter: 没有筛选条件，返回 true');
      return true;
    }
    
    // 获取记录中的日期值
    let cellValue;
    try {
      cellValue = getValue 
        ? getValue(record)
        : (dataIndex.includes('.') 
            ? dataIndex.split('.').reduce((obj, key) => obj?.[key], record)
            : record[dataIndex]);
      
      console.log('DateRangeFilter 获取值', { cellValue, useGetValue: !!getValue });
    } catch (e) {
      console.error('DateRangeFilter 获取值错误:', e, { record });
      return false;
    }
    
    if (!cellValue) {
      console.log('DateRangeFilter: cellValue 为空，返回 false');
      return false;
    }
    
    // 将日期值转换为Date对象
    let recordDate;
    let recordDateStr;
    
    // 处理特殊字符串值
    if (typeof cellValue === 'string') {
      const specialStrings = ['无法预测', '长期内不会满', '增长缓慢', '增长缓慢，长期内不会满'];
      for (const specialStr of specialStrings) {
        if (cellValue.includes(specialStr)) {
          console.log('DateRangeFilter: 特殊字符串不参与筛选', { cellValue, matchedSpecialStr: specialStr });
          return false; // 特殊字符串不参与日期筛选
        }
      }
    }
    
    try {
      if (cellValue instanceof Date) {
        recordDate = cellValue;
        console.log('DateRangeFilter: cellValue 是 Date 实例');
      } else if (typeof cellValue === 'string') {
        console.log('DateRangeFilter: cellValue 是字符串，尝试转换为日期', { cellValue });
        recordDate = new Date(cellValue);
      } else if (cellValue !== null && typeof cellValue !== 'undefined' && typeof cellValue.toString === 'function') {
        // 如果 cellValue 不是 Date 或字符串，但有 toString 方法，尝试转换
        const strValue = cellValue.toString();
        console.log('DateRangeFilter: cellValue 转换为字符串', { strValue });
        recordDate = new Date(strValue);
      } else {
        console.log('DateRangeFilter: cellValue 无法处理', { cellValue });
        return false;
      }
      
      // 检查日期是否有效
      if (isNaN(recordDate.getTime())) {
        console.log('DateRangeFilter: 无效日期', { recordDate });
        return false;
      }
      
      recordDateStr = recordDate.toISOString().split('T')[0]; // 格式化为 YYYY-MM-DD
      console.log('DateRangeFilter: 日期转换成功', { recordDateStr });
    } catch (error) {
      console.error('DateRangeFilter 日期转换错误:', error, { cellValue });
      return false;
    }
    
    // 应用筛选条件
    let result = false;
    if (startDateFilter && endDateFilter) {
      result = recordDateStr >= startDateFilter && recordDateStr <= endDateFilter;
    } else if (startDateFilter) {
      result = recordDateStr >= startDateFilter;
    } else if (endDateFilter) {
      result = recordDateStr <= endDateFilter;
    }
    
    console.log('DateRangeFilter 筛选结果', { result, recordDateStr, startDateFilter, endDateFilter });
    return result;
  },
});