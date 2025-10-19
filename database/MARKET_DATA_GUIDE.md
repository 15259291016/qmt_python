# 市场数据存储指南

## 概述

本指南专门为记录市场数据而设计，为未来的量化AI模型准备数据。数据库设计简洁高效，专注于数据存储和查询。

## 设计理念

### 专注数据存储
- **简化设计**: 去除复杂的交易管理功能，专注于数据存储
- **高效存储**: 优化的表结构，支持大量历史数据
- **易于查询**: 为AI模型训练提供便捷的数据访问接口

### 支持迅投数据
- **3秒级别tick数据**: 支持高频数据存储
- **多时间周期**: 分钟级、日线级数据
- **技术指标**: 预计算的技术指标存储
- **数据完整性**: 确保数据的完整性和一致性

## 数据库架构

### 核心表结构

```
market_data/
├── 股票基础信息
│   └── stock_basic (股票基础信息表)
├── 市场数据
│   ├── tick_data (3秒级别tick数据)
│   ├── minute_data (分钟级数据)
│   ├── daily_data (日线数据)
│   └── adj_factor (复权因子)
├── 技术指标
│   └── technical_indicators (技术指标表)
├── 数据管理
│   ├── data_sync_status (数据同步状态)
│   └── system_config (系统配置)
└── 视图和存储过程
    ├── v_stock_summary (股票汇总视图)
    ├── v_data_statistics (数据统计视图)
    └── 数据维护存储过程
```

## 快速开始

### 1. 安装数据库

```bash
# 一键初始化数据库
python database/init_market_data.py --host localhost --user root --password your_password

# 测试连接
python database/init_market_data.py --test-only --host localhost --user root --password your_password
```

### 2. 基本使用

```python
from database.market_data_manager import MarketDataManager

# 创建数据管理器
manager = MarketDataManager(
    host='localhost',
    port=3306,
    user='market_data_app',
    password='app_password',
    database='market_data'
)

# 测试连接
if manager.test_connection():
    print("✅ 数据库连接成功！")
```

## 数据存储示例

### 1. 存储股票基础信息

```python
import pandas as pd

# 准备股票数据
stocks_data = pd.DataFrame({
    'ts_code': ['000001.SZ', '000002.SZ', '600519.SH'],
    'symbol': ['000001', '000002', '600519'],
    'name': ['平安银行', '万科A', '贵州茅台'],
    'area': ['深圳', '深圳', '贵州'],
    'industry': ['银行', '房地产', '食品饮料'],
    'market': ['主板', '主板', '主板'],
    'list_date': ['19910403', '19910129', '20010827']
})

# 插入数据
result = manager.insert_stock_basic(stocks_data)
print(f"插入 {result} 条股票数据")
```

### 2. 存储tick数据

```python
import pandas as pd
from datetime import datetime

# 准备tick数据
tick_data = pd.DataFrame({
    'symbol': ['000001.SZ'] * 100,
    'tick_time': pd.date_range('2025-01-15 09:30:00', periods=100, freq='3S'),
    'last_price': [15.50 + i * 0.01 for i in range(100)],
    'volume': [1000] * 100,
    'amount': [15500 + i * 10 for i in range(100)],
    'bid_price1': [15.49 + i * 0.01 for i in range(100)],
    'bid_volume1': [500] * 100,
    'ask_price1': [15.51 + i * 0.01 for i in range(100)],
    'ask_volume1': [500] * 100
})

# 插入数据
result = manager.insert_tick_data(tick_data)
print(f"插入 {result} 条tick数据")
```

### 3. 存储日线数据

```python
# 准备日线数据
daily_data = pd.DataFrame({
    'symbol': ['000001.SZ', '000002.SZ', '600519.SH'],
    'trade_date': ['2025-01-15', '2025-01-15', '2025-01-15'],
    'open': [15.50, 20.30, 1800.00],
    'high': [15.80, 20.50, 1820.00],
    'low': [15.40, 20.20, 1790.00],
    'close': [15.70, 20.45, 1810.00],
    'volume': [1000000, 2000000, 500000],
    'amount': [15700000, 40900000, 905000000],
    'pct_chg': [1.29, 0.74, 0.56]
})

# 插入数据
result = manager.insert_daily_data(daily_data)
print(f"插入 {result} 条日线数据")
```

### 4. 存储技术指标

```python
# 准备技术指标数据
indicators_data = pd.DataFrame({
    'symbol': ['000001.SZ', '000001.SZ', '000001.SZ'],
    'trade_date': ['2025-01-13', '2025-01-14', '2025-01-15'],
    'ma5': [15.45, 15.50, 15.55],
    'ma10': [15.40, 15.42, 15.45],
    'ma20': [15.35, 15.37, 15.40],
    'rsi6': [65.5, 67.2, 68.8],
    'rsi12': [62.3, 63.5, 64.7],
    'rsi24': [58.7, 59.2, 59.8]
})

# 插入数据
result = manager.insert_technical_indicators(indicators_data)
print(f"插入 {result} 条技术指标数据")
```

## 数据查询示例

### 1. 获取股票列表

```python
# 获取所有股票
stocks = manager.get_stock_list()
print(f"股票总数: {len(stocks)}")

# 获取特定市场股票
main_board_stocks = manager.get_stock_list(market='主板')
print(f"主板股票数: {len(main_board_stocks)}")

# 获取特定行业股票
bank_stocks = [s for s in stocks if s['industry'] == '银行']
print(f"银行股票数: {len(bank_stocks)}")
```

### 2. 获取市场数据

```python
# 获取日线数据
daily_data = manager.get_daily_data('000001.SZ', '2025-01-01', '2025-01-15')
print(f"日线数据条数: {len(daily_data)}")
print(daily_data.head())

# 获取分钟数据
minute_data = manager.get_minute_data('000001.SZ', '2025-01-15 09:30:00', '2025-01-15 15:00:00')
print(f"分钟数据条数: {len(minute_data)}")

# 获取tick数据
tick_data = manager.get_tick_data('000001.SZ', '2025-01-15 09:30:00', '2025-01-15 10:00:00')
print(f"tick数据条数: {len(tick_data)}")

# 获取最新价格
latest_price = manager.get_latest_price('000001.SZ')
print(f"平安银行最新价格: {latest_price}")
```

### 3. 获取技术指标

```python
# 获取技术指标
indicators = manager.get_technical_indicators('000001.SZ', '2025-01-01', '2025-01-15')
print(f"技术指标数据条数: {len(indicators)}")
print(indicators[['trade_date', 'ma5', 'ma20', 'rsi6']].head())

# 计算技术指标
manager.calculate_technical_indicators('000001.SZ', days=60)
print("技术指标计算完成")
```

## 数据统计和分析

### 1. 数据统计信息

```python
# 获取数据统计
stats = manager.get_data_statistics()
print("数据统计信息:")
for data_type, info in stats.items():
    print(f"  {data_type}:")
    print(f"    总记录数: {info['total_records']}")
    print(f"    股票数量: {info['unique_symbols']}")
    print(f"    时间范围: {info['earliest_time']} - {info['latest_time']}")
```

### 2. 股票汇总信息

```python
# 获取股票汇总
summary = manager.get_stock_summary()
print(f"股票汇总信息: {len(summary)} 只股票")
print(summary[['symbol', 'name', 'industry', 'latest_price', 'latest_change']].head())
```

### 3. 数据覆盖情况

```python
# 获取数据覆盖情况
coverage = manager.get_data_coverage('000001.SZ')
print("平安银行数据覆盖情况:")
for data_type, info in coverage.items():
    print(f"  {data_type}: {info.get('count', 0)} 条记录")
    if info.get('start_time') and info.get('end_time'):
        print(f"    时间范围: {info['start_time']} - {info['end_time']}")
```

## 数据同步管理

### 1. 更新同步状态

```python
# 更新同步状态
manager.update_sync_status('daily_data', '000001.SZ', 'SUCCESS', 100)
manager.update_sync_status('tick_data', '000001.SZ', 'SUCCESS', 1000)
manager.update_sync_status('minute_data', '000001.SZ', 'FAILED', 0, '网络错误')

# 获取同步状态
sync_status = manager.get_sync_status()
print("同步状态:")
print(sync_status[['data_type', 'symbol', 'sync_status', 'last_sync_time', 'record_count']].head())
```

### 2. 数据清理

```python
# 清理历史数据（保留30天）
deleted_rows = manager.clean_historical_data(days_to_keep=30)
print(f"清理了 {deleted_rows} 条历史数据")
```

## 数据导出

### 1. 导出到CSV

```python
# 导出日线数据
csv_file = manager.export_data_to_csv(
    symbol='000001.SZ',
    data_type='daily',
    start_date='2025-01-01',
    end_date='2025-01-15',
    output_dir='data/export'
)
print(f"数据导出到: {csv_file}")

# 导出tick数据
csv_file = manager.export_data_to_csv(
    symbol='000001.SZ',
    data_type='tick',
    start_date='2025-01-15',
    end_date='2025-01-15',
    output_dir='data/export'
)
print(f"tick数据导出到: {csv_file}")
```

## 为AI模型准备数据

### 1. 特征工程数据

```python
# 获取用于AI模型训练的数据
def get_training_data(symbol, start_date, end_date):
    """获取训练数据"""
    # 获取日线数据
    daily_data = manager.get_daily_data(symbol, start_date, end_date)
    
    # 获取技术指标
    indicators = manager.get_technical_indicators(symbol, start_date, end_date)
    
    # 合并数据
    training_data = daily_data.merge(indicators, on=['symbol', 'trade_date'], how='left')
    
    # 计算特征
    training_data['price_change'] = training_data['close'].pct_change()
    training_data['volume_change'] = training_data['volume'].pct_change()
    training_data['ma5_ma20_diff'] = training_data['ma5'] - training_data['ma20']
    training_data['rsi_signal'] = (training_data['rsi6'] > 70).astype(int) - (training_data['rsi6'] < 30).astype(int)
    
    return training_data

# 获取训练数据
training_data = get_training_data('000001.SZ', '2024-01-01', '2024-12-31')
print(f"训练数据形状: {training_data.shape}")
print(training_data.columns.tolist())
```

### 2. 时间序列数据

```python
# 获取时间序列数据
def get_time_series_data(symbol, start_date, end_date, freq='D'):
    """获取时间序列数据"""
    if freq == 'D':
        data = manager.get_daily_data(symbol, start_date, end_date)
        data['datetime'] = pd.to_datetime(data['trade_date'])
    elif freq == '1min':
        data = manager.get_minute_data(symbol, f"{start_date} 00:00:00", f"{end_date} 23:59:59")
        data['datetime'] = pd.to_datetime(data['datetime'])
    elif freq == '3S':
        data = manager.get_tick_data(symbol, f"{start_date} 00:00:00", f"{end_date} 23:59:59")
        data['datetime'] = pd.to_datetime(data['tick_time'])
    
    # 设置时间索引
    data = data.set_index('datetime').sort_index()
    
    return data

# 获取不同频率的时间序列数据
daily_ts = get_time_series_data('000001.SZ', '2024-01-01', '2024-12-31', 'D')
minute_ts = get_time_series_data('000001.SZ', '2025-01-15', '2025-01-15', '1min')
tick_ts = get_time_series_data('000001.SZ', '2025-01-15', '2025-01-15', '3S')

print(f"日线时间序列: {daily_ts.shape}")
print(f"分钟时间序列: {minute_ts.shape}")
print(f"tick时间序列: {tick_ts.shape}")
```

### 3. 批量数据获取

```python
# 批量获取多只股票数据
def get_multiple_stocks_data(symbols, start_date, end_date):
    """批量获取多只股票数据"""
    all_data = []
    
    for symbol in symbols:
        try:
            # 获取日线数据
            daily_data = manager.get_daily_data(symbol, start_date, end_date)
            
            # 获取技术指标
            indicators = manager.get_technical_indicators(symbol, start_date, end_date)
            
            # 合并数据
            stock_data = daily_data.merge(indicators, on=['symbol', 'trade_date'], how='left')
            all_data.append(stock_data)
            
        except Exception as e:
            print(f"获取 {symbol} 数据失败: {e}")
            continue
    
    # 合并所有数据
    if all_data:
        combined_data = pd.concat(all_data, ignore_index=True)
        return combined_data
    else:
        return pd.DataFrame()

# 批量获取数据
symbols = ['000001.SZ', '000002.SZ', '600519.SH', '600036.SH', '601318.SH']
batch_data = get_multiple_stocks_data(symbols, '2024-01-01', '2024-12-31')
print(f"批量数据形状: {batch_data.shape}")
print(f"包含股票: {batch_data['symbol'].unique()}")
```

## 性能优化建议

### 1. 索引优化

```sql
-- 为常用查询创建索引
CREATE INDEX idx_tick_data_symbol_time ON tick_data(symbol, tick_time);
CREATE INDEX idx_daily_data_symbol_date ON daily_data(symbol, trade_date);
CREATE INDEX idx_minute_data_symbol_datetime ON minute_data(symbol, datetime);
```

### 2. 分区策略

```sql
-- 为tick数据创建分区（需要重新建表）
CREATE TABLE tick_data_partitioned (
    -- 表结构同tick_data
    PRIMARY KEY (id, tick_time)
) ENGINE=InnoDB
PARTITION BY RANGE (TO_DAYS(tick_time)) (
    PARTITION p202501 VALUES LESS THAN (TO_DAYS('2025-02-01')),
    PARTITION p202502 VALUES LESS THAN (TO_DAYS('2025-03-01')),
    -- ... 更多分区
    PARTITION p_future VALUES LESS THAN MAXVALUE
);
```

### 3. 数据清理

```python
# 定期清理历史数据
def cleanup_old_data():
    """清理旧数据"""
    # 清理30天前的tick数据
    manager.clean_historical_data(days_to_keep=30)
    print("历史数据清理完成")

# 设置定时任务
import schedule
import time

schedule.every().day.at("02:00").do(cleanup_old_data)

while True:
    schedule.run_pending()
    time.sleep(60)
```

## 总结

这个市场数据存储方案具有以下特点：

### 优势
1. **专注数据存储**: 简化设计，专注于数据存储和查询
2. **支持迅投数据**: 完整支持迅投的各种数据格式
3. **AI友好**: 为机器学习模型提供便捷的数据访问接口
4. **高性能**: 优化的索引和查询性能
5. **易于维护**: 简单的表结构和清晰的数据管理

### 适用场景
- 市场数据收集和存储
- 量化研究数据准备
- AI模型训练数据源
- 历史数据分析
- 回测数据支持

### 扩展建议
1. **数据压缩**: 对历史数据进行压缩存储
2. **分布式存储**: 支持大数据量的分布式存储
3. **实时流处理**: 集成Kafka等流处理框架
4. **数据湖集成**: 与数据湖技术集成
5. **API接口**: 提供RESTful API接口

这个方案为你的量化AI模型提供了完整、高效的数据存储解决方案！🚀

