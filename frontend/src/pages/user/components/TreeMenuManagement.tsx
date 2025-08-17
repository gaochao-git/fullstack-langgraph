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
import { authApi } from '@/services/authApi';
import { omind_get, omind_put, omind_post, omind_del } from '@/utils/base_api';

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

const TreeMenuManagement: React.FC = () => {
  const [form] = Form.useForm();
  const [treeData, setTreeData] = useState<MenuNode[]>([]);
  const [selectedMenu, setSelectedMenu] = useState<MenuNode | null>(null);
  const [loading, setLoading] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [parentMenuId, setParentMenuId] = useState<number>(-1);

  // 构建树形数据
  const buildTreeData = (menus: RawMenuData[]): MenuNode[] => {
    const buildNode = (menu: RawMenuData): MenuNode => ({
      key: menu.menu_id.toString(),
      title: (
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          width: '100%'
        }}>
          <span style={{ display: 'flex', alignItems: 'center' }}>
            {menu.menu_icon ? (
              <span style={{ marginRight: 8, fontSize: '14px' }}>
                {getIconComponent(menu.menu_icon)}
              </span>
            ) : (
              <MenuOutlined style={{ marginRight: 8, color: '#999' }} />
            )}
            <span>{menu.menu_name}</span>
            {menu.show_menu === 0 && (
              <EyeInvisibleOutlined style={{ marginLeft: 8, color: '#999' }} />
            )}
          </span>
          <Dropdown
            overlay={getMenuActions(menu)}
            trigger={['click']}
            placement="bottomRight"
            onClick={(e) => e.stopPropagation()}
          >
            <Button 
              type="text" 
              icon={<MoreOutlined />}
              onClick={(e) => e.stopPropagation()}
            />
          </Dropdown>
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
      children: menu.children ? menu.children.map(buildNode) : []
    });

    return menus.map(buildNode);
  };

  // 简单的图标映射
  const getIconComponent = (iconName: string) => {
    const iconMap: { [key: string]: React.ReactNode } = {
      'dashboard': '📊',
      'users': '👥',
      'settings': '⚙️',
      'file-text': '📄',
      'home': '🏠',
      'system': '💻',
      'menu': '📋',
      'default': '📌'
    };
    return iconMap[iconName] || iconMap['default'];
  };

  // 菜单操作下拉菜单
  const getMenuActions = (menu: RawMenuData) => (
    <AntMenu onClick={(e) => e.domEvent.stopPropagation()}>
      <AntMenu.Item 
        key="addChild" 
        icon={<PlusOutlined />}
        onClick={(e) => {
          e.domEvent.stopPropagation();
          handleAddChild(menu);
        }}
      >
        添加子菜单
      </AntMenu.Item>
      <AntMenu.Item 
        key="edit" 
        icon={<EditOutlined />}
        onClick={(e) => {
          e.domEvent.stopPropagation();
          handleEdit(menu);
        }}
      >
        编辑
      </AntMenu.Item>
      <AntMenu.Item 
        key="toggle" 
        icon={menu.show_menu ? <EyeInvisibleOutlined /> : <EyeOutlined />}
        onClick={(e) => {
          e.domEvent.stopPropagation();
          handleToggleVisible(menu);
        }}
      >
        {menu.show_menu ? '隐藏' : '显示'}
      </AntMenu.Item>
      <AntMenu.Divider />
      <AntMenu.Item 
        key="delete" 
        icon={<DeleteOutlined />}
        danger
        onClick={(e) => {
          e.domEvent.stopPropagation();
          handleDelete(menu);
        }}
      >
        删除
      </AntMenu.Item>
    </AntMenu>
  );

  // 加载菜单树
  const loadMenuTree = async () => {
    try {
      setLoading(true);
      const data = await omind_get('/api/v1/auth/admin/menus');
      console.log('Menu data:', data);
      const treeData = buildTreeData(data.menus || []);
      setTreeData(treeData);
    } catch (error) {
      console.error('Load menu error:', error);
      message.error('加载菜单失败');
    } finally {
      setLoading(false);
    }
  };

  // 选中树节点
  const handleSelect = (selectedKeys: React.Key[], info: any) => {
    if (selectedKeys.length > 0) {
      const selectedNode = info.node;
      setSelectedMenu(selectedNode);
      setEditMode(false);
      
      // 填充表单
      form.setFieldsValue({
        menu_name: selectedNode.menu_name,
        route_path: selectedNode.route_path,
        menu_component: selectedNode.menu_component,
        menu_icon: selectedNode.menu_icon,
        show_menu: selectedNode.show_menu,
        redirect_path: selectedNode.redirect_path || ''
      });
    } else {
      setSelectedMenu(null);
      form.resetFields();
    }
  };

  // 添加根菜单
  const handleAddRoot = () => {
    setSelectedMenu(null);
    setEditMode(true);
    setParentMenuId(-1);
    form.resetFields();
    form.setFieldsValue({ 
      show_menu: 1 
    });
  };

  // 添加子菜单
  const handleAddChild = (parentMenu: RawMenuData) => {
    setSelectedMenu(null);
    setEditMode(true);
    setParentMenuId(parentMenu.menu_id);
    form.resetFields();
    form.setFieldsValue({ 
      show_menu: 1 
    });
  };

  // 编辑菜单
  const handleEdit = (menu: RawMenuData) => {
    const menuNode = findMenuById(treeData, menu.menu_id);
    setSelectedMenu(menuNode);
    setEditMode(true);
    setParentMenuId(menu.parent_id);
    form.setFieldsValue({
      menu_name: menu.menu_name,
      route_path: menu.route_path,
      menu_component: menu.menu_component,
      menu_icon: menu.menu_icon,
      show_menu: menu.show_menu,
      redirect_path: menu.redirect_path || ''
    });
  };

  // 查找菜单节点
  const findMenuById = (nodes: MenuNode[], menuId: number): MenuNode | null => {
    for (const node of nodes) {
      if (node.menu_id === menuId) {
        return node;
      }
      if (node.children) {
        const found = findMenuById(node.children, menuId);
        if (found) return found;
      }
    }
    return null;
  };

  // 切换显示/隐藏
  const handleToggleVisible = async (menu: RawMenuData) => {
    try {
      await omind_put(`/api/v1/auth/admin/menus/${menu.menu_id}`, {
        show_menu: menu.show_menu === 1 ? 0 : 1
      });
      message.success('状态更新成功');
      loadMenuTree();
    } catch (error) {
      console.error('Toggle visibility error:', error);
      message.error('状态更新失败');
    }
  };

  // 删除菜单
  const handleDelete = (menu: RawMenuData) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除菜单"${menu.menu_name}"吗？如果有子菜单，需要先删除子菜单。`,
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          await omind_del(`/api/v1/auth/admin/menus/${menu.menu_id}`);
          message.success('删除成功');
          loadMenuTree();
          if (selectedMenu?.menu_id === menu.menu_id) {
            setSelectedMenu(null);
            form.resetFields();
          }
        } catch (error) {
          console.error('Delete menu error:', error);
          message.error('删除失败');
        }
      }
    });
  };

  // 保存菜单
  const handleSave = async (values: any) => {
    try {
      const isEdit = selectedMenu !== null;
      
      // 如果是新增菜单，添加父菜单ID
      const payload = isEdit ? values : { ...values, parent_id: parentMenuId };

      if (isEdit) {
        await omind_put(`/api/v1/auth/admin/menus/${selectedMenu.menu_id}`, payload);
        message.success('更新成功');
      } else {
        await omind_post('/api/v1/auth/admin/menus', payload);
        message.success('创建成功');
      }
      
      setEditMode(false);
      setParentMenuId(-1);
      loadMenuTree();
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
        redirect_path: selectedMenu.redirect_path || ''
      });
    } else {
      form.resetFields();
      setSelectedMenu(null);
    }
  };

  useEffect(() => {
    loadMenuTree();
  }, []);

  return (
    <div style={{ 
      display: 'flex', 
      height: 'calc(100vh - 120px)', 
      gap: 16,
      padding: '0 24px'
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
        extra={
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={handleAddRoot}
          >
            新增根菜单
          </Button>
        }
        bodyStyle={{ height: 'calc(100% - 56px)', overflow: 'auto' }}
      >
        <Spin spinning={loading}>
          {treeData.length > 0 ? (
            <Tree
              treeData={treeData}
              onSelect={handleSelect}
              showLine={{ showLeafIcon: false }}
              showIcon={false}
              height={500}
              selectedKeys={selectedMenu ? [selectedMenu.key] : []}
            />
          ) : (
            <div style={{ 
              textAlign: 'center', 
              color: '#999', 
              padding: '60px 0' 
            }}>
              暂无菜单数据，点击"新增根菜单"开始创建
            </div>
          )}
        </Spin>
      </Card>

      {/* 右侧：菜单详情/编辑 */}
      <Card 
        title={
          editMode 
            ? (selectedMenu ? '编辑菜单' : '新增菜单') 
            : '菜单详情'
        }
        style={{ flex: 1, overflow: 'hidden' }}
        extra={
          !editMode && selectedMenu && (
            <Button 
              type="primary" 
              icon={<EditOutlined />}
              onClick={() => setEditMode(true)}
            >
              编辑
            </Button>
          )
        }
        bodyStyle={{ height: 'calc(100% - 56px)', overflow: 'auto' }}
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
                <Input placeholder="请输入菜单图标" />
              </Form.Item>

              <Form.Item 
                label="路由路径" 
                name="route_path"
                rules={[{ required: true, message: '请输入路由路径' }]}
              >
                <Input placeholder="请输入路由路径，如：/dashboard" />
              </Form.Item>

              <Form.Item label="重定向路径" name="redirect_path">
                <Input placeholder="请输入重定向路径（可选）" />
              </Form.Item>

              <Form.Item 
                label="组件名称" 
                name="menu_component"
                rules={[{ required: true, message: '请输入组件名称' }]}
              >
                <Input placeholder="请输入组件名称，如：Dashboard" />
              </Form.Item>

              <Form.Item label="显示状态" name="show_menu">
                <Select placeholder="选择显示状态">
                  <Select.Option value={1}>显示</Select.Option>
                  <Select.Option value={0}>隐藏</Select.Option>
                </Select>
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
                  {selectedMenu ? '正在编辑菜单' : '正在创建新菜单'}
                  {parentMenuId !== -1 && ` (父菜单ID: ${parentMenuId})`}
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
    </div>
  );
};

export default TreeMenuManagement;