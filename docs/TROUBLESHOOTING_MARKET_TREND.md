# 市场趋势判断数据获取问题排查指南

## 🔍 问题现象

```
[市场趋势] 各因子得分: 
- ma_system: 错误(所有指数数据不足)
- fear_greed: 0.195 ✅ (正常)
- index_return: 错误(主要指数数据不足)
- volume: 错误(数据不足)
```

## 📋 快速诊断步骤

### 步骤1：检查Tushare Token

```python
# 在Python控制台运行
import config.ConfigServer as Cs
token = Cs.getTushareToken()
print(f"Token: {token[:10]}..." if token else "❌ Token未设置")
```

### 步骤2：测试获取指数数据

```python
# 测试获取上证指数数据（指数使用 index_daily API）
import tushare as ts
import config.ConfigServer as Cs

token = Cs.getTushareToken()
if not token:
    print("❌ Tushare Token未设置")
else:
    pro = ts.pro_api(token)
    try:
        # 指数数据使用 index_daily API
        df = pro.index_daily(ts_code='000001.SH', start_date='20240101', end_date='20241231')
        if df is None or df.empty:
            print("❌ Tushare返回空数据")
        else:
            print(f"✅ 成功获取 {len(df)} 条数据")
            print(f"列名: {df.columns.tolist()}")
            print(f"日期范围: {df['trade_date'].min()} 至 {df['trade_date'].max()}")
    except Exception as e:
        print(f"❌ API调用失败: {e}")
```

### 步骤3：检查所有指数代码

```python
# 测试所有指数代码（指数使用 index_daily API）
index_codes = ['000001.SH', '399001.SZ', '399006.SZ', '000905.SH']
for code in index_codes:
    try:
        # 指数数据使用 index_daily API
        df = pro.index_daily(ts_code=code, start_date='20240101', end_date='20241231')
        status = "✅" if df is not None and not df.empty else "❌"
        print(f"{status} {code}: {len(df) if df is not None else 0} 条数据")
    except Exception as e:
        print(f"❌ {code}: {e}")
```

## 🔧 常见问题及解决方案

### 问题1：Token无效或过期

**症状：**
- API调用返回错误
- 提示"权限不足"或"积分不足"

**解决：**
1. 登录 [Tushare官网](https://tushare.pro/)
2. 检查Token是否有效
3. 检查积分是否足够（指数数据可能需要积分）
4. 更新 `.env` 或 `Config.yaml` 中的Token

### 问题2：指数代码格式错误

**症状：**
- 返回空数据
- 提示"代码不存在"

**解决：**
- Tushare指数代码格式：
  - 上证指数：`000001.SH`
  - 深证成指：`399001.SZ`
  - 创业板指：`399006.SZ`
  - 中证500：`000905.SH`

### 问题3：API调用频率限制

**症状：**
- 部分请求成功，部分失败
- 提示"请求过于频繁"

**解决：**
1. 检查是否超过API调用限制
2. 添加请求延迟（已实现）
3. 考虑升级Tushare账户

### 问题4：网络连接问题

**症状：**
- 连接超时
- 无法访问Tushare API

**解决：**
1. 检查网络连接
2. 检查防火墙设置
3. 可能需要代理或VPN

## 📊 已实现的改进

### 1. 增强错误处理 ✅
- 检查数据是否为None或空
- 验证必需列（close, volume）
- 详细的错误日志

### 2. 改进数据获取 ✅
- 合理的日期范围（400天）
- 支持vol/volume列名兼容
- 使用logging替代print

### 3. 降级处理 ✅
- 数据获取失败时使用默认值（中性）
- 不影响系统运行
- 记录警告日志

## 🎯 预期结果

修复后，应该看到：
```
[市场趋势] 各因子得分: 
- ma_system: 0.xxx (正常数值，-1到1之间)
- fear_greed: 0.195 ✅
- index_return: 0.xxx (正常数值，-1到1之间)
- volume: 0.xxx (正常数值，-1到1之间)
```

## 📝 调试建议

1. **启用DEBUG日志**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **查看详细日志**
   - 查找 `获取.*历史行情失败`
   - 查找 `指数.*数据获取失败`
   - 查找 `数据质量不足`

3. **手动测试数据获取**
   ```python
   from main import get_history_func
   import config.ConfigServer as Cs
   
   token = Cs.getTushareToken()
   df = get_history_func('000001.SH', token)
   print(f"数据: {df is not None and not df.empty}")
   ```

## ⚠️ 注意事项

1. **Tushare免费版限制**
   - 有调用频率限制
   - 部分数据需要积分
   - 建议使用专业版

2. **数据更新延迟**
   - 非交易日可能无法获取最新数据
   - 数据可能有1-2天延迟

3. **降级方案**
   - 如果数据获取失败，系统会使用默认值
   - 不会影响交易系统运行
   - 但市场趋势判断可能不准确

