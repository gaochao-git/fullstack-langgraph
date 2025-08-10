import React, { createElement } from 'react';
import { Icons, IconCategories, type IconName } from '@/icons';
import iconConfigData from '@/icons/icon-config.json';

// 定义分类颜色
export const categoryColors = iconConfigData.categories;

// 图标分类映射 - 从 icon-config.json 自动生成
export const iconCategoryMap: { [key: string]: string } = {};
Object.entries(iconConfigData.icons).forEach(([iconKey, iconData]) => {
  const iconName = iconKey.replace('lucide:', '');
  const pascalName = iconName.split('-').map(part => 
    part.charAt(0).toUpperCase() + part.slice(1)
  ).join('');
  iconCategoryMap[pascalName] = iconData.category;
});

// 图标配置数据 - 从 icon-config.json 自动生成
export const iconConfig = Object.entries(iconConfigData.icons).map(([iconKey, iconData]) => {
  const iconName = iconKey.replace('lucide:', '');
  const pascalName = iconName.split('-').map(part => 
    part.charAt(0).toUpperCase() + part.slice(1)
  ).join('');
  
  return {
    name: pascalName,
    label: iconData.label,
    category: iconData.category
  };
});

// 根据图标名称渲染图标组件
export const renderIcon = (iconName: string, size: number = 18, color?: string) => {
  // 如果没有指定颜色，则根据分类获取颜色
  if (!color) {
    const category = iconCategoryMap[iconName];
    const categoryData = categoryColors[category as keyof typeof categoryColors];
    color = categoryData?.color || '#666666';
  }
  
  // 使用 Icons 对象获取图标组件
  if (iconName in Icons) {
    const IconComponent = Icons[iconName as IconName];
    return createElement(IconComponent as any, { size, color });
  }
  
  // 默认图标
  return createElement(Icons.Bot as any, { size, color });
};

// 获取图标背景色（根据分类）
export const getIconBackgroundColor = (iconName: string, opacity: string = '20'): string => {
  const category = iconCategoryMap[iconName];
  if (category) {
    const categoryData = categoryColors[category as keyof typeof categoryColors];
    const categoryColor = categoryData?.color || '#1677ff';
    return categoryColor + opacity; // 添加透明度
  }
  const defaultColor = categoryColors['基础']?.color || '#1677ff';
  return defaultColor + opacity; // 默认蓝色背景
};

// 按分类分组图标
export const getIconsByCategory = () => {
  const grouped: { [category: string]: typeof iconConfig } = {};
  
  iconConfig.forEach(icon => {
    if (!grouped[icon.category]) {
      grouped[icon.category] = [];
    }
    grouped[icon.category].push(icon);
  });
  
  return grouped;
};

// 获取所有可用的图标名称
export const getAllIconNames = (): string[] => {
  return iconConfig.map(icon => icon.name);
};

// 获取图标标签
export const getIconLabel = (iconName: string): string => {
  const icon = iconConfig.find(icon => icon.name === iconName);
  return icon?.label || iconName;
};

// 获取图标分类
export const getIconCategory = (iconName: string): string => {
  return iconCategoryMap[iconName] || '基础';
};