#!/bin/bash

# OpenSSL 1.1.1w 编译安装脚本
# 适用于 CentOS 7/8, RHEL 7/8

set -e

OPENSSL_VERSION="1.1.1w"
OPENSSL_PACKAGE="openssl-${OPENSSL_VERSION}.tar.gz"
INSTALL_PREFIX="/usr/local/openssl-${OPENSSL_VERSION}"

echo "🔐 开始安装 OpenSSL ${OPENSSL_VERSION}..."

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 root 用户运行此脚本"
    exit 1
fi

# 检查安装包是否存在
if [ ! -f "$OPENSSL_PACKAGE" ]; then
    echo "❌ 找不到 OpenSSL 安装包: $OPENSSL_PACKAGE"
    echo "请确保在 packages 目录下运行此脚本"
    exit 1
fi

# 安装编译依赖
echo "📦 安装编译依赖..."
if command -v yum >/dev/null 2>&1; then
    yum groupinstall -y "Development Tools"
    yum install -y zlib-devel
elif command -v dnf >/dev/null 2>&1; then
    dnf groupinstall -y "Development Tools"
    dnf install -y zlib-devel
else
    echo "❌ 不支持的包管理器，请手动安装编译工具"
    exit 1
fi

# 备份现有OpenSSL（如果存在）
if [ -d "$INSTALL_PREFIX" ]; then
    echo "🗂️  备份现有 OpenSSL 安装..."
    mv "$INSTALL_PREFIX" "${INSTALL_PREFIX}_backup_$(date +%Y%m%d_%H%M%S)"
fi

# 解压源码
echo "📂 解压源码包..."
tar -xzf "$OPENSSL_PACKAGE"
cd "openssl-${OPENSSL_VERSION}"

# 配置编译选项
echo "⚙️  配置编译选项..."
./config \
    --prefix="$INSTALL_PREFIX" \
    --openssldir="$INSTALL_PREFIX" \
    shared \
    zlib

# 编译
echo "🔨 编译 OpenSSL（这可能需要几分钟）..."
make -j$(nproc)

# 安装
echo "📥 安装 OpenSSL..."
make install

# 更新动态链接库配置
echo "🔗 配置动态链接库..."
echo "$INSTALL_PREFIX/lib" > /etc/ld.so.conf.d/openssl.conf
ldconfig

# 更新环境变量
echo "🌐 配置环境变量..."
cat > /etc/profile.d/openssl.sh << EOF
export PATH="$INSTALL_PREFIX/bin:\$PATH"
export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib:\$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:\$PKG_CONFIG_PATH"
EOF

# 应用环境变量
source /etc/profile.d/openssl.sh

# 验证安装
echo "✅ 验证安装..."
"$INSTALL_PREFIX/bin/openssl" version

# 清理源码目录
cd ..
rm -rf "openssl-${OPENSSL_VERSION}"

echo ""
echo "🎉 OpenSSL ${OPENSSL_VERSION} 安装完成！"
echo ""
echo "📍 安装位置: $INSTALL_PREFIX"
echo "🔧 配置文件: $INSTALL_PREFIX/openssl.cnf"
echo "📚 库文件: $INSTALL_PREFIX/lib"
echo ""
echo "💡 使用说明:"
echo "  - 重新登录或执行: source /etc/profile.d/openssl.sh"
echo "  - 验证版本: $INSTALL_PREFIX/bin/openssl version"
echo "  - 在编译Python时会自动使用此OpenSSL版本"