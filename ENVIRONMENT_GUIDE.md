# 环境配置使用指南

## 概述

本量化交易平台支持模拟和实盘两种环境，可以灵活切换以满足不同阶段的开发和交易需求。

## 环境配置

### 1. 环境路径配置

**模拟环境 (SIMULATION):**
- QMT路径: `D:\国金QMT交易端模拟\userdata_mini`
- 账户: `55005056`
- 用途: 策略开发、测试、模拟交易

**实盘环境 (PRODUCTION):**
- QMT路径: `D:\国金证券QMT交易端\userdata_mini`
- 账户: `8881667160`
- 用途: 实际交易、生产环境

### 2. 配置文件位置

环境配置存储在 `config/Config.yaml` 文件中：

```yaml
# 模拟环境配置
SIMULATION:
  QMT_PATH: 'D:\国金QMT交易端模拟\userdata_mini'
  ACCOUNT: '55005056'
  NAME: '模拟环境'

# 实盘环境配置
PRODUCTION:
  QMT_PATH: 'D:\国金证券QMT交易端\userdata_mini'
  ACCOUNT: '8881667160'
  NAME: '实盘环境'
```

## 使用方法

### 1. 命令行运行

**主程序运行:**
```bash
# 模拟环境 (默认)
python main.py
# 或
python main.py --env SIMULATION

# 实盘环境
python main.py --env PRODUCTION
```

**选股策略运行:**
```bash
# 模拟环境
python user_strategy/simple_select_stock.py --env SIMULATION

# 实盘环境
python user_strategy/simple_select_stock.py --env PRODUCTION
```

### 2. 程序内切换

```python
from utils.environment_manager import (
    get_env_manager, 
    switch_to_simulation, 
    switch_to_production
)

# 获取环境管理器
env_manager = get_env_manager()

# 切换到模拟环境
switch_to_simulation()

# 切换到实盘环境
switch_to_production()

# 获取当前环境信息
info = env_manager.get_environment_info()
print(f"当前环境: {info['environment']}")
print(f"QMT路径: {info['qmt_path']}")
print(f"账户: {info['account']}")
```

### 3. 环境验证

```python
# 验证当前环境配置
is_valid = env_manager.validate_current_environment()
if is_valid:
    print("环境配置有效")
else:
    print("环境配置无效，请检查QMT路径")
```

## 环境管理器功能

### 1. 环境切换
- `switch_to_simulation()`: 切换到模拟环境
- `switch_to_production()`: 切换到实盘环境
- `switch_environment(env_name)`: 切换到指定环境

### 2. 环境信息
- `get_environment_info()`: 获取当前环境信息
- `list_available_environments()`: 列出所有可用环境
- `print_environment_info()`: 打印当前环境信息

### 3. 配置获取
- `get_database_config()`: 获取数据库配置
- `get_tushare_token()`: 获取Tushare Token
- `get_qmt_path()`: 获取QMT路径
- `get_account()`: 获取账户信息

### 4. 环境验证
- `validate_current_environment()`: 验证当前环境配置
- `validate_environment(env_name)`: 验证指定环境配置

## 演示脚本

运行环境切换演示：
```bash
python demo_environment_switch.py
```

演示内容包括：
1. 环境切换功能展示
2. 在不同环境中运行选股策略
3. 环境配置验证
4. 与主程序的集成方式

## 注意事项

### 1. 路径检查
- 系统会自动检查QMT路径是否存在
- 如果路径不存在，环境验证会失败
- 请确保QMT软件已正确安装

### 2. 环境隔离
- 模拟和实盘环境完全隔离
- 不同环境使用不同的账户和配置
- 建议在模拟环境中充分测试后再切换到实盘

### 3. 安全考虑
- 实盘环境涉及真实资金，请谨慎操作
- 建议先在模拟环境中验证策略
- 定期备份重要配置和数据

### 4. 错误处理
- 环境切换失败时会记录错误日志
- 配置验证失败时会给出警告
- 程序会自动回退到默认环境

## 故障排除

### 1. QMT路径不存在
**问题:** 环境验证显示"QMT路径不存在"
**解决:** 
- 检查QMT软件是否正确安装
- 确认路径配置是否正确
- 检查路径中的反斜杠是否正确

### 2. 环境切换失败
**问题:** 环境切换时出现错误
**解决:**
- 检查配置文件格式是否正确
- 确认环境名称拼写正确
- 查看错误日志获取详细信息

### 3. 数据库连接失败
**问题:** 数据库连接错误
**解决:**
- 检查数据库服务器是否运行
- 确认数据库配置信息正确
- 检查网络连接是否正常

## 最佳实践

1. **开发阶段**: 始终使用模拟环境进行开发和测试
2. **测试阶段**: 在模拟环境中充分验证策略逻辑
3. **生产阶段**: 确认无误后再切换到实盘环境
4. **监控**: 定期检查环境配置和连接状态
5. **备份**: 定期备份配置文件和重要数据

## 更新日志

- **2025-07-18**: 更新QMT路径配置，修正模拟和实盘环境路径
- **2025-07-18**: 添加环境切换演示脚本
- **2025-07-18**: 完善环境管理器功能
- **2025-07-18**: 创建环境配置使用指南 