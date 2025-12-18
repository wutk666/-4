# 快速启动指南

## 🚀 立即开始

### 步骤 1: 初始化数据库和靶场数据

```bash
python init_attack_ranges.py
```

这将创建：
- 所有数据库表
- SQL注入靶场的8个测试用户
- 目录遍历靶场的8个测试文件

### 步骤 2: 启动应用

```bash
python run.py
```

应用将在 `http://localhost:5000` 启动

### 步骤 3: 登录系统

- 访问: `http://localhost:5000/login`
- 默认账号: `admin`
- 默认密码: `admin`

## 📍 主要页面

### 攻击测试中心
`http://localhost:5000/attack_hub`

这是所有攻击测试的入口，包含：
- 💉 注入类攻击 (XSS, SQL注入, 命令注入)
- 🚫 访问控制攻击 (目录遍历)
- ⏱️ 行为分析攻击 (开发中)

### 各类攻击靶场

1. **XSS 测试** - `http://localhost:5000/test_xss`
   - 反射型 XSS
   - 存储型 XSS (带隔离靶场)
   - DOM型 XSS

2. **SQL 注入** - `http://localhost:5000/test_sqli`
   - 用户搜索功能
   - 多种注入payload示例
   - 完整数据库沙箱查看

3. **命令注入** - `http://localhost:5000/test_cmdi`
   - Ping 工具模拟
   - 各类命令注入技巧
   - 实时防御检测

4. **目录遍历** - `http://localhost:5000/test_path_traversal`
   - 文件查看功能
   - 路径遍历攻击
   - 编码绕过测试

## 🧪 测试示例

### SQL 注入测试

在 SQL 注入页面输入以下 payload：

```sql
-- 经典注入
admin' OR '1'='1

-- 注释绕过
admin' --

-- UNION 注入
' UNION SELECT username,password,email FROM vulnerable_user --

-- DROP TABLE
'; DROP TABLE vulnerable_user; --
```

### 命令注入测试

在命令注入页面输入：

```bash
# 读取密码文件
127.0.0.1; cat /etc/passwd

# 列举目录
127.0.0.1 && ls -la

# 查看用户
127.0.0.1 | whoami

# 命令替换
127.0.0.1$(uname -a)
```

### 目录遍历测试

在目录遍历页面输入：

```
# 相对路径
../../../etc/passwd

# URL编码
%2e%2e%2f%2e%2e%2fetc%2fpasswd

# 混合编码
..%2f..%2fetc%2fpasswd

# 敏感文件
../../etc/shadow
```

## 🎯 预期结果

### 防御开启时
- ✅ 攻击被检测并拦截
- ✅ 显示攻击类型和描述
- ✅ 记录到攻击日志
- ✅ 显示防御成功提示

### 防御关闭时
- ⚠️ 攻击payload可能执行
- ⚠️ 但在靶场隔离环境中
- ⚠️ 不影响主系统安全

## 📊 查看统计

### 控制台
`http://localhost:5000/console`

- 实时攻击统计
- IP封禁管理
- 防御开关控制
- 攻击趋势图表

### 仪表盘
`http://localhost:5000/dashboard`

- 详细的攻击分析
- 攻击类型分布
- Top攻击IP
- 历史趋势

## 🔧 重置靶场

### SQL注入靶场
在测试页面点击"重置数据库"按钮，或访问：
```
POST http://localhost:5000/attack/sqli/reset
```

### 存储型XSS
在测试页面点击"清空"按钮，或访问：
```
POST http://localhost:5000/xss/stored/clear
```

## 📝 攻击分类体系

### 💉 注入类攻击 (Injection)
- **XSS** - 跨站脚本 (HIGH)
- **SQL注入** - 数据库注入 (CRITICAL)
- **命令注入** - 系统命令执行 (CRITICAL)

### 🚫 访问控制攻击 (Access Control)
- **目录遍历** - 路径遍历 (HIGH)
- **权限提升** - 开发中
- **文件上传** - 开发中

### ⏱️ 行为分析攻击 (Behavioral)
- **暴力破解** - 开发中
- **DoS攻击** - 开发中
- **爬虫检测** - 开发中

## 🛡️ 安全提示

1. ⚠️ 仅用于教育和安全研究
2. ⚠️ 不要在生产环境使用
3. ⚠️ 所有数据都是模拟的
4. ⚠️ 靶场环境已隔离
5. ⚠️ 请遵守法律法规

## 🐛 常见问题

### 数据库错误
```bash
# 删除旧数据库
rm instance/app.db

# 重新初始化
python init_attack_ranges.py
```

### 端口被占用
修改 `run.py` 中的端口号：
```python
app.run(debug=False, host='0.0.0.0', port=5001)
```

### 模块导入错误
```bash
pip install -r requirements.txt
```

## 📚 更多信息

详细文档请查看: `ATTACK_RANGES_README.md`

## 🎓 学习路径

1. 先测试 XSS 攻击，了解基本概念
2. 进阶到 SQL 注入，理解数据库安全
3. 学习命令注入，掌握系统安全
4. 研究目录遍历，理解访问控制
5. 查看攻击日志，分析攻击模式
6. 尝试关闭防御，观察攻击效果
7. 研究检测器代码，理解防御机制

## 🚀 下一步

- 尝试编写自己的攻击payload
- 研究如何绕过现有检测
- 为新攻击类型添加检测器
- 优化检测规则减少误报
- 集成机器学习增强检测

祝你学习愉快！🎉
