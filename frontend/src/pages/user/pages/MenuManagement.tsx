import React, { useState, useEffect } from 'react';
import { 
  Tree, Card, Form, Input, Select, Button, Space, 
  message, Modal, Dropdown, Menu as AntMenu, Spin
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, 
  EyeOutlined, EyeInvisibleOutlined, MoreOutlined,
  HomeOutlined, MenuOutlined
} from '@ant-design/icons';
import iconConfig from '../../../icons/icon-config.json';
import { renderIcon } from '../../agent/components/AgentIconSystem';

interface MenuNode {
  key: string;
  title: React.ReactNode;
  menu_id: number;
  menu_name: string;
  route_path: string;
  menu_component: string;
  menu_icon: string;
  show_menu: number;
  parent_id: number;
  redirect_path?: string;
  sort_order?: number;
  children?: MenuNode[];
}

interface RawMenuData {
  menu_id: number;
  menu_name: string;
  route_path: string;
  menu_component: string;
  menu_icon: string;
  show_menu: number;
  parent_id: number;
  redirect_path?: string;
  sort_order?: number;
  children?: RawMenuData[];
}

// 图标选择器组件
const IconSelector: React.FC<{
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
}> = ({ value, onChange, placeholder }) => {
  const iconOptions = Object.keys(iconConfig.icons).map(iconKey => ({
    value: iconKey,
    label: (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <IconDisplay iconKey={iconKey} size={16} />
        <span style={{ fontSize: 14 }}>{iconKey.split(':')[1]}</span>
        <span style={{ color: '#666', fontSize: 12 }}>
          {iconConfig.icons[iconKey as keyof typeof iconConfig.icons].label}
        </span>
      </div>
    )
  }));

  // 按分类分组选项
  const groupedOptions = iconConfig.categories ? Object.keys(iconConfig.categories).map(category => ({
    label: iconConfig.categories[category as keyof typeof iconConfig.categories].label,
    options: iconOptions.filter(option => 
      iconConfig.icons[option.value as keyof typeof iconConfig.icons].category === category
    )
  })) : iconOptions;

  return (
    <Select
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      showSearch
      optionFilterProp="children"
      filterOption={(input, option) => {
        const iconKey = option?.value as string;
        const iconData = iconConfig.icons[iconKey as keyof typeof iconConfig.icons];
        return iconKey?.toLowerCase().includes(input.toLowerCase()) ||
               iconData?.label?.toLowerCase().includes(input.toLowerCase());
      }}
      options={groupedOptions}
    />
  );
};

// 图标显示组件
const IconDisplay: React.FC<{ iconKey: string; size?: number }> = ({ iconKey, size = 16 }) => {
  // 检查是否是新格式的图标键（lucide:xxx）
  if (iconKey && iconKey.includes(':')) {
    const [provider, iconName] = iconKey.split(':');
    if (provider === 'lucide') {
      // 转换短横线命名为帕斯卡命名 (kebab-case to PascalCase)
      const pascalCaseName = iconName
        .split('-')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join('');
      
      try {
        // 使用 AgentIconSystem 渲染图标
        return <div style={{ display: 'inline-flex', alignItems: 'center' }}>
          {renderIcon(pascalCaseName, size)}
        </div>;
      } catch (error) {
        console.warn(`Icon not found: ${pascalCaseName}`);
      }
    }
  }
  
  // 兼容旧格式或显示默认图标
  return <MenuOutlined style={{ fontSize: size, color: '#999' }} />;
};

export function MenuManagement() {
  const [form] = Form.useForm();
  const [treeData, setTreeData] = useState<MenuNode[]>([]);
  const [selectedMenu, setSelectedMenu] = useState<MenuNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [parentMenuId, setParentMenuId] = useState<number>(-1);
  const [expandedKeys, setExpandedKeys] = useState<React.Key[]>([]);
  const [rawMenuData, setRawMenuData] = useState<RawMenuData[]>([]);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [menuToDelete, setMenuToDelete] = useState<RawMenuData | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [contextMenuVisible, setContextMenuVisible] = useState(false);
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 });
  const [contextMenuData, setContextMenuData] = useState<RawMenuData | null>(null);
  const [treeSelectedKeys, setTreeSelectedKeys] = useState<React.Key[]>([]);

  // 获取所有节点的key用于默认展开
  const getAllNodeKeys = (nodes: MenuNode[]): React.Key[] => {
    const keys: React.Key[] = [];
    const traverse = (nodeList: MenuNode[]) => {
      nodeList.forEach(node => {
        keys.push(node.key);
        if (node.children && node.children.length > 0) {
          traverse(node.children);
        }
      });
    };
    traverse(nodes);
    return keys;
  };

  // 构建树形数据
  const buildTreeData = (menus: RawMenuData[]): MenuNode[] => {
    const buildNode = (menu: RawMenuData, allMenus: RawMenuData[]): MenuNode => {
      return {
        key: menu.menu_id.toString(),
        title: (
          <div 
            style={{ 
              display: 'flex', 
              alignItems: 'center',
              width: '100%',
              userSelect: 'none'
            }}
            onContextMenu={(e) => handleContextMenu(e, menu)}
          >
            <span style={{ display: 'flex', alignItems: 'center' }}>
              <span style={{ marginRight: 8 }}>
                <IconDisplay iconKey={menu.menu_icon} size={16} />
              </span>
              <span>{menu.menu_name}</span>
              {menu.show_menu === 0 && (
                <EyeInvisibleOutlined style={{ marginLeft: 8, color: '#999' }} />
              )}
            </span>
          </div>
        ),
        menu_id: menu.menu_id,
        menu_name: menu.menu_name,
        route_path: menu.route_path,
        menu_component: menu.menu_component,
        menu_icon: menu.menu_icon,
        show_menu: menu.show_menu,
        parent_id: menu.parent_id,
        redirect_path: menu.redirect_path,
        sort_order: menu.sort_order,
        children: menu.children ? menu.children.map(child => buildNode(child, menus)) : []
      };
    };

    return menus.map(menu => buildNode(menu, menus));
  };


  // 计算菜单层级深度（递归计算从根节点到目标节点的深度）
  const getMenuDepth = (menuId: number): number => {
    const calculateDepth = (menuList: RawMenuData[], targetId: number, currentDepth: number): number => {
      for (const menu of menuList) {
        if (menu.menu_id === targetId) {
          return currentDepth;
        }
        if (menu.children && menu.children.length > 0) {
          const childDepth = calculateDepth(menu.children, targetId, currentDepth + 1);
          if (childDepth > 0) {
            return childDepth;
          }
        }
      }
      return 0; // 未找到
    };

    return calculateDepth(rawMenuData, menuId, 1);
  };

  // 使用指定菜单数据计算层级深度
  const getMenuDepthWithData = (menuId: number, menuData: RawMenuData[]): number => {
    const calculateDepth = (menuList: RawMenuData[], targetId: number, currentDepth: number): number => {
      for (const menu of menuList) {
        if (menu.menu_id === targetId) {
          return currentDepth;
        }
        if (menu.children && menu.children.length > 0) {
          const childDepth = calculateDepth(menu.children, targetId, currentDepth + 1);
          if (childDepth > 0) {
            return childDepth;
          }
        }
      }
      return 0; // 未找到
    };

    return calculateDepth(menuData, menuId, 1);
  };


  // 加载菜单树
  const loadMenuTree = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/auth/admin/menus');
      const data = await response.json();
      console.log('Menu data:', data);
      setRawMenuData(data.menus || []);
      const treeData = buildTreeData(data.menus || []);
      setTreeData(treeData);
      // 设置默认全部展开
      const allKeys = getAllNodeKeys(treeData);
      setExpandedKeys(allKeys);
    } catch (error) {
      console.error('Load menu error:', error);
      message.error('加载菜单失败');
    } finally {
      setLoading(false);
    }
  };

  // 处理右键菜单
  const handleContextMenu = (e: React.MouseEvent, menu: RawMenuData) => {
    e.preventDefault();
    e.stopPropagation();
    
    setContextMenuData(menu);
    setContextMenuPosition({ x: e.clientX, y: e.clientY });
    setContextMenuVisible(true);
  };

  // 关闭右键菜单
  const hideContextMenu = () => {
    setContextMenuVisible(false);
    setContextMenuData(null);
  };

  // 生成右键菜单项
  const getContextMenuItems = (menu: RawMenuData) => {
    const currentDepth = getMenuDepthWithData(menu.menu_id, rawMenuData);
    const menuActions = [];

    // 只有层级小于4级才能添加子菜单
    if (currentDepth < 4) {
      menuActions.push({
        key: 'addChild',
        icon: <PlusOutlined />,
        label: '添加子菜单',
        onClick: () => {
          hideContextMenu();
          handleAddChild(menu);
        }
      });
    }

    // 所有菜单都可以编辑
    menuActions.push({
      key: 'edit',
      icon: <EditOutlined />,
      label: '编辑菜单',
      onClick: () => {
        hideContextMenu();
        handleEdit(menu);
      }
    });

    // 删除选项：所有菜单都可以删除（但系统核心菜单会在handleDelete中特殊处理）
    menuActions.push(
      {
        key: 'delete',
        icon: <DeleteOutlined />,
        label: '删除',
        danger: true,
        onClick: () => {
          hideContextMenu();
          handleDelete(menu);
        }
      }
    );

    // 只有非系统核心菜单才显示隐藏/显示选项
    const systemCoreMenus = ['首页', '用户服务', '系统管理'];
    const isSystemCore = menu.parent_id === -1 && systemCoreMenus.includes(menu.menu_name);
    
    if (!isSystemCore) {
      // 在删除选项前插入隐藏/显示选项
      menuActions.splice(-1, 0, 
        {
          key: 'toggle',
          icon: menu.show_menu ? <EyeInvisibleOutlined /> : <EyeOutlined />,
          label: menu.show_menu ? '隐藏' : '显示',
          onClick: () => {
            hideContextMenu();
            handleToggleVisible(menu);
          }
        },
        {
          type: 'divider' as const
        }
      );
    }

    return menuActions;
  };

  // 选中树节点
  const handleSelect = (selectedKeys: React.Key[], info: any) => {
    setTreeSelectedKeys(selectedKeys);
    if (selectedKeys.length > 0) {
      const selectedNode = info.node;
      setSelectedMenu(selectedNode);
      setEditMode(false);
      setParentMenuId(-1);
      
      // 填充表单
      form.setFieldsValue({
        menu_name: selectedNode.menu_name,
        route_path: selectedNode.route_path,
        menu_component: selectedNode.menu_component,
        menu_icon: selectedNode.menu_icon,
        show_menu: selectedNode.show_menu,
        redirect_path: selectedNode.redirect_path || '',
        sort_order: selectedNode.sort_order || 0
      });
    } else {
      setSelectedMenu(null);
      form.resetFields();
    }
  };

  // 添加根菜单
  const handleAddRoot = async () => {
    try {
      // 生成新菜单数据
      const { name, path, component } = generateNewMenuData();
      
      // 创建新的根菜单节点
      const newMenuData = {
        menu_name: name,
        route_path: path,
        menu_component: component,
        menu_icon: 'lucide:folder-open',
        show_menu: 1,
        sort_order: 0,
        parent_id: -1
      };

      const response = await fetch('/api/v1/auth/admin/menus', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newMenuData)
      });

      if (response.ok) {
        const newMenu = await response.json();
        message.success('根菜单创建成功，请选择新节点进行编辑');
        // 重新加载菜单树
        loadMenuTree();
      } else {
        const errorData = await response.json();
        message.error(errorData.msg || '创建根菜单失败');
      }
    } catch (error) {
      console.error('Create root menu error:', error);
      message.error('创建根菜单失败');
    }
  };

  // 获取父菜单的完整路径
  const getParentFullPath = (parentMenu: RawMenuData): string => {
    if (parentMenu.parent_id === -1) {
      // 父菜单是根菜单，直接返回其路径
      return parentMenu.route_path;
    } else {
      // 递归查找父菜单的完整路径
      const findParentInData = (menus: RawMenuData[], targetId: number): RawMenuData | null => {
        for (const menu of menus) {
          if (menu.menu_id === targetId) {
            return menu;
          }
          if (menu.children) {
            const found = findParentInData(menu.children, targetId);
            if (found) return found;
          }
        }
        return null;
      };
      
      const grandParent = findParentInData(rawMenuData, parentMenu.parent_id);
      if (grandParent) {
        return getParentFullPath(grandParent) + parentMenu.route_path.replace(/^\//, '/');
      }
      return parentMenu.route_path;
    }
  };

  // 生成新菜单名称和路径（自动编号 + 路径继承）
  const generateNewMenuData = (parentMenu?: RawMenuData): { name: string, path: string, component: string } => {
    const existingMenus = parentMenu 
      ? parentMenu.children || []
      : rawMenuData.filter(menu => menu.parent_id === -1);
    
    // 查找现有的"新菜单"系列名称
    const newMenuPattern = /^新菜单(\d*)$/;
    const existingNumbers: number[] = [];
    
    const checkMenuNames = (menus: RawMenuData[]) => {
      menus.forEach(menu => {
        const match = menu.menu_name.match(newMenuPattern);
        if (match) {
          const num = match[1] ? parseInt(match[1]) : 1;
          existingNumbers.push(num);
        }
        if (menu.children) {
          checkMenuNames(menu.children);
        }
      });
    };
    
    checkMenuNames(rawMenuData);
    
    // 找到下一个可用的编号
    let nextNumber = 1;
    while (existingNumbers.includes(nextNumber)) {
      nextNumber++;
    }
    
    const menuName = nextNumber === 1 ? '新菜单' : `新菜单${nextNumber}`;
    
    // 生成路径：如果有父菜单，继承父路径
    let routePath: string;
    if (parentMenu) {
      const parentFullPath = getParentFullPath(parentMenu);
      const childPath = nextNumber === 1 ? 'new-menu' : `new-menu-${nextNumber}`;
      routePath = `${parentFullPath}/${childPath}`.replace(/\/+/g, '/');
    } else {
      routePath = nextNumber === 1 ? '/new-menu' : `/new-menu-${nextNumber}`;
    }
    
    // 生成组件名称：统一使用pages/前缀便于定位代码位置
    const componentName = nextNumber === 1 ? 'pages/NewMenuComponent' : `pages/NewMenuComponent${nextNumber}`;
    
    return { name: menuName, path: routePath, component: componentName };
  };

  // 添加子菜单
  const handleAddChild = async (parentMenu: RawMenuData) => {
    // 检查父菜单层级
    const parentDepth = getMenuDepthWithData(parentMenu.menu_id, rawMenuData);

    if (parentDepth >= 4) {
      message.warning('菜单层级最多支持4级，不能继续添加子菜单');
      return;
    }

    try {
      // 生成新菜单数据
      const { name, path, component } = generateNewMenuData(parentMenu);
      
      // 创建新的子菜单节点
      const newMenuData = {
        menu_name: name,
        route_path: path,
        menu_component: component,
        menu_icon: 'lucide:file-text',
        show_menu: 1,
        sort_order: 0,
        parent_id: parentMenu.menu_id
      };

      const response = await fetch('/api/v1/auth/admin/menus', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newMenuData)
      });

      if (response.ok) {
        const newMenu = await response.json();
        message.success('子菜单创建成功，请选择新节点进行编辑');
        // 重新加载菜单树
        loadMenuTree();
      } else {
        const errorData = await response.json();
        message.error(errorData.msg || '创建子菜单失败');
      }
    } catch (error) {
      console.error('Create child menu error:', error);
      message.error('创建子菜单失败');
    }
  };

  // 编辑菜单
  const handleEdit = (menu: RawMenuData) => {
    const menuNode = findMenuById(treeData, menu.menu_id);
    if (menuNode) {
      // 选中树节点
      setTreeSelectedKeys([menu.menu_id.toString()]);
      setSelectedMenu(menuNode);
      setEditMode(true);
      setParentMenuId(-1); // 编辑模式下重置parentMenuId，表示不是新建
      form.setFieldsValue({
        menu_name: menu.menu_name,
        route_path: menu.route_path,
        menu_component: menu.menu_component,
        menu_icon: menu.menu_icon,
        show_menu: menu.show_menu,
        redirect_path: menu.redirect_path || '',
        sort_order: menu.sort_order || 0
      });
    }
  };

  // 查找菜单节点
  const findMenuById = (nodes: MenuNode[], menuId: number): MenuNode | null => {
    for (const node of nodes) {
      if (node.menu_id === menuId) {
        return node;
      }
      if (node.children && node.children.length > 0) {
        const found = findMenuById(node.children, menuId);
        if (found) return found;
      }
    }
    return null;
  };

  // 切换显示/隐藏
  const handleToggleVisible = async (menu: RawMenuData) => {
    // 检查是否是系统核心菜单
    const systemCoreMenus = ['首页', '用户服务', '系统管理'];
    if (menu.parent_id === -1 && systemCoreMenus.includes(menu.menu_name)) {
      message.warning(`系统核心菜单"${menu.menu_name}"不能隐藏`);
      return;
    }
    
    try {
      const response = await fetch(`/api/v1/auth/admin/menus/${menu.menu_id}`, {
        method: 'PUT',
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          show_menu: menu.show_menu === 1 ? 0 : 1
        })
      });

      if (response.ok) {
        message.success('状态更新成功');
        loadMenuTree();
      } else {
        const errorData = await response.json();
        message.error(errorData.msg || '状态更新失败');
      }
    } catch (error) {
      console.error('Toggle visibility error:', error);
      message.error('状态更新失败');
    }
  };

  // 删除菜单
  const handleDelete = (menu: RawMenuData) => {
    console.log('handleDelete被调用，菜单:', menu.menu_name, menu.menu_id);
    
    // 检查是否是系统核心菜单（首页、用户服务、系统管理等核心菜单不能删除）
    const systemCoreMenus = ['首页', '用户服务', '系统管理'];
    if (menu.parent_id === -1 && systemCoreMenus.includes(menu.menu_name)) {
      console.log('系统核心菜单不能删除:', menu.menu_name);
      message.warning(`系统核心菜单"${menu.menu_name}"不能删除`);
      return;
    }

    console.log('准备显示确认对话框...');
    setMenuToDelete(menu);
    setDeleteModalOpen(true);
  };

  // 确认删除
  const confirmDelete = async () => {
    if (!menuToDelete) return;
    
    console.log('确认删除，准备调用API...');
    setDeleteLoading(true);
    
    try {
      const response = await fetch(`/api/v1/auth/admin/menus/${menuToDelete.menu_id}`, {
        method: 'DELETE'
      });

      console.log('删除API响应状态:', response.status);
      if (response.ok) {
        message.success('删除成功');
        loadMenuTree(); // 重新加载菜单
        if (selectedMenu?.menu_id === menuToDelete.menu_id) {
          setSelectedMenu(null);
          form.resetFields();
        }
        console.log('删除成功，关闭Modal');
        setDeleteModalOpen(false);
        setMenuToDelete(null);
      } else {
        const errorData = await response.json();
        console.error('删除API错误:', errorData);
        message.error(errorData.msg || '删除失败');
      }
    } catch (error) {
      console.error('Delete menu error:', error);
      message.error('删除失败');
    } finally {
      setDeleteLoading(false);
    }
  };

  // 取消删除
  const cancelDelete = () => {
    console.log('取消删除');
    setDeleteModalOpen(false);
    setMenuToDelete(null);
  };

  // 保存菜单
  const handleSave = async (values: any) => {
    try {
      const isEdit = parentMenuId === -1 && selectedMenu !== null;
      const url = isEdit 
        ? `/api/v1/auth/admin/menus/${selectedMenu.menu_id}`
        : '/api/v1/auth/admin/menus';
      
      const method = isEdit ? 'PUT' : 'POST';

      // 如果是新增菜单，添加父菜单ID
      const payload = isEdit ? values : { ...values, parent_id: parentMenuId };

      const response = await fetch(url, {
        method,
        headers: { 
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (response.ok) {
        message.success(isEdit ? '更新成功' : '创建成功');
        setEditMode(false);
        setParentMenuId(-1);
        loadMenuTree();
      } else {
        const errorData = await response.json();
        message.error(errorData.msg || '保存失败');
      }
    } catch (error) {
      console.error('Save menu error:', error);
      message.error('保存失败');
    }
  };

  // 取消编辑
  const handleCancel = () => {
    setEditMode(false);
    setParentMenuId(-1);
    if (selectedMenu) {
      form.setFieldsValue({
        menu_name: selectedMenu.menu_name,
        route_path: selectedMenu.route_path,
        menu_component: selectedMenu.menu_component,
        menu_icon: selectedMenu.menu_icon,
        show_menu: selectedMenu.show_menu,
        redirect_path: selectedMenu.redirect_path || '',
        sort_order: selectedMenu.sort_order || 0
      });
    } else {
      form.resetFields();
      setSelectedMenu(null);
    }
  };

  // 当rawMenuData变化时重新构建树数据
  useEffect(() => {
    if (rawMenuData.length > 0) {
      const newTreeData = buildTreeData(rawMenuData);
      setTreeData(newTreeData);
      
      // 只有在不是编辑模式时才保持展开状态
      if (!editMode) {
        const allKeys = getAllNodeKeys(newTreeData);
        setExpandedKeys(allKeys);
      }
    }
  }, [rawMenuData, editMode]);

  // 点击其他地方时关闭右键菜单
  useEffect(() => {
    const handleClickOutside = () => {
      if (contextMenuVisible) {
        hideContextMenu();
      }
    };

    document.addEventListener('click', handleClickOutside);
    document.addEventListener('contextmenu', handleClickOutside);
    
    return () => {
      document.removeEventListener('click', handleClickOutside);
      document.removeEventListener('contextmenu', handleClickOutside);
    };
  }, [contextMenuVisible]);

  useEffect(() => {
    loadMenuTree();
  }, []);

  return (
    <div style={{ 
      display: 'flex', 
      height: 'calc(100vh - 200px)', 
      gap: 16,
      padding: '0 0'
    }}>
      {/* 左侧：菜单树 */}
      <Card 
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <HomeOutlined style={{ marginRight: 8 }} />
            菜单树
          </div>
        }
        style={{ width: '45%', overflow: 'hidden' }}
        styles={{ body: { height: 'calc(100% - 56px)', overflow: 'auto' } }}
      >
        <Spin spinning={loading}>
          {treeData.length > 0 ? (
            <Tree
              treeData={treeData}
              onSelect={handleSelect}
              onExpand={setExpandedKeys}
              expandedKeys={expandedKeys}
              showLine={{ showLeafIcon: false }}
              showIcon={false}
              height={500}
              selectedKeys={treeSelectedKeys}
            />
          ) : (
            <div style={{ 
              textAlign: 'center', 
              color: '#999', 
              padding: '60px 0' 
            }}>
              暂无菜单数据，点击"新增菜单"开始创建
            </div>
          )}
        </Spin>
      </Card>

      {/* 右侧：菜单详情/编辑 */}
      <Card 
        title={
          editMode 
            ? (parentMenuId !== -1 || !selectedMenu ? '新增菜单' : '编辑菜单') 
            : '菜单详情'
        }
        style={{ flex: 1, overflow: 'hidden' }}
        extra={
          !editMode && selectedMenu && (
            <Button 
              type="primary" 
              icon={<EditOutlined />}
              onClick={() => handleEdit({
                menu_id: selectedMenu.menu_id,
                menu_name: selectedMenu.menu_name,
                route_path: selectedMenu.route_path,
                menu_component: selectedMenu.menu_component,
                menu_icon: selectedMenu.menu_icon,
                show_menu: selectedMenu.show_menu,
                parent_id: selectedMenu.parent_id,
                redirect_path: selectedMenu.redirect_path,
                sort_order: selectedMenu.sort_order
              })}
              size="small"
            >
              编辑
            </Button>
          )
        }
        styles={{ body: { height: 'calc(100% - 56px)', overflow: 'auto' } }}
      >
        {selectedMenu || editMode ? (
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
            disabled={!editMode}
          >
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 1fr', 
              gap: 16,
              marginBottom: 24
            }}>
              <Form.Item 
                label="菜单名称" 
                name="menu_name"
                rules={[{ required: true, message: '请输入菜单名称' }]}
              >
                <Input placeholder="请输入菜单名称" />
              </Form.Item>

              <Form.Item label="菜单图标" name="menu_icon">
                <IconSelector placeholder="请选择菜单图标" />
              </Form.Item>

              <Form.Item 
                label="路由路径" 
                name="route_path"
                rules={[{ required: true, message: '请输入路由路径' }]}
                extra={selectedMenu && selectedMenu.parent_id !== -1 ? 
                  `提示：子菜单路径会自动继承父级路径` : 
                  "根菜单路径格式：/dashboard"
                }
              >
                <Input placeholder={selectedMenu && selectedMenu.parent_id !== -1 ? 
                  "子路径将自动继承父级路径前缀" : 
                  "请输入路由路径，如：/dashboard"
                } />
              </Form.Item>

              <Form.Item label="重定向路径" name="redirect_path">
                <Input placeholder="请输入重定向路径（可选）" />
              </Form.Item>

              <Form.Item 
                label="组件名称" 
                name="menu_component"
                rules={[{ required: true, message: '请输入组件名称' }]}
                extra="组件路径格式：pages/模块名/组件名，便于定位代码位置"
              >
                <Input placeholder="请输入组件名称，如：pages/agent/AgentMarketplace" />
              </Form.Item>

              <Form.Item label="显示状态" name="show_menu">
                <Select placeholder="选择显示状态">
                  <Select.Option value={1}>显示</Select.Option>
                  <Select.Option value={0}>隐藏</Select.Option>
                </Select>
              </Form.Item>

              <Form.Item label="排序" name="sort_order">
                <Input 
                  type="number" 
                  placeholder="排序值（数字越小越靠前）" 
                  min={0}
                />
              </Form.Item>
            </div>

            {/* 当前菜单信息展示 */}
            {editMode && (
              <div style={{ 
                background: '#f5f5f5', 
                padding: 12, 
                borderRadius: 6, 
                marginBottom: 24,
                fontSize: '12px',
                color: '#666'
              }}>
                <div>
                  {parentMenuId !== -1 
                    ? `正在为"${selectedMenu?.menu_name}"创建子菜单` 
                    : selectedMenu 
                      ? `正在编辑菜单: ${selectedMenu.menu_name}` 
                      : '正在创建新菜单'
                  }
                </div>
              </div>
            )}

            {editMode && (
              <div style={{ textAlign: 'right' }}>
                <Space>
                  <Button onClick={handleCancel}>
                    取消
                  </Button>
                  <Button type="primary" htmlType="submit">
                    保存
                  </Button>
                </Space>
              </div>
            )}
          </Form>
        ) : (
          <div style={{ 
            textAlign: 'center', 
            color: '#999', 
            padding: '60px 0',
            background: '#fafafa',
            borderRadius: 6
          }}>
            <HomeOutlined style={{ fontSize: 48, marginBottom: 16 }} />
            <div>请在左侧选择一个菜单项进行查看或编辑</div>
          </div>
        )}
      </Card>

      {/* 右键上下文菜单 */}
      {contextMenuVisible && contextMenuData && (
        <div
          style={{
            position: 'fixed',
            left: contextMenuPosition.x,
            top: contextMenuPosition.y,
            zIndex: 9999,
            background: '#fff',
            border: '1px solid #d9d9d9',
            borderRadius: 6,
            boxShadow: '0 6px 16px 0 rgba(0, 0, 0, 0.08), 0 3px 6px -4px rgba(0, 0, 0, 0.12), 0 9px 28px 8px rgba(0, 0, 0, 0.05)',
            padding: '4px 0',
            minWidth: 140
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {getContextMenuItems(contextMenuData).map((item, index) => {
            if (item.type === 'divider') {
              return (
                <div
                  key={index}
                  style={{
                    height: 1,
                    background: '#f0f0f0',
                    margin: '4px 0'
                  }}
                />
              );
            }
            
            return (
              <div
                key={item.key}
                style={{
                  padding: '5px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 8,
                  fontSize: 14,
                  color: item.danger ? '#ff4d4f' : '#000',
                  transition: 'background-color 0.2s'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = item.danger ? '#fff2f0' : '#f5f5f5';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                }}
                onClick={item.onClick}
              >
                {item.icon}
                <span>{item.label}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* 删除确认Modal */}
      <Modal
        title="确认删除"
        open={deleteModalOpen}
        onOk={confirmDelete}
        onCancel={cancelDelete}
        okText="确定"
        cancelText="取消"
        confirmLoading={deleteLoading}
        centered
        maskClosable={false}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{ 
            width: 32,
            height: 32,
            borderRadius: '50%',
            background: '#faad14',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            <span style={{ color: '#fff', fontSize: 16, fontWeight: 'bold' }}>!</span>
          </div>
          <div>
            确定要删除菜单"{menuToDelete?.menu_name}"吗？如果有子菜单，需要先删除子菜单。
          </div>
        </div>
      </Modal>
    </div>
  );
}