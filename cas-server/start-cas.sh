#!/bin/bash

# 一键启动 CAS Server

echo "🚀 启动 CAS Server..."

# 创建必要的目录
mkdir -p config services

# 启动 CAS
docker-compose up -d

echo "⏳ 等待 CAS 启动..."
sleep 10

echo "✅ CAS Server 启动完成！"
echo ""
echo "📋 访问信息："
echo "  - CAS 登录页面: http://localhost:8080/cas/login"
echo "  - 测试用户:"
echo "    • 用户名: casuser  密码: Mellon"
echo "    • 用户名: admin    密码: admin123"
echo "    • 用户名: zhangsan 密码: 123456"
echo ""
echo "🔧 OMind 系统配置："
echo "  - CAS Server URL: http://localhost:8080/cas"
echo "  - CAS Service URL: http://localhost:3000/api/v1/auth/sso/callback"
echo ""
echo "📝 查看日志: docker logs -f cas-server"