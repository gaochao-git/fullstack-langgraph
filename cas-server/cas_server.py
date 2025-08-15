#!/usr/bin/env python3
"""
简单的CAS Mock服务器 - 基于FastAPI (仅用于测试)
"""

from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
import secrets
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Optional
import uvicorn

app = FastAPI(title="CAS Mock Server")

# 存储已验证的票据
tickets = {}

# 模拟用户数据
users = {
    'zhangsan': {
        'password': '123456',
        'display_name': '张三',
        'email': 'zhangsan@taobao.com',
        'group_name': 'CN=张三,OU=开发组,OU=技术部,OU=淘宝,DC=taobao,DC=COM'
    },
    'admin': {
        'password': 'admin123',
        'display_name': '管理员',
        'email': 'admin@taobao.com',
        'group_name': 'CN=管理员,OU=运维组,OU=技术部,OU=淘宝,DC=taobao,DC=COM'
    },
    'lisi': {
        'password': '654321',
        'display_name': '李四',
        'email': 'lisi@taobao.com',
        'group_name': 'CN=李四,OU=测试组,OU=技术部,OU=淘宝,DC=taobao,DC=COM'
    }
}

def get_login_page(service: str = "", error: str = "") -> str:
    """生成登录页面HTML"""
    error_html = f'<div class="error">{error}</div>' if error else ''
    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CAS Mock 登录</title>
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'none'; object-src 'none';">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #f5f5f5; }}
        .login-box {{ background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 20px rgba(0,0,0,0.1); width: 360px; }}
        h2 {{ margin: 0 0 30px 0; color: #333; text-align: center; font-weight: 500; }}
        input {{ width: 100%; padding: 12px; margin: 8px 0; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; box-sizing: border-box; }}
        input:focus {{ outline: none; border-color: #007bff; }}
        button {{ width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: 500; margin-top: 10px; }}
        button:hover {{ background: #0056b3; }}
        .error {{ color: #dc3545; margin: 10px 0; text-align: center; }}
        .info {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px; }}
        .info h4 {{ margin: 0 0 10px 0; color: #333; }}
        .account {{ background: #f8f9fa; padding: 8px 12px; margin: 5px 0; border-radius: 4px; font-family: monospace; }}
    </style>
</head>
<body>
    <div class="login-box">
        <h2>🔐 CAS Mock 登录</h2>
        {error_html}
        <form method="POST" action="/cas/login">
            <input type="text" name="username" placeholder="用户名" required autofocus>
            <input type="password" name="password" placeholder="密码" required>
            <input type="hidden" name="service" value="{service}">
            <button type="submit">登 录</button>
        </form>
        <div class="info">
            <h4>测试账号：</h4>
            <div class="account">zhangsan / 123456</div>
            <div class="account">admin / admin123</div>
            <div class="account">lisi / 654321</div>
        </div>
    </div>
</body>
</html>
'''

@app.get("/cas/login", response_class=HTMLResponse)
async def login_get(service: Optional[str] = Query(None)):
    """CAS登录页面"""
    return get_login_page(service or "")

@app.post("/cas/login")
async def login_post(
    username: str = Form(...),
    password: str = Form(...),
    service: Optional[str] = Form(None)
):
    """处理登录请求"""
    # 验证用户
    if username in users and users[username]['password'] == password:
        # 生成票据
        ticket = f"ST-{secrets.token_urlsafe(32)}"
        tickets[ticket] = {
            'username': username,
            'service': service or '',
            'attributes': users[username]
        }
        
        # 重定向回服务
        if service:
            separator = '&' if '?' in service else '?'
            return RedirectResponse(
                url=f"{service}{separator}ticket={ticket}",
                status_code=302
            )
        else:
            return HTMLResponse("登录成功，但没有指定服务URL")
    else:
        return HTMLResponse(get_login_page(service or "", "用户名或密码错误"))

@app.get("/cas/logout")
async def logout(service: Optional[str] = Query(None)):
    """CAS登出"""
    if service:
        return RedirectResponse(url=service, status_code=302)
    return HTMLResponse("已登出")

@app.get("/cas/p3/serviceValidate")
@app.get("/cas/serviceValidate")
async def validate(
    ticket: str = Query(...),
    service: str = Query(...)
):
    """验证CAS票据"""
    # 验证票据
    if ticket in tickets:
        ticket_data = tickets[ticket]
        # 使用后删除票据
        del tickets[ticket]
        
        # 构建CAS 3.0响应
        root = ET.Element('{http://www.yale.edu/tp/cas}serviceResponse')
        success = ET.SubElement(root, '{http://www.yale.edu/tp/cas}authenticationSuccess')
        
        user = ET.SubElement(success, '{http://www.yale.edu/tp/cas}user')
        user.text = ticket_data['username']
        
        # 添加属性
        attributes = ET.SubElement(success, '{http://www.yale.edu/tp/cas}attributes')
        for key, value in ticket_data['attributes'].items():
            if key != 'password':
                attr = ET.SubElement(attributes, f'{{http://www.yale.edu/tp/cas}}{key}')
                attr.text = str(value)
        
        # 返回XML响应
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        return Response(content=xml_str, media_type="text/xml; charset=UTF-8")
    else:
        # 认证失败
        root = ET.Element('{http://www.yale.edu/tp/cas}serviceResponse')
        failure = ET.SubElement(root, '{http://www.yale.edu/tp/cas}authenticationFailure')
        failure.set('code', 'INVALID_TICKET')
        failure.text = 'Ticket is invalid'
        
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding='unicode')
        return Response(content=xml_str, media_type="text/xml; charset=UTF-8")

@app.get("/")
async def root():
    """根路径重定向到登录页"""
    return RedirectResponse(url="/cas/login", status_code=302)

if __name__ == '__main__':
    print("🚀 CAS Mock服务器启动在 http://localhost:5555")
    print("📝 测试账号：")
    print("   - zhangsan / 123456")
    print("   - admin / admin123")
    print("   - lisi / 654321")
    print("🔗 登录页面: http://localhost:5555/cas/login")
    
    uvicorn.run(app, host='0.0.0.0', port=5555)