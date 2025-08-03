#!/usr/bin/env python3
"""
测试RBAC API接口
验证用户、角色、权限、菜单的增删改查功能
"""
import requests
import json
from datetime import datetime

# API基础配置
BASE_URL = "http://localhost:8000/api/v1/rbac"
HEADERS = {"Content-Type": "application/json"}

class RBACAPITester:
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name, success, response_data=None, error=None):
        """记录测试结果"""
        result = {
            'test': test_name,
            'success': success,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'data': response_data,
            'error': str(error) if error else None
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"    错误: {error}")
        elif response_data:
            print(f"    响应: {response_data.get('message', 'OK')}")

    def test_user_apis(self):
        """测试用户管理API"""
        print(f"\n🧪 测试用户管理API")
        print("=" * 50)
        
        # 测试数据
        test_user_data = {
            "user_id": "test_user_001",
            "user_name": "测试用户",
            "display_name": "Test User",
            "department_name": "测试部门",
            "group_name": "测试组",
            "email": "test@example.com",
            "mobile": "13800138000",
            "user_source": 3,
            "is_active": 1,
            "role_ids": [4]  # 普通用户角色
        }
        
        created_user_id = None
        
        try:
            # 1. 创建用户
            response = requests.post(f"{BASE_URL}/users", json=test_user_data, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                created_user_id = result.get('data', {}).get('user_id')
                self.log_test("创建用户", True, result)
            else:
                self.log_test("创建用户", False, error=f"HTTP {response.status_code}: {response.text}")
                return
            
            # 2. 查询用户列表
            response = requests.get(f"{BASE_URL}/users?page=1&page_size=10", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                self.log_test("查询用户列表", True, {"total": result.get('data', {}).get('total', 0)})
            else:
                self.log_test("查询用户列表", False, error=f"HTTP {response.status_code}")
            
            # 3. 获取单个用户
            if created_user_id:
                response = requests.get(f"{BASE_URL}/users/{created_user_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("获取单个用户", True, {"user_name": result.get('data', {}).get('user_name')})
                else:
                    self.log_test("获取单个用户", False, error=f"HTTP {response.status_code}")
            
            # 4. 更新用户
            if created_user_id:
                update_data = {
                    "display_name": "Updated Test User",
                    "department_name": "更新后的部门"
                }
                response = requests.put(f"{BASE_URL}/users/{created_user_id}", json=update_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("更新用户", True, result)
                else:
                    self.log_test("更新用户", False, error=f"HTTP {response.status_code}")
            
            # 5. 删除用户
            if created_user_id:
                response = requests.delete(f"{BASE_URL}/users/{created_user_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("删除用户", True, result)
                else:
                    self.log_test("删除用户", False, error=f"HTTP {response.status_code}")
                    
        except requests.exceptions.ConnectionError:
            self.log_test("用户API连接", False, error="无法连接到服务器，请确保后端服务正在运行")
        except Exception as e:
            self.log_test("用户API测试", False, error=str(e))

    def test_role_apis(self):
        """测试角色管理API"""
        print(f"\n🧪 测试角色管理API")
        print("=" * 50)
        
        # 测试数据
        test_role_data = {
            "role_id": 999,
            "role_name": "测试角色",
            "description": "这是一个测试角色",
            "permission_ids": [5001, 5002]  # 基础权限
        }
        
        created_role_id = None
        
        try:
            # 1. 创建角色
            response = requests.post(f"{BASE_URL}/roles", json=test_role_data, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                created_role_id = result.get('data', {}).get('role_id')
                self.log_test("创建角色", True, result)
            else:
                self.log_test("创建角色", False, error=f"HTTP {response.status_code}: {response.text}")
                return
            
            # 2. 查询角色列表
            response = requests.get(f"{BASE_URL}/roles?page=1&page_size=10", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                self.log_test("查询角色列表", True, {"total": result.get('data', {}).get('total', 0)})
            else:
                self.log_test("查询角色列表", False, error=f"HTTP {response.status_code}")
            
            # 3. 获取单个角色
            if created_role_id:
                response = requests.get(f"{BASE_URL}/roles/{created_role_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("获取单个角色", True, {"role_name": result.get('data', {}).get('role_name')})
                else:
                    self.log_test("获取单个角色", False, error=f"HTTP {response.status_code}")
            
            # 4. 更新角色
            if created_role_id:
                update_data = {
                    "role_name": "更新后的测试角色",
                    "description": "这是更新后的测试角色描述"
                }
                response = requests.put(f"{BASE_URL}/roles/{created_role_id}", json=update_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("更新角色", True, result)
                else:
                    self.log_test("更新角色", False, error=f"HTTP {response.status_code}")
            
            # 5. 删除角色
            if created_role_id:
                response = requests.delete(f"{BASE_URL}/roles/{created_role_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("删除角色", True, result)
                else:
                    self.log_test("删除角色", False, error=f"HTTP {response.status_code}")
                    
        except requests.exceptions.ConnectionError:
            self.log_test("角色API连接", False, error="无法连接到服务器")
        except Exception as e:
            self.log_test("角色API测试", False, error=str(e))

    def test_permission_apis(self):
        """测试权限管理API"""
        print(f"\n🧪 测试权限管理API")
        print("=" * 50)
        
        # 测试数据
        test_permission_data = {
            "permission_id": 9999,
            "permission_name": "测试权限",
            "permission_description": "这是一个测试权限",
            "release_disable": "off",
            "permission_allow_client": "web,mobile"
        }
        
        created_permission_id = None
        
        try:
            # 1. 创建权限
            response = requests.post(f"{BASE_URL}/permissions", json=test_permission_data, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                created_permission_id = result.get('data', {}).get('permission_id')
                self.log_test("创建权限", True, result)
            else:
                self.log_test("创建权限", False, error=f"HTTP {response.status_code}: {response.text}")
                return
            
            # 2. 查询权限列表
            response = requests.get(f"{BASE_URL}/permissions?page=1&page_size=10", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                self.log_test("查询权限列表", True, {"total": result.get('data', {}).get('total', 0)})
            else:
                self.log_test("查询权限列表", False, error=f"HTTP {response.status_code}")
            
            # 3. 获取单个权限
            if created_permission_id:
                response = requests.get(f"{BASE_URL}/permissions/{created_permission_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("获取单个权限", True, {"permission_name": result.get('data', {}).get('permission_name')})
                else:
                    self.log_test("获取单个权限", False, error=f"HTTP {response.status_code}")
            
            # 4. 更新权限
            if created_permission_id:
                update_data = {
                    "permission_name": "更新后的测试权限",
                    "permission_description": "这是更新后的测试权限描述"
                }
                response = requests.put(f"{BASE_URL}/permissions/{created_permission_id}", json=update_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("更新权限", True, result)
                else:
                    self.log_test("更新权限", False, error=f"HTTP {response.status_code}")
            
            # 5. 删除权限
            if created_permission_id:
                response = requests.delete(f"{BASE_URL}/permissions/{created_permission_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("删除权限", True, result)
                else:
                    self.log_test("删除权限", False, error=f"HTTP {response.status_code}")
                    
        except requests.exceptions.ConnectionError:
            self.log_test("权限API连接", False, error="无法连接到服务器")
        except Exception as e:
            self.log_test("权限API测试", False, error=str(e))

    def test_menu_apis(self):
        """测试菜单管理API"""
        print(f"\n🧪 测试菜单管理API")
        print("=" * 50)
        
        # 测试数据
        test_menu_data = {
            "menu_id": 9999,
            "menu_name": "测试菜单",
            "menu_icon": "test-icon",
            "parent_id": -1,
            "route_path": "/test-menu",
            "redirect_path": "/test-menu/index",
            "menu_component": "TestMenu",
            "show_menu": 1
        }
        
        created_menu_id = None
        
        try:
            # 1. 创建菜单
            response = requests.post(f"{BASE_URL}/menus", json=test_menu_data, headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                created_menu_id = result.get('data', {}).get('menu_id')
                self.log_test("创建菜单", True, result)
            else:
                self.log_test("创建菜单", False, error=f"HTTP {response.status_code}: {response.text}")
                return
            
            # 2. 查询菜单列表
            response = requests.get(f"{BASE_URL}/menus?page=1&page_size=10", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                self.log_test("查询菜单列表", True, {"total": result.get('data', {}).get('total', 0)})
            else:
                self.log_test("查询菜单列表", False, error=f"HTTP {response.status_code}")
            
            # 3. 获取单个菜单
            if created_menu_id:
                response = requests.get(f"{BASE_URL}/menus/{created_menu_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("获取单个菜单", True, {"menu_name": result.get('data', {}).get('menu_name')})
                else:
                    self.log_test("获取单个菜单", False, error=f"HTTP {response.status_code}")
            
            # 4. 更新菜单
            if created_menu_id:
                update_data = {
                    "menu_name": "更新后的测试菜单",
                    "route_path": "/updated-test-menu"
                }
                response = requests.put(f"{BASE_URL}/menus/{created_menu_id}", json=update_data, headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("更新菜单", True, result)
                else:
                    self.log_test("更新菜单", False, error=f"HTTP {response.status_code}")
            
            # 5. 删除菜单
            if created_menu_id:
                response = requests.delete(f"{BASE_URL}/menus/{created_menu_id}", headers=HEADERS)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("删除菜单", True, result)
                else:
                    self.log_test("删除菜单", False, error=f"HTTP {response.status_code}")
                    
        except requests.exceptions.ConnectionError:
            self.log_test("菜单API连接", False, error="无法连接到服务器")
        except Exception as e:
            self.log_test("菜单API测试", False, error=str(e))

    def test_existing_data(self):
        """测试查询现有数据"""
        print(f"\n🧪 测试查询现有数据")
        print("=" * 50)
        
        try:
            # 查询现有角色
            response = requests.get(f"{BASE_URL}/roles?page=1&page_size=100", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                roles = result.get('data', {}).get('data', [])
                self.log_test("查询现有角色", True, {"count": len(roles)})
                for role in roles:
                    print(f"    角色: {role.get('role_name')} (ID: {role.get('role_id')})")
            else:
                self.log_test("查询现有角色", False, error=f"HTTP {response.status_code}")
            
            # 查询现有权限
            response = requests.get(f"{BASE_URL}/permissions?page=1&page_size=100", headers=HEADERS)
            if response.status_code == 200:
                result = response.json()
                permissions = result.get('data', {}).get('data', [])
                self.log_test("查询现有权限", True, {"count": len(permissions)})
                print(f"    权限总数: {len(permissions)}")
            else:
                self.log_test("查询现有权限", False, error=f"HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.log_test("数据查询连接", False, error="无法连接到服务器")
        except Exception as e:
            self.log_test("数据查询测试", False, error=str(e))

    def generate_report(self):
        """生成测试报告"""
        print(f"\n📊 测试报告")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['success']])
        failed_tests = total_tests - passed_tests
        
        print(f"测试总数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {failed_tests} ❌")
        print(f"通过率: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['error']}")
        
        print(f"\n💡 测试建议:")
        if failed_tests == 0:
            print("  🎉 所有测试通过！RBAC API功能正常")
        else:
            print("  🔧 请检查后端服务是否正常运行")
            print("  🔧 确认数据库连接和表结构正确")
            print("  🔧 检查API路由配置是否正确")

def main():
    """主函数"""
    print("🚀 RBAC API接口测试工具")
    print("=" * 60)
    print(f"测试目标: {BASE_URL}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = RBACAPITester()
    
    # 执行所有测试
    tester.test_existing_data()   # 先测试查询现有数据
    tester.test_user_apis()       # 测试用户API
    tester.test_role_apis()       # 测试角色API
    tester.test_permission_apis() # 测试权限API
    tester.test_menu_apis()       # 测试菜单API
    
    # 生成测试报告
    tester.generate_report()

if __name__ == "__main__":
    main()