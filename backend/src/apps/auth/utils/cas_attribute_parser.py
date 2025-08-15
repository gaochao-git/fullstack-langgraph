"""
CAS 属性解析器
根据配置文件解析 CAS 返回的属性并映射到系统用户字段
"""

import re
import uuid
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path


class CASAttributeParser:
    """CAS 属性解析器"""
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化解析器"""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent.parent / "shared/core/cas_mapping_config.yaml"
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        self.mapping_config = self.config.get('cas_attribute_mapping', {})
    
    def parse_attributes(self, cas_attributes: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 CAS 属性并转换为用户表数据
        
        Args:
            cas_attributes: CAS 返回的原始属性
            
        Returns:
            转换后的用户数据字典
        """
        result = {}
        
        # 1. 处理直接映射
        direct_mapping = self.mapping_config.get('direct_mapping', {})
        for cas_field, db_field in direct_mapping.items():
            if cas_field in cas_attributes:
                result[db_field] = cas_attributes[cas_field]
        
        # 2. 解析 group_name
        if self.mapping_config.get('group_name_parsing', {}).get('enabled'):
            group_name = cas_attributes.get('group_name', '')
            if group_name:
                parsed_data = self._parse_group_name(group_name)
                result.update(parsed_data)
        
        # 3. 生成 user_id
        if 'user_id' not in result:
            result['user_id'] = self._generate_user_id(result)
        
        # 4. 应用默认值
        defaults = self.mapping_config.get('defaults', {})
        for field, default_value in defaults.items():
            if field not in result:
                result[field] = default_value
        
        # 5. 验证和处理字段
        result = self._validate_and_process_fields(result)
        
        return result
    
    def _parse_group_name(self, group_name: str) -> Dict[str, str]:
        """
        解析 LDAP DN 格式的 group_name
        示例: CN=张三,OU=开发组,OU=技术部,OU=淘宝,DC=taobao,DC=COM
        """
        result = {}
        parsing_config = self.mapping_config.get('group_name_parsing', {})
        
        if parsing_config.get('parser_type') == 'ldap_dn':
            # 解析 LDAP DN
            dn_parts = self._parse_ldap_dn(group_name)
            
            # 应用映射规则
            for rule in parsing_config.get('rules', []):
                attr_type = rule.get('type')
                index = rule.get('index', 0)
                target = rule.get('target')
                
                if attr_type in dn_parts and len(dn_parts[attr_type]) > index:
                    result[target] = dn_parts[attr_type][index]
        
        return result
    
    def _parse_ldap_dn(self, dn_string: str) -> Dict[str, List[str]]:
        """
        解析 LDAP DN 字符串
        返回格式: {'CN': ['张三'], 'OU': ['开发组', '技术部', '淘宝'], 'DC': ['taobao', 'COM']}
        """
        dn_parts = {}
        
        # 使用正则表达式解析 DN
        # 匹配模式: 属性=值
        pattern = r'([A-Z]+)=([^,]+)'
        matches = re.findall(pattern, dn_string)
        
        for attr_type, value in matches:
            if attr_type not in dn_parts:
                dn_parts[attr_type] = []
            dn_parts[attr_type].append(value.strip())
        
        return dn_parts
    
    def _generate_user_id(self, user_data: Dict[str, Any]) -> str:
        """生成 user_id"""
        generation_config = self.mapping_config.get('field_generation', {}).get('user_id', {})
        strategy = generation_config.get('strategy', 'prefix_username')
        
        if strategy == 'prefix_username':
            prefix = generation_config.get('prefix', 'cas_')
            username = user_data.get('user_name', '')
            return f"{prefix}{username}" if username else f"{prefix}{uuid.uuid4().hex[:8]}"
        
        elif strategy == 'uuid':
            return f"cas_{uuid.uuid4().hex}"
        
        elif strategy == 'cas_uid':
            # 如果 CAS 提供了唯一 ID
            return user_data.get('cas_uid', f"cas_{uuid.uuid4().hex[:8]}")
        
        else:
            return f"cas_{uuid.uuid4().hex[:8]}"
    
    def _validate_and_process_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """验证和处理字段"""
        validation_config = self.mapping_config.get('validation', {})
        
        for field, rules in validation_config.items():
            if field in data:
                value = data[field]
                
                # 检查必填
                if rules.get('required') and not value:
                    raise ValueError(f"字段 {field} 不能为空")
                
                # 检查长度
                max_length = rules.get('max_length')
                if max_length and isinstance(value, str) and len(value) > max_length:
                    data[field] = value[:max_length]
                
                # 检查格式
                pattern = rules.get('pattern')
                if pattern and isinstance(value, str):
                    if not re.match(pattern, value):
                        raise ValueError(f"字段 {field} 格式不正确")
            
            # 应用默认值
            elif rules.get('default_if_empty'):
                data[field] = rules['default_if_empty']
        
        return data


# 使用示例
if __name__ == "__main__":
    # 模拟 CAS 返回的属性
    cas_attrs = {
        "username": "zhangsan",
        "display_name": "张三",
        "email": "zhangsan@taobao.com",
        "group_name": "CN=张三,OU=开发组,OU=技术部,OU=淘宝,DC=taobao,DC=COM"
    }
    
    parser = CASAttributeParser()
    user_data = parser.parse_attributes(cas_attrs)
    
    print("转换后的用户数据:")
    for key, value in user_data.items():
        print(f"  {key}: {value}")