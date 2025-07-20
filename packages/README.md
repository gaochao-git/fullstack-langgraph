# 依赖包安装说明

本目录包含项目所需的依赖包和安装脚本，适用于 CentOS 7/8, RHEL 7/8 系统。

## 📦 包含的软件包

- `openssl-1.1.1w.tar.gz` - OpenSSL 1.1.1w 源码包
- `Python-3.12.11.tgz` - Python 3.12.11 源码包

## 🚀 快速安装

### 1. 安装 OpenSSL（推荐先安装）

```bash
cd packages
chmod +x install_openssl.sh
sudo ./install_openssl.sh
```

**安装位置**: `/usr/local/openssl-1.1.1w`

### 2. 安装 Python

```bash
cd packages  
chmod +x install_python.sh
sudo ./install_python.sh
```

**安装位置**: `/srv/python312`

## 📋 安装顺序说明

1. **建议先安装 OpenSSL**：Python 编译时会使用最新的 OpenSSL 版本
2. **再安装 Python**：会自动检测并使用已安装的 OpenSSL

## 🔧 安装后配置

### 环境变量自动配置

安装脚本会自动配置环境变量，重新登录后生效：

```bash
# 或手动应用环境变量
source /etc/profile.d/openssl.sh
source /etc/profile.d/python312.sh
```

### 验证安装

```bash
# 验证 OpenSSL
/usr/local/openssl-1.1.1w/bin/openssl version

# 验证 Python
/srv/python312/bin/python3.12 --version
/srv/python312/bin/python3.12 -c "import ssl; print(ssl.OPENSSL_VERSION)"
```

## 📍 安装路径

| 软件 | 安装路径 | 可执行文件 | 配置文件 |
|------|----------|------------|----------|
| OpenSSL | `/usr/local/openssl-1.1.1w` | `/usr/local/openssl-1.1.1w/bin/openssl` | `/etc/profile.d/openssl.sh` |
| Python | `/srv/python312` | `/srv/python312/bin/python3.12` | `/etc/profile.d/python312.sh` |

## 💡 使用说明

### 创建虚拟环境

```bash
# 使用安装的 Python 创建虚拟环境
/srv/python312/bin/python3.12 -m venv myproject_env

# 激活虚拟环境
source myproject_env/bin/activate

# 安装项目依赖
pip install -r requirements.txt
```

### 在部署脚本中使用

项目的 `pre_env.sh` 脚本会自动使用 `/srv/python312/bin/python3.12`：

```bash
# 运行项目的环境预配置
./pre_env.sh
```

## 🛠️ 故障排除

### 编译依赖问题

如果编译失败，请确保安装了必要的开发工具：

```bash
# CentOS 7
yum groupinstall -y "Development Tools"
yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel expat-devel libffi-devel

# CentOS 8/RHEL 8  
dnf groupinstall -y "Development Tools"
dnf install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel gdbm-devel libdb-devel libpcap-devel xz-devel expat-devel libffi-devel
```

### SSL 模块问题

如果 Python 编译后 SSL 模块不可用：

1. 确保先安装了 OpenSSL
2. 重新编译 Python
3. 检查环境变量配置

### 权限问题

所有安装脚本需要 root 权限：

```bash
sudo ./install_openssl.sh
sudo ./install_python.sh
```

## 🔄 卸载

### 卸载 Python

```bash
sudo rm -rf /srv/python312
sudo rm -f /etc/ld.so.conf.d/python312.conf
sudo rm -f /etc/profile.d/python312.sh
sudo ldconfig
```

### 卸载 OpenSSL

```bash
sudo rm -rf /usr/local/openssl-1.1.1w
sudo rm -f /etc/ld.so.conf.d/openssl.conf  
sudo rm -f /etc/profile.d/openssl.sh
sudo ldconfig
```

## 📊 系统要求

- **操作系统**: CentOS 7/8, RHEL 7/8
- **磁盘空间**: 至少 2GB 可用空间
- **内存**: 至少 2GB RAM（编译时）
- **权限**: root 用户权限
- **网络**: 如需下载依赖包