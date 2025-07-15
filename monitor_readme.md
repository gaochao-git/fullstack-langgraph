# 服务器监控脚本使用说明

## 脚本说明

我为你创建了两个优化的服务器监控脚本：

### 1. `simple_monitor.sh` - 简化版本
专门针对你的需求：采集3次CPU占用最高的进程和3次磁盘IO占用最高的进程。

### 2. `server_monitor.sh` - 完整版本
功能更丰富的监控脚本，包含多种监控模式。

## 优化点

相比你原来的命令，这些脚本有以下优化：

### 性能优化
1. **CPU监控优化**：
   - 使用 `ps aux --sort=-%cpu` 替代 `top -b -n1`
   - `ps` 命令比 `top` 更轻量，执行更快
   - 减少了不必要的输出信息

2. **IO监控优化**：
   - 添加了 `iotop` 可用性检查
   - 提供了 `iostat` 和 `lsof` 作为备选方案
   - 更好的错误处理

### 功能增强
1. **结构化输出**：清晰的分段和时间戳
2. **错误处理**：检查工具是否可用
3. **可配置性**：可以调整采集次数和间隔时间
4. **多种模式**：支持快速监控和连续监控

## 使用方法

### 简化版本
```bash
# 给脚本添加执行权限
chmod +x simple_monitor.sh

# 运行监控
./simple_monitor.sh
```

### 完整版本
```bash
# 给脚本添加执行权限
chmod +x server_monitor.sh

# 默认模式：采集3次CPU和IO
./server_monitor.sh

# 快速监控模式（单次采集）
./server_monitor.sh -q

# 连续监控模式
./server_monitor.sh -c

# 查看帮助
./server_monitor.sh -h
```

## 输出示例

```
=== 服务器监控开始 ===
时间: 2024-01-15 14:30:25

=== CPU使用率监控 (采集3次) ===
第 1 次采集:
----------------------------------------
PID     USER    %CPU    %MEM    COMMAND
1234    user1   25.5    2.1     /usr/bin/python3
5678    user2   15.2    1.8     /usr/bin/nginx
...

=== 磁盘IO使用率监控 (采集3次) ===
第 1 次采集:
----------------------------------------
Total DISK READ:         0.00 B/s | Total DISK WRITE:       156.00 K/s
Actual DISK READ:         0.00 B/s | Actual DISK WRITE:       156.00 K/s
  TID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN     IO>    COMMAND
...
```

## 依赖工具

### 必需工具
- `ps` - 进程信息（系统自带）
- `awk` - 文本处理（系统自带）

### 可选工具
- `iotop` - IO监控（需要安装）
- `iostat` - 系统IO统计（sysstat包）
- `lsof` - 文件句柄信息

## 安装依赖

### Ubuntu/Debian
```bash
# 安装iotop
sudo apt-get install iotop

# 安装sysstat（包含iostat）
sudo apt-get install sysstat
```

### CentOS/RHEL
```bash
# 安装iotop
sudo yum install iotop

# 安装sysstat
sudo yum install sysstat
```

## 自定义配置

你可以修改脚本中的以下参数：

```bash
# 修改采集次数
max_iterations=3

# 修改采集间隔（秒）
sleep 5

# 修改显示进程数量
head -10
```

## 与原命令对比

### 你的原命令
```bash
top -b -n1 | head -12; iotop -b -n1 | head -10
```

### 优化后的脚本
- ✅ 自动采集3次
- ✅ 更好的输出格式
- ✅ 错误处理
- ✅ 性能优化
- ✅ 可配置参数
- ✅ 多种监控模式

这样你就可以更方便地监控服务器性能了！ 