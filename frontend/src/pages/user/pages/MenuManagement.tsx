import { useState, useEffect } from 'react';
import { 
  Card, Table, Button, Space, Input, Modal, Form, message, 
  Tag, Tooltip, Row, Col, InputNumber, Select, Statistic
} from 'antd';
import { 
  PlusOutlined, EditOutlined, DeleteOutlined, SearchOutlined, 
  MenuOutlined, ReloadOutlined, FolderOutlined, FileOutlined
} from '@ant-design/icons';
import type { ColumnsType } from 'antd/es/table';
import { menuApi } from '../services/rbacApi';
import type { 
  RbacMenu, MenuCreateRequest, MenuUpdateRequest, MenuQueryParams 
} from '../types/rbac';

const { Search } = Input;
const { Option } = Select;

export function MenuManagement() {
  const [loading, setLoading] = useState(false);
  const [menus, setMenus] = useState<RbacMenu[]>([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingMenu, setEditingMenu] = useState<RbacMenu | null>(null);
  const [form] = Form.useForm();
  
  // 分页和搜索状态
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [searchKeyword, setSearchKeyword] = useState('');
  const [filters, setFilters] = useState({
    show_menu: undefined as number | undefined,
    parent_id: undefined as number | undefined,
  });

  const columns: ColumnsType<RbacMenu> = [
    {
      title: '菜单ID',
      dataIndex: 'menu_id',
      key: 'menu_id',
      width: 100,
    },
    {
      title: '菜单名称',
      dataIndex: 'menu_name',
      key: 'menu_name',
      width: 150,
      render: (text: string, record: RbacMenu) => (
        <Space>
          {record.parent_id === -1 ? <FolderOutlined /> : <FileOutlined />}
          {text}
        </Space>
      ),
    },
    {
      title: '菜单图标',
      dataIndex: 'menu_icon',
      key: 'menu_icon',
      width: 100,
      render: (icon: string) => icon || '-',
    },
    {
      title: '父菜单ID',
      dataIndex: 'parent_id',
      key: 'parent_id',
      width: 100,
      render: (parentId: number) => parentId === -1 ? '根菜单' : parentId,
    },
    {
      title: '路由路径',
      dataIndex: 'route_path',
      key: 'route_path',
      width: 200,
      ellipsis: true,
    },
    {
      title: '重定向路径',
      dataIndex: 'redirect_path',
      key: 'redirect_path',
      width: 200,
      ellipsis: true,
    },
    {
      title: '组件',
      dataIndex: 'menu_component',
      key: 'menu_component',
      width: 150,
      ellipsis: true,
    },
    {
      title: '显示状态',
      dataIndex: 'show_menu',
      key: 'show_menu',
      width: 100,
      render: (showMenu: number) => (
        <Tag color={showMenu === 1 ? 'green' : 'red'}>
          {showMenu === 1 ? '显示' : '隐藏'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'create_time',
      key: 'create_time',
      width: 150,
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'action',
      width: 120,
      fixed: 'right',
      render: (_: any, record: RbacMenu) => (
        <Space size="small">
          <Tooltip title="编辑">
            <Button
              type="link"
              size="small"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Tooltip title="删除">
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDelete(record)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 获取菜单列表
  const fetchMenus = async () => {
    try {
      setLoading(true);
      const params: MenuQueryParams = {
        page: pagination.current,
        page_size: pagination.pageSize,
        search: searchKeyword || undefined,
        show_menu: filters.show_menu,
        parent_id: filters.parent_id,
      };
      
      const response = await menuApi.listMenus(params);
      console.log('菜单API响应:', response);
      const items = response.items || [];
      console.log('设置菜单数据:', items.length, '条');
      setMenus(items);
      setPagination(prev => ({
        ...prev,
        total: response.pagination?.total || 0,
      }));
    } catch (error) {
      message.error('获取菜单列表失败');
      console.error('获取菜单列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMenus();
  }, [pagination.current, pagination.pageSize, searchKeyword, filters]);

  const handleAdd = () => {
    setEditingMenu(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (menu: RbacMenu) => {
    setEditingMenu(menu);
    form.setFieldsValue({
      menu_id: menu.menu_id,
      menu_name: menu.menu_name,
      menu_icon: menu.menu_icon,
      parent_id: menu.parent_id,
      route_path: menu.route_path,
      redirect_path: menu.redirect_path,
      menu_component: menu.menu_component,
      show_menu: menu.show_menu,
    });
    setModalVisible(true);
  };

  const handleDelete = (menu: RbacMenu) => {
    Modal.confirm({
      title: '确认删除',
      content: (
        <div>
          <p>确定要删除菜单 <strong>"{menu.menu_name}"</strong> 吗？</p>
          <p className="text-gray-500">删除父菜单将同时删除所有子菜单。</p>
        </div>
      ),
      okText: '确定',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await menuApi.deleteMenu(menu.menu_id);
          if (response.success) {
            message.success('删除成功');
            fetchMenus();
          } else {
            message.error(response.message || '删除失败');
          }
        } catch (error) {
          message.error('删除失败');
          console.error('删除菜单失败:', error);
        }
      },
    });
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      if (editingMenu) {
        // 更新菜单
        const updateData: MenuUpdateRequest = {
          menu_name: values.menu_name,
          menu_icon: values.menu_icon,
          parent_id: values.parent_id,
          route_path: values.route_path,
          redirect_path: values.redirect_path,
          menu_component: values.menu_component,
          show_menu: values.show_menu,
        };
        
        const response = await menuApi.updateMenu(editingMenu.menu_id, updateData);
        if (response.success) {
          message.success('更新成功');
          setModalVisible(false);
          form.resetFields();
          fetchMenus();
        } else {
          message.error(response.message || '更新失败');
        }
      } else {
        // 创建菜单
        const createData: MenuCreateRequest = {
          menu_id: values.menu_id,
          menu_name: values.menu_name,
          menu_icon: values.menu_icon || '',
          parent_id: values.parent_id || -1,
          route_path: values.route_path,
          redirect_path: values.redirect_path,
          menu_component: values.menu_component,
          show_menu: values.show_menu ?? 1,
        };
        
        const response = await menuApi.createMenu(createData);
        if (response.success) {
          message.success('创建成功');
          setModalVisible(false);
          form.resetFields();
          fetchMenus();
        } else {
          message.error(response.message || '创建失败');
        }
      }
    } catch (error) {
      console.error('表单验证失败:', error);
    }
  };

  const handleSearch = (value: string) => {
    setSearchKeyword(value);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleTableChange = (paginationConfig: any) => {
    setPagination({
      current: paginationConfig.current,
      pageSize: paginationConfig.pageSize,
      total: paginationConfig.total,
    });
  };

  // 统计信息
  const totalMenus = pagination.total;
  const visibleCount = menus.filter(m => m.show_menu === 1).length;
  const hiddenCount = menus.filter(m => m.show_menu === 0).length;
  const rootMenuCount = menus.filter(m => m.parent_id === -1).length;

  // 构建菜单树数据
  // const buildMenuTree = (menus: RbacMenu[]): any[] => {
  //   const rootMenus = menus.filter(menu => menu.parent_id === -1);
  //   
  //   const buildNode = (menu: RbacMenu): any => ({
  //     title: menu.menu_name,
  //     key: menu.menu_id,
  //     children: menus
  //       .filter(m => m.parent_id === menu.menu_id)
  //       .map(buildNode),
  //   });
  //   
  //   return rootMenus.map(buildNode);
  // };

  // const menuTreeData = buildMenuTree(menus);

  return (
    <div>
      <Card
        title={
          <Space>
            <MenuOutlined />
            菜单管理
          </Space>
        }
        extra={
          <Space>
            <Search
              placeholder="搜索菜单名称"
              allowClear
              style={{ width: 240 }}
              onSearch={handleSearch}
              prefix={<SearchOutlined />}
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={() => fetchMenus()}
              title="刷新"
            />
            <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
              新增菜单
            </Button>
          </Space>
        }
      >
        {/* 统计信息 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Statistic
              title="总菜单数"
              value={totalMenus}
              prefix={<MenuOutlined />}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="显示菜单"
              value={visibleCount}
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="隐藏菜单"
              value={hiddenCount}
              prefix={<FileOutlined />}
              valueStyle={{ color: '#cf1322' }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="根菜单"
              value={rootMenuCount}
              prefix={<FolderOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Col>
        </Row>

        {/* 筛选器 */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Select
              placeholder="选择显示状态"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => setFilters(prev => ({ ...prev, show_menu: value }))}
            >
              <Option value={1}>显示</Option>
              <Option value={0}>隐藏</Option>
            </Select>
          </Col>
          <Col span={6}>
            <InputNumber
              placeholder="父菜单ID"
              style={{ width: '100%' }}
              onChange={(value: number | null) => setFilters(prev => ({ ...prev, parent_id: value || undefined }))}
            />
          </Col>
        </Row>

        <Table
          columns={columns}
          dataSource={menus}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1400 }}
          pagination={{
            ...pagination,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条记录`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          onChange={handleTableChange}
        />
      </Card>

      <Modal
        title={editingMenu ? '编辑菜单' : '新增菜单'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        okText="确定"
        cancelText="取消"
        width={800}
        destroyOnClose
      >
        <Form form={form} layout="vertical">
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="menu_id"
                label="菜单ID"
                rules={[{ required: true, message: '请输入菜单ID' }]}
              >
                <InputNumber 
                  placeholder="请输入菜单ID" 
                  style={{ width: '100%' }}
                  disabled={!!editingMenu}
                  min={1}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="menu_name"
                label="菜单名称"
                rules={[{ required: true, message: '请输入菜单名称' }]}
              >
                <Input placeholder="请输入菜单名称" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="menu_icon"
                label="菜单图标"
              >
                <Input placeholder="请输入菜单图标" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="parent_id"
                label="父菜单ID"
                initialValue={-1}
              >
                <InputNumber 
                  placeholder="父菜单ID，-1为根菜单" 
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="route_path"
                label="路由路径"
                rules={[{ required: true, message: '请输入路由路径' }]}
              >
                <Input placeholder="请输入路由路径" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="redirect_path"
                label="重定向路径"
                rules={[{ required: true, message: '请输入重定向路径' }]}
              >
                <Input placeholder="请输入重定向路径" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="menu_component"
                label="组件名称"
                rules={[{ required: true, message: '请输入组件名称' }]}
              >
                <Input placeholder="请输入组件名称" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="show_menu"
                label="显示状态"
                initialValue={1}
              >
                <Select>
                  <Option value={1}>显示</Option>
                  <Option value={0}>隐藏</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}