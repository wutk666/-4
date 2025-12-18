# 命令注入演示功能说明

## 🎯 新增功能

命令注入测试页面现已支持**真实命令执行结果演示**，让你能够直观看到各种命令注入攻击成功后的实际输出效果。

## 📋 支持的命令演示

### 1. 系统信息收集
- **`whoami`** - 显示当前用户：`www-data`
- **`id`** - 显示用户ID和组信息
- **`uname -a`** - 显示完整的系统信息
- **`hostname`** - 显示主机名
- **`pwd`** - 显示当前工作目录

### 2. 文件系统操作
- **`cat /etc/passwd`** - 读取系统密码文件（显示用户列表）
- **`ls`** - 列举当前目录文件
- **`ls -la`** - 详细列举文件（包括隐藏文件和权限）

### 3. 环境和配置
- **`env`** - 显示环境变量（包括敏感信息如API密钥）
- **`ifconfig`** - 显示网络接口配置
- **`netstat -an`** - 显示网络连接状态

### 4. 进程信息
- **`ps aux`** - 显示所有运行中的进程

## 🎮 使用方法

### 防御开启时
1. 访问 http://localhost:5000/test_cmdi
2. 点击任意 payload 示例
3. 点击"执行 Ping"
4. **结果**: ⚠️ 命令注入攻击已被拦截

### 防御关闭时（演示模式）
1. **关闭防御开关**
2. 点击任意 payload 示例（如"读取密码文件"）
3. 点击"执行 Ping"
4. **结果**: 🚨 命令注入成功！显示完整的命令执行输出

## 📊 演示效果示例

### 示例1: 读取密码文件
```
输入: 127.0.0.1; cat /etc/passwd
输出:
PING 127.0.0.1 (127.0.0.1): 56 data bytes
64 bytes from 127.0.0.1: icmp_seq=0 ttl=64 time=0.123 ms

--- 127.0.0.1 ping statistics ---
2 packets transmitted, 2 packets received, 0.0% packet loss

[命令注入执行: cat /etc/passwd]
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
sys:x:3:3:sys:/dev:/usr/sbin/nologin
www-data:x:33:33:www-data:/var/www:/usr/sbin/nologin
mysql:x:111:116:MySQL Server,,,:/nonexistent:/bin/false
admin:x:1000:1000:Admin User:/home/admin:/bin/bash
alice:x:1001:1001:Alice:/home/alice:/bin/bash
```

### 示例2: 环境变量泄露
```
输入: 127.0.0.1; env
输出:
[命令注入执行: env]
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
HOME=/var/www
USER=www-data
SHELL=/bin/bash
DATABASE_URL=sqlite:///database.db
SECRET_KEY=super_secret_key_12345
API_KEY=sk-1234567890abcdef
```

### 示例3: 列举目录文件
```
输入: 127.0.0.1 && ls -la
输出:
[命令注入执行: ls -la]
total 48
drwxr-xr-x  5 www-data www-data 4096 Dec 15 09:00 .
drwxr-xr-x  3 root     root     4096 Nov 20 10:30 ..
-rw-r--r--  1 www-data www-data  220 Nov 20 10:30 .bash_logout
-rw-r--r--  1 www-data www-data 3526 Nov 20 10:30 .bashrc
drwxr-xr-x  3 www-data www-data 4096 Dec 15 09:00 app
-rw-r--r--  1 www-data www-data  807 Nov 20 10:30 .profile
-rw-r--r--  1 www-data www-data 1024 Dec 15 09:00 config.php
-rw-r--r--  1 www-data www-data 2048 Dec 15 09:00 database.db
-rw-r--r--  1 www-data www-data  512 Dec 15 09:00 .env
```

### 示例4: 进程列表
```
输入: 127.0.0.1; ps aux
输出:
[命令注入执行: ps aux]
USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
root         1  0.0  0.1  18508  3256 ?        Ss   09:00   0:00 /sbin/init
www-data   123  0.5  2.1 245678 43210 ?        S    09:01   0:15 python3 app.py
www-data   456  0.1  0.8  98765 16543 ?        S    09:01   0:03 nginx worker
mysql      789  0.3  5.2 876543 98765 ?        Ssl  09:00   0:08 /usr/sbin/mysqld
```

## 🛡️ 安全说明

### 模拟环境
- ✅ 所有命令输出都是**预设的模拟数据**
- ✅ **不会执行真实的系统命令**
- ✅ 完全安全，仅用于教学演示
- ✅ 所有攻击都在隔离的靶场环境中

### 真实攻击的危害
这些演示展示了命令注入攻击成功后可能造成的危害：
- 🔴 **信息泄露**: 读取敏感文件（密码、配置、密钥）
- 🔴 **权限提升**: 获取系统用户信息
- 🔴 **环境侦察**: 了解系统架构和运行环境
- 🔴 **横向移动**: 发现网络拓扑和其他服务

## 🎨 界面特性

### 视觉反馈
- **防御开启**: 绿色提示，攻击被拦截
- **防御关闭 + 正常命令**: 蓝色提示
- **防御关闭 + 注入成功**: 红色警告 + 终端风格输出

### 输出格式
- 使用深色终端风格（黑底白字）
- 清晰标注注入执行的命令
- 保留原始格式和缩进
- 支持滚动查看长输出

## 🚀 测试建议

### 学习路径
1. **先开启防御** - 了解防御系统如何工作
2. **关闭防御** - 观察攻击成功的效果
3. **尝试不同命令** - 理解不同命令的危害
4. **查看攻击日志** - 在控制台查看完整记录

### 推荐测试顺序
1. `whoami` - 最简单的命令
2. `cat /etc/passwd` - 文件读取
3. `env` - 环境变量泄露
4. `ls -la` - 目录遍历
5. `ps aux` - 进程信息
6. `netstat -an` - 网络侦察

## 📈 扩展性

系统支持轻松添加新的命令演示：
- 在 `simulate_command_injection()` 函数中添加新命令
- 定义命令的模拟输出
- 自动匹配和显示

---

**重要提示**: 此功能仅用于安全教育和测试，请勿用于非法用途！
