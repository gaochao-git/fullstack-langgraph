#!/usr/bin/env python3
"""测试使用langextract的敏感数据扫描"""

import requests
import json
import time

# API配置
BASE_URL = "http://localhost:8000/api"
API_KEY = "ak-qy3akU2Z0wPvM-pvXu-WB9yNsvSNofx11EVycDE5YyE"

# 请求头
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def create_test_file():
    """创建测试文件"""
    print("📝 创建包含敏感数据的测试文件...")
    
    # 测试内容，包含各种敏感数据
    test_content = """
这是一个测试文档，包含各种敏感数据。

个人信息：
姓名：张三
身份证号：110101199001011234
手机号：13812345678
邮箱：zhangsan@example.com

公司信息：
统一社会信用代码：91110000000000000X
公司名称：测试科技有限公司

其他信息：
车牌号：京A12345
护照号：G12345678
IP地址：192.168.1.100
银行卡号：6222021234567890123

系统配置：
数据库密码：password123456
API_KEY=sk-1234567890abcdef1234567890abcdef
SECRET_KEY="my_secret_key_123"

这个文档用于测试langextract的敏感数据扫描功能。
"""
    
    # 保存到临时文件
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, 
                                     dir='/tmp/documents', encoding='utf-8') as f:
        f.write(test_content)
        temp_file = f.name
    
    # 获取文件ID（文件名不含扩展名）
    file_id = os.path.basename(temp_file).replace('.txt', '')
    
    print(f"✅ 测试文件创建成功")
    print(f"   文件路径: {temp_file}")
    print(f"   文件ID: {file_id}")
    
    return file_id

def test_langextract_scan():
    """测试langextract扫描"""
    # 创建测试文件
    file_id = create_test_file()
    
    # 创建扫描任务
    print(f"\n🚀 创建扫描任务...")
    
    test_data = {
        "file_ids": [file_id]
    }
    
    response = requests.post(
        f"{BASE_URL}/v1/scan/tasks",
        headers=headers,
        json=test_data
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('status') == 'ok':
            task_id = result['data']['task_id']
            print(f"✅ 任务创建成功: {task_id}")
            
            # 等待任务完成
            print("\n⏳ 等待扫描完成...")
            for i in range(30):  # 最多等待30秒
                time.sleep(1)
                
                # 检查进度
                progress_response = requests.get(
                    f"{BASE_URL}/v1/scan/tasks/{task_id}/progress",
                    headers=headers
                )
                
                if progress_response.status_code == 200:
                    progress_data = progress_response.json()
                    if progress_data.get('status') == 'ok':
                        task_status = progress_data['data']['status']
                        progress_info = progress_data['data'].get('progress', {})
                        
                        print(f"\r状态: {task_status} - {progress_info.get('message', '')}", end='')
                        
                        if task_status == 'completed':
                            print("\n✅ 扫描完成!")
                            
                            # 获取结果
                            result_response = requests.get(
                                f"{BASE_URL}/v1/scan/tasks/{task_id}/result",
                                headers=headers
                            )
                            
                            if result_response.status_code == 200:
                                result_data = result_response.json()
                                if result_data.get('status') == 'ok':
                                    files = result_data['data']['files']
                                    for file in files:
                                        if file['status'] == 'completed':
                                            print(f"\n📄 文件扫描结果:")
                                            print(f"   文件ID: {file['file_id']}")
                                            print(f"   JSONL路径: {file['jsonl_path']}")
                                            print(f"   HTML路径: {file['html_path']}")
                                            
                                            # 获取JSONL内容
                                            print("\n📋 获取JSONL内容...")
                                            jsonl_response = requests.get(
                                                f"{BASE_URL}/v1/scan/results/{task_id}/{file['file_id']}/jsonl",
                                                headers=headers
                                            )
                                            
                                            if jsonl_response.status_code == 200:
                                                print("✅ JSONL内容:")
                                                lines = jsonl_response.text.strip().split('\n')
                                                for line in lines[:3]:  # 显示前3行
                                                    try:
                                                        data = json.loads(line)
                                                        print(f"   {json.dumps(data, ensure_ascii=False, indent=2)}")
                                                    except:
                                                        print(f"   {line}")
                                                if len(lines) > 3:
                                                    print(f"   ... 还有 {len(lines) - 3} 行")
                                            
                                            # 获取HTML内容
                                            print("\n🌐 获取HTML报告...")
                                            html_response = requests.get(
                                                f"{BASE_URL}/v1/scan/results/{task_id}/{file['file_id']}/html",
                                                headers=headers
                                            )
                                            
                                            if html_response.status_code == 200:
                                                print("✅ HTML报告已生成")
                                                print(f"   大小: {len(html_response.text)} 字节")
                                                
                                                # 保存到文件供查看
                                                output_file = f"/tmp/langextract_report_{task_id}.html"
                                                with open(output_file, 'w', encoding='utf-8') as f:
                                                    f.write(html_response.text)
                                                print(f"   已保存到: {output_file}")
                            
                            break
                        elif task_status == 'failed':
                            print("\n❌ 扫描失败!")
                            errors = progress_data['data'].get('errors', [])
                            for error in errors:
                                print(f"   错误: {error}")
                            break
            else:
                print("\n⏱️ 超时：任务未在30秒内完成")
        else:
            print(f"❌ 创建任务失败: {result.get('msg')}")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    print("=" * 60)
    print("测试langextract敏感数据扫描")
    print("=" * 60)
    
    test_langextract_scan()
    
    print("\n✅ 测试完成!")