# MySQL安装和配置指南

## 概述

本指南将帮助您在Windows系统上安装和配置MySQL数据库，以支持量化交易平台。

## 安装方法

### 方法一：使用MySQL Installer（推荐）

1. **下载MySQL Installer**
   - 访问：https://dev.mysql.com/downloads/installer/
   - 下载 "MySQL Installer for Windows"

2. **运行安装程序**
   ```bash
   # 以管理员身份运行安装程序
   mysql-installer-community-8.0.xx.x.msi
   ```

3. **选择安装类型**
   - 选择 "Developer Default" 或 "Server only"
   - 点击 "Next"

4. **配置MySQL Server**
   - 端口：3306（默认）
   - Root密码：设置一个强密码（记住这个密码）
   - 添加用户：可以创建额外的用户账户

5. **完成安装**
   - 等待安装完成
   - 启动MySQL服务

### 方法二：使用Docker（快速部署）

1. **安装Docker Desktop**
   - 下载：https://www.docker.com/products/docker-desktop
   - 安装并启动Docker

2. **运行MySQL容器**
   ```bash
   # 拉取MySQL镜像
   docker pull mysql:8.0

   # 运行MySQL容器
   docker run --name mysql-stock -e MYSQL_ROOT_PASSWORD=6116988.niu -e MYSQL_DATABASE=stock_data -p 3306:3306 -d mysql:8.0

   # 检查容器状态
   docker ps
   ```

3. **连接到MySQL容器**
   ```bash
   # 进入容器
   docker exec -it mysql-stock mysql -u root -p

   # 或者从外部连接
   mysql -h localhost -P 3306 -u root -p
   ```

### 方法三：使用XAMPP（包含Apache和PHP）

1. **下载XAMPP**
   - 访问：https://www.apachefriends.org/
   - 下载Windows版本

2. **安装XAMPP**
   - 运行安装程序
   - 选择MySQL组件

3. **启动MySQL**
   - 打开XAMPP Control Panel
   - 点击MySQL的 "Start" 按钮

## 配置MySQL

### 1. 设置环境变量

将MySQL的bin目录添加到系统PATH：

```bash
# 默认安装路径
C:\Program Files\MySQL\MySQL Server 8.0\bin

# 或者XAMPP路径
C:\xampp\mysql\bin
```

### 2. 验证安装

```bash
# 检查MySQL版本
mysql --version

# 连接到MySQL
mysql -u root -p
```

### 3. 创建数据库和用户

```sql
-- 登录MySQL后执行
CREATE DATABASE stock_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 创建应用用户
CREATE USER 'stock_app'@'localhost' IDENTIFIED BY 'app_password';
GRANT ALL PRIVILEGES ON stock_data.* TO 'stock_app'@'localhost';

-- 创建只读用户
CREATE USER 'stock_readonly'@'localhost' IDENTIFIED BY 'readonly_password';
GRANT SELECT ON stock_data.* TO 'stock_readonly'@'localhost';

FLUSH PRIVILEGES;
```

## 常见问题解决

### 1. 连接被拒绝

**问题**：`Access denied for user 'root'@'localhost'`

**解决方案**：
```bash
# 方法1：重置root密码
mysql -u root -p
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';

# 方法2：使用管理员权限
mysql -u root -p --skip-grant-tables
UPDATE mysql.user SET authentication_string=PASSWORD('new_password') WHERE User='root';
FLUSH PRIVILEGES;
```

### 2. 服务无法启动

**问题**：MySQL服务启动失败

**解决方案**：
```bash
# 检查服务状态
services.msc
# 找到MySQL服务，右键选择"启动"

# 或者使用命令行
net start mysql80
```

### 3. 端口被占用

**问题**：端口3306被其他程序占用

**解决方案**：
```bash
# 查看端口占用
netstat -ano | findstr 3306

# 修改MySQL端口
# 编辑my.ini文件，修改port=3307
```

### 4. 字符集问题

**问题**：中文显示乱码

**解决方案**：
```sql
-- 设置字符集
SET NAMES utf8mb4;

-- 修改数据库字符集
ALTER DATABASE stock_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## 数据库初始化

### 1. 使用Python脚本

```bash
# 安装依赖
pip install pymysql

# 运行初始化脚本
python init_database.py --host localhost --port 3306 --user root --password your_password
```

### 2. 手动执行SQL

```bash
# 登录MySQL
mysql -u root -p

# 选择数据库
USE stock_data;

# 执行SQL文件
source database_schema.sql;
```

### 3. 使用MySQL Workbench

1. 下载并安装MySQL Workbench
2. 连接到MySQL服务器
3. 打开SQL文件并执行

## 连接测试

### Python测试脚本

```python
import pymysql

# 测试连接
try:
    connection = pymysql.connect(
        host='localhost',
        port=3306,
        user='root',
        password='your_password',
        database='stock_data',
        charset='utf8mb4'
    )
    print("✅ 数据库连接成功!")
    
    # 测试查询
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()
        print(f"MySQL版本: {version[0]}")
        
    connection.close()
    
except Exception as e:
    print(f"❌ 连接失败: {e}")
```

### 命令行测试

```bash
# 测试连接
mysql -h localhost -P 3306 -u root -p -e "SELECT VERSION();"

# 测试数据库
mysql -h localhost -P 3306 -u root -p stock_data -e "SHOW TABLES;"
```

## 安全配置

### 1. 修改默认密码

```sql
-- 修改root密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'strong_password_123';

-- 修改应用用户密码
ALTER USER 'stock_app'@'localhost' IDENTIFIED BY 'strong_app_password_123';
```

### 2. 限制访问

```sql
-- 只允许本地访问
DELETE FROM mysql.user WHERE Host NOT IN ('localhost', '127.0.0.1');

-- 限制特定IP访问
GRANT ALL PRIVILEGES ON stock_data.* TO 'stock_app'@'192.168.1.100';
```

### 3. 启用SSL

```sql
-- 要求SSL连接
ALTER USER 'stock_app'@'localhost' REQUIRE SSL;
```

## 备份和恢复

### 1. 备份数据库

```bash
# 备份整个数据库
mysqldump -u root -p stock_data > stock_data_backup.sql

# 备份特定表
mysqldump -u root -p stock_data daily_data orders > trading_backup.sql
```

### 2. 恢复数据库

```bash
# 恢复整个数据库
mysql -u root -p stock_data < stock_data_backup.sql

# 恢复特定表
mysql -u root -p stock_data < trading_backup.sql
```

## 性能优化

### 1. 配置文件优化

编辑 `my.ini` 文件：

```ini
[mysqld]
# 缓冲池大小（根据内存调整）
innodb_buffer_pool_size = 1G

# 查询缓存
query_cache_size = 64M
query_cache_type = 1

# 连接数
max_connections = 200

# 慢查询日志
slow_query_log = 1
long_query_time = 2
```

### 2. 定期维护

```sql
-- 优化表
OPTIMIZE TABLE daily_data;
OPTIMIZE TABLE orders;

-- 分析表
ANALYZE TABLE stock_basic;
ANALYZE TABLE daily_data;
```

## 监控工具

### 1. MySQL Workbench

- 图形化界面管理
- 性能监控
- 查询优化

### 2. phpMyAdmin

- Web界面管理
- 数据导入导出
- 用户管理

### 3. 命令行工具

```bash
# 查看状态
mysqladmin -u root -p status

# 查看进程
mysqladmin -u root -p processlist

# 查看变量
mysqladmin -u root -p variables
```

## 故障排除

### 1. 服务无法启动

```bash
# 检查错误日志
tail -f /var/log/mysql/error.log

# 检查配置文件
mysql --help --verbose | grep "Default options"
```

### 2. 连接超时

```sql
-- 增加超时时间
SET GLOBAL wait_timeout = 28800;
SET GLOBAL interactive_timeout = 28800;
```

### 3. 内存不足

```sql
-- 减少缓冲池大小
SET GLOBAL innodb_buffer_pool_size = 512M;
```

## 总结

完成以上步骤后，您应该能够：

1. ✅ 成功安装MySQL数据库
2. ✅ 创建量化交易平台所需的数据库和表
3. ✅ 配置适当的用户权限
4. ✅ 测试数据库连接
5. ✅ 开始使用数据库进行开发

如果遇到问题，请检查：
- MySQL服务是否正在运行
- 端口是否被占用
- 用户名和密码是否正确
- 防火墙设置
- 网络连接

更多帮助请参考MySQL官方文档：https://dev.mysql.com/doc/ 