# MySQL数据库初始化指南

## 概述

本指南将帮助您完成量化交易平台MySQL数据库的初始化设置。数据库包含完整的表结构，支持股票数据管理、订单管理、风控合规、策略回测等功能。

## 数据库结构

### 主要表分类

#### 1. 股票数据表
- `stock_basic` - 股票基础信息
- `daily_data` - 日线行情数据
- `adj_factor` - 复权因子
- `minute_data` - 分钟级行情数据

#### 2. 财务数据表
- `fina_indicator` - 财务指标
- `daily_basic` - 每日指标（PE、PB等）

#### 3. 交易管理表
- `orders` - 订单表
- `backtest_results` - 回测结果
- `backtest_trades` - 回测交易记录

#### 4. 风控合规表
- `risk_config` - 风控配置
- `stock_blacklist` - 股票黑名单
- `risk_logs` - 风控日志
- `compliance_rules` - 合规规则
- `compliance_logs` - 合规日志

#### 5. 审计日志表
- `audit_logs` - 审计日志

#### 6. 策略管理表
- `strategy_config` - 策略配置
- `strategy_signals` - 策略信号

#### 7. 统计分析表
- `statistics` - 统计结果
- `ml_results` - 机器学习结果

#### 8. 系统配置表
- `system_config` - 系统配置

## 快速开始

### 1. 环境准备

确保您的系统已安装：
- MySQL 5.7+ 或 MySQL 8.0+
- Python 3.7+
- PyMySQL

```bash
# 安装Python依赖
pip install pymysql
```

### 2. 数据库初始化

#### 方法一：使用Python脚本（推荐）

```bash
# 使用默认配置
python init_database.py

# 使用自定义配置
python init_database.py --host localhost --port 3306 --user root --password your_password

# 指定SQL文件
python init_database.py --sql-file database_schema.sql
```

#### 方法二：手动执行SQL

```bash
# 登录MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE stock_data CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 执行SQL文件
mysql -u root -p stock_data < database_schema.sql
```

### 3. 验证安装

初始化完成后，您应该看到类似以下的输出：

```
🚀 开始初始化MySQL数据库...
============================================================
✅ 成功连接到MySQL服务器 localhost:3306
✅ 数据库 stock_data 创建成功
✅ 切换到数据库 stock_data
✅ 执行SQL语句 1/50: CREATE TABLE IF NOT EXISTS stock_basic...
...
✅ 所有SQL语句执行完成

📊 表创建验证结果:
==================================================
✅ stock_basic
✅ daily_data
✅ adj_factor
...
🎉 所有表创建成功!

📋 初始数据检查:
==================================================
✅ 系统配置: 5 条记录
✅ 风控配置: 4 条记录
✅ 合规规则: 3 条记录
✅ 策略配置: 3 条记录

📝 创建示例数据:
==================================================
✅ 示例股票数据: 5 条记录
✅ 示例日线数据: 4 条记录

🎉 数据库初始化完成!
============================================================
📋 数据库信息:
   主机: localhost:3306
   数据库: stock_data
   用户: root

🔗 连接信息:
   应用连接: mysql+pymysql://root:****@localhost:3306/stock_data
   只读用户: stock_readonly@%
   应用用户: stock_app@%
   管理员: stock_admin@%
```

## 数据库用户

初始化脚本会自动创建以下用户：

### 1. 只读用户
- 用户名：`stock_readonly`
- 密码：`readonly_password`
- 权限：SELECT

### 2. 应用用户
- 用户名：`stock_app`
- 密码：`app_password`
- 权限：SELECT, INSERT, UPDATE, DELETE

### 3. 管理员用户
- 用户名：`stock_admin`
- 密码：`admin_password`
- 权限：ALL PRIVILEGES

## 连接配置

### Python应用连接

```python
import pymysql

# 连接配置
db_config = {
    'host': 'localhost',
    'port': 3306,
    'user': 'stock_app',
    'password': 'app_password',
    'database': 'stock_data',
    'charset': 'utf8mb4'
}

# 建立连接
connection = pymysql.connect(**db_config)
```

### SQLAlchemy连接

```python
from sqlalchemy import create_engine

# 连接字符串
connection_string = (
    f"mysql+pymysql://stock_app:app_password@localhost:3306/stock_data?"
    f"charset=utf8mb4"
)

# 创建引擎
engine = create_engine(connection_string, echo=True)
```

## 常用查询示例

### 1. 查询股票基础信息

```sql
SELECT ts_code, symbol, name, industry, market 
FROM stock_basic 
WHERE industry = '银行';
```

### 2. 查询最新行情数据

```sql
SELECT d.ts_code, s.name, d.close, d.pct_chg, d.trade_date
FROM daily_data d
JOIN stock_basic s ON d.ts_code = s.ts_code
WHERE d.trade_date = (SELECT MAX(trade_date) FROM daily_data);
```

### 3. 查询订单统计

```sql
SELECT 
    DATE(create_time) as order_date,
    side,
    COUNT(*) as order_count,
    SUM(quantity * price) as total_amount
FROM orders
GROUP BY DATE(create_time), side
ORDER BY order_date DESC;
```

### 4. 使用视图查询

```sql
-- 查询股票综合信息
SELECT * FROM v_stock_summary WHERE industry = '白酒';

-- 查询订单统计
SELECT * FROM v_order_summary WHERE order_date = CURDATE();
```

## 数据维护

### 1. 清理历史数据

```sql
-- 使用存储过程清理30天前的数据
CALL CleanHistoricalData(30);
```

### 2. 计算技术指标

```sql
-- 计算指定股票的技术指标
CALL CalculateTechnicalIndicators('000001.SZ', 100);
```

### 3. 备份数据库

```bash
# 备份整个数据库
mysqldump -u root -p stock_data > stock_data_backup.sql

# 备份特定表
mysqldump -u root -p stock_data daily_data orders > trading_data_backup.sql
```

### 4. 恢复数据库

```bash
# 恢复整个数据库
mysql -u root -p stock_data < stock_data_backup.sql

# 恢复特定表
mysql -u root -p stock_data < trading_data_backup.sql
```

## 性能优化

### 1. 索引优化

数据库已包含以下优化索引：
- 复合索引：`(ts_code, trade_date)`
- 时间索引：`trade_date`, `create_time`
- 状态索引：`status`, `is_active`

### 2. 分区建议

对于大量历史数据，建议按时间分区：

```sql
-- 按月分区示例
ALTER TABLE daily_data PARTITION BY RANGE (YEAR(trade_date) * 100 + MONTH(trade_date)) (
    PARTITION p202401 VALUES LESS THAN (202402),
    PARTITION p202402 VALUES LESS THAN (202403),
    PARTITION p202403 VALUES LESS THAN (202404)
);
```

### 3. 配置优化

```sql
-- 设置缓冲池大小（根据服务器内存调整）
SET GLOBAL innodb_buffer_pool_size = 1073741824; -- 1GB

-- 设置查询缓存
SET GLOBAL query_cache_size = 67108864; -- 64MB
SET GLOBAL query_cache_type = 1;
```

## 监控和维护

### 1. 慢查询监控

```sql
-- 启用慢查询日志
SET GLOBAL slow_query_log = 1;
SET GLOBAL long_query_time = 2;

-- 查看慢查询
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;
```

### 2. 表状态监控

```sql
-- 查看表大小
SELECT 
    table_name,
    ROUND(((data_length + index_length) / 1024 / 1024), 2) AS 'Size (MB)'
FROM information_schema.tables 
WHERE table_schema = 'stock_data'
ORDER BY (data_length + index_length) DESC;
```

### 3. 连接数监控

```sql
-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看最大连接数
SHOW VARIABLES LIKE 'max_connections';
```

## 故障排除

### 1. 连接问题

```bash
# 检查MySQL服务状态
systemctl status mysql

# 检查端口监听
netstat -tlnp | grep 3306

# 检查防火墙
firewall-cmd --list-ports
```

### 2. 权限问题

```sql
-- 检查用户权限
SHOW GRANTS FOR 'stock_app'@'%';

-- 重新授权
GRANT SELECT, INSERT, UPDATE, DELETE ON stock_data.* TO 'stock_app'@'%';
FLUSH PRIVILEGES;
```

### 3. 字符集问题

```sql
-- 检查字符集
SHOW VARIABLES LIKE 'character_set%';

-- 修改字符集
SET NAMES utf8mb4;
```

## 安全建议

1. **修改默认密码**：初始化后立即修改所有用户的默认密码
2. **限制访问**：只允许必要的IP地址访问数据库
3. **定期备份**：建立自动备份机制
4. **监控日志**：定期检查审计日志和错误日志
5. **更新补丁**：及时更新MySQL安全补丁

## 技术支持

如果遇到问题，请检查：
1. MySQL版本兼容性
2. 字符集设置
3. 权限配置
4. 网络连接
5. 磁盘空间

更多信息请参考MySQL官方文档。 