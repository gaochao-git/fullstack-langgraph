#!/bin/bash

# Python 3.12.11 编译安装脚本
# 适用于 CentOS 7/8, RHEL 7/8

set -e

PYTHON_VERSION="3.12.11"
PYTHON_PACKAGE="Python-${PYTHON_VERSION}.tgz"
INSTALL_PREFIX="/srv/python312"
OPENSSL_PREFIX="/usr/local/openssl-1.1.1w"

echo "🐍 开始安装 Python ${PYTHON_VERSION}..."

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "❌ 请使用 root 用户运行此脚本"
    exit 1
fi

# 检查安装包是否存在
if [ ! -f "$PYTHON_PACKAGE" ]; then
    echo "❌ 找不到 Python 安装包: $PYTHON_PACKAGE"
    echo "请确保在 packages 目录下运行此脚本"
    exit 1
fi

# 检查OpenSSL是否已安装
if [ ! -d "$OPENSSL_PREFIX" ]; then
    echo "⚠️  未检测到自定义 OpenSSL 安装"
    echo "建议先运行: ./install_openssl.sh"
    echo "继续使用系统默认 OpenSSL..."
    OPENSSL_PREFIX=""
fi

# 安装编译依赖
echo "📦 安装编译依赖..."
if command -v yum >/dev/null 2>&1; then
    yum groupinstall -y "Development Tools"
    yum install -y \
        zlib-devel \
        bzip2-devel \
        openssl-devel \
        ncurses-devel \
        sqlite-devel \
        readline-devel \
        tk-devel \
        gdbm-devel \
        db4-devel \
        libpcap-devel \
        xz-devel \
        expat-devel \
        libffi-devel \
        libuuid-devel
elif command -v dnf >/dev/null 2>&1; then
    dnf groupinstall -y "Development Tools"
    dnf install -y \
        zlib-devel \
        bzip2-devel \
        openssl-devel \
        ncurses-devel \
        sqlite-devel \
        readline-devel \
        tk-devel \
        gdbm-devel \
        libdb-devel \
        libpcap-devel \
        xz-devel \
        expat-devel \
        libffi-devel \
        libuuid-devel
else
    echo "❌ 不支持的包管理器，请手动安装编译工具"
    exit 1
fi

# 备份现有Python安装（如果存在）
if [ -d "$INSTALL_PREFIX" ]; then
    echo "🗂️  备份现有 Python 安装..."
    mv "$INSTALL_PREFIX" "${INSTALL_PREFIX}_backup_$(date +%Y%m%d_%H%M%S)"
fi

# 解压源码
echo "📂 解压源码包..."
tar -xzf "$PYTHON_PACKAGE"
cd "Python-${PYTHON_VERSION}"

# 配置编译选项
echo "⚙️  配置编译选项..."
CONFIGURE_OPTS="--prefix=$INSTALL_PREFIX --enable-optimizations"

# 如果有自定义OpenSSL，使用它
if [ -n "$OPENSSL_PREFIX" ] && [ -d "$OPENSSL_PREFIX" ]; then
    echo "🔐 使用自定义 OpenSSL: $OPENSSL_PREFIX"
    export LDFLAGS="-L${OPENSSL_PREFIX}/lib"
    export CPPFLAGS="-I${OPENSSL_PREFIX}/include"
    export PKG_CONFIG_PATH="${OPENSSL_PREFIX}/lib/pkgconfig:$PKG_CONFIG_PATH"
    CONFIGURE_OPTS="$CONFIGURE_OPTS --with-openssl=$OPENSSL_PREFIX"
fi

./configure $CONFIGURE_OPTS

# 编译
echo "🔨 编译 Python（这可能需要10-20分钟）..."
make -j$(nproc)

# 运行测试（可选，但推荐）
echo "🧪 运行基础测试..."
make test || echo "⚠️  部分测试失败，但可以继续安装"

# 安装
echo "📥 安装 Python..."
make altinstall  # 使用 altinstall 避免覆盖系统Python

# 创建符号链接
echo "🔗 创建符号链接..."
ln -sf "$INSTALL_PREFIX/bin/python3.12" "$INSTALL_PREFIX/bin/python3"
ln -sf "$INSTALL_PREFIX/bin/python3.12" "$INSTALL_PREFIX/bin/python"
ln -sf "$INSTALL_PREFIX/bin/pip3.12" "$INSTALL_PREFIX/bin/pip3"
ln -sf "$INSTALL_PREFIX/bin/pip3.12" "$INSTALL_PREFIX/bin/pip"

# 更新动态链接库配置
echo "🔗 配置动态链接库..."
echo "$INSTALL_PREFIX/lib" > /etc/ld.so.conf.d/python312.conf
ldconfig

# 更新环境变量
echo "🌐 配置环境变量..."
cat > /etc/profile.d/python312.sh << EOF
export PATH="$INSTALL_PREFIX/bin:\$PATH"
export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib:\$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:\$PKG_CONFIG_PATH"
EOF

# 应用环境变量
source /etc/profile.d/python312.sh

# 升级pip
echo "📦 升级 pip..."
"$INSTALL_PREFIX/bin/python3.12" -m pip install --upgrade pip

# 验证安装
echo "✅ 验证安装..."
"$INSTALL_PREFIX/bin/python3.12" --version
"$INSTALL_PREFIX/bin/pip3.12" --version

# 验证SSL模块
echo "🔐 验证 SSL 模块..."
"$INSTALL_PREFIX/bin/python3.12" -c "import ssl; print('SSL模块可用，版本:', ssl.OPENSSL_VERSION)"

# 清理源码目录
cd ..
rm -rf "Python-${PYTHON_VERSION}"

echo ""
echo "🎉 Python ${PYTHON_VERSION} 安装完成！"
echo ""
echo "📍 安装位置: $INSTALL_PREFIX"
echo "🐍 Python 可执行文件: $INSTALL_PREFIX/bin/python3.12"
echo "📦 pip 可执行文件: $INSTALL_PREFIX/bin/pip3.12"
echo ""
echo "💡 使用说明:"
echo "  - 重新登录或执行: source /etc/profile.d/python312.sh"
echo "  - 验证版本: $INSTALL_PREFIX/bin/python3.12 --version"
echo "  - 创建虚拟环境: $INSTALL_PREFIX/bin/python3.12 -m venv myenv"
echo "  - 安装包: $INSTALL_PREFIX/bin/pip3.12 install package_name"