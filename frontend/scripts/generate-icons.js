import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 读取 icon-config.json
const iconConfig = JSON.parse(
  fs.readFileSync(path.join(__dirname, '../src/icons/icon-config.json'), 'utf-8')
);

// 将 kebab-case 转换为 PascalCase
function toPascalCase(str) {
  return str
    .split('-')
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join('');
}

// 收集所有需要导入的图标
const iconImports = new Set();
const iconNames = new Set();

Object.keys(iconConfig.icons).forEach(iconKey => {
  const iconName = iconKey.replace('lucide:', '');
  const componentName = toPascalCase(iconName);
  iconImports.add(componentName);
  iconNames.add(componentName);
});

// 确保包含别名需要的图标
const requiredIcons = ['Settings', 'Bot', 'ShieldCheck', 'Clock', 'Users', 'Package', 'List', 'AppWindow'];
requiredIcons.forEach(icon => iconImports.add(icon));

// 生成导入语句
const imports = Array.from(iconImports).sort();
const importStatement = `import {\n  ${imports.join(',\n  ')}\n} from 'lucide-react';`;

// 生成导出语句
const exportStatement = `export const Icons = {\n  ${imports.join(',\n  ')},\n  // 别名\n  Setting: Settings,\n  Robot: Bot,\n  Safety: ShieldCheck,\n  ClockCircle: Clock,\n  Team: Users,\n  Api: Package,\n  UnorderedList: List,\n  Appstore: AppWindow\n} as const;`;

// 生成分类
const categories = {};
Object.entries(iconConfig.categories).forEach(([key, value]) => {
  const categoryIcons = Object.entries(iconConfig.icons)
    .filter(([_, icon]) => icon.category === key)
    .map(([iconKey]) => {
      const iconName = iconKey.replace('lucide:', '');
      return toPascalCase(iconName);
    });
  
  categories[value.label] = categoryIcons;
});

const categoriesString = JSON.stringify(categories, null, 2)
  .replace(/"([^"]+)":/g, '$1:');

// 生成完整的文件内容
const fileContent = `/**
 * 全局图标定义
 * 只使用 Lucide 图标，保持统一的视觉风格
 * 
 * 此文件由 scripts/generate-icons.js 自动生成
 * 请勿手动修改，如需添加图标请编辑 icon-config.json
 */

import React from 'react';
${importStatement}

// 导出所有图标
${exportStatement}

// 图标类型
export type IconName = keyof typeof Icons;

// 图标分类
export const IconCategories = ${categoriesString};

// 获取图标组件的辅助函数
export function getIcon(name: IconName) {
  return Icons[name] || Icons.Appstore;
}

// 简单的图标渲染组件
interface IconProps {
  name?: string;
  className?: string;
  style?: React.CSSProperties;
  size?: number;
}

export const Icon: React.FC<IconProps> = ({ name, className, style, size = 16 }) => {
  if (!name) return null;
  
  // 直接使用图标名称
  if (name in Icons) {
    const IconComponent = Icons[name as IconName];
    return <IconComponent className={className} style={style} size={size} />;
  }
  
  // 默认图标
  return <Icons.Appstore className={className} style={style} size={size} />;
};
`;

// 写入文件
fs.writeFileSync(
  path.join(__dirname, '../src/icons/index.tsx'),
  fileContent,
  'utf-8'
);

console.log('✅ 图标文件生成成功！');