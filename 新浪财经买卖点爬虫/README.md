# 新浪财经/同花顺买卖点爬虫

## 功能说明

本爬虫提供两种方案获取股票的买卖点（B点和S点）数据：

1. **方案1：直接爬取新浪财经网页数据**
   - 优点：直接获取网站计算好的买卖点，无需自己实现算法
   - 缺点：依赖网站结构，可能不稳定，需要处理反爬机制

2. **方案2：自行计算买卖点指标（推荐）**
   - 优点：稳定可靠，可自定义策略，不依赖外部网站
   - 缺点：需要自己实现算法，需要历史数据源

## 安装依赖

```bash
pip install requests beautifulsoup4 pandas numpy
```

如果使用方案2，还需要：

```bash
# 使用Tushare数据源（推荐）
pip install tushare

# 或使用AKShare数据源（备用）
pip install akshare
```

## 使用方法

### 基本用法

```python
from main import BuySellPointCrawler
import os
from dotenv import load_dotenv

# 加载环境变量（包含TUSHARE_TOKEN）
load_dotenv()
tushare_token = os.getenv('TUSHARE_TOKEN')

# 方案1: 直接爬取新浪财经
crawler1 = BuySellPointCrawler(method='crawl')
result1 = crawler1.get_buy_sell_points('603444')  # 股票代码

# 方案2: 自行计算（推荐）
crawler2 = BuySellPointCrawler(method='calculate', tushare_token=tushare_token)
result2 = crawler2.get_buy_sell_points('603444', days=250)

# 保存结果到CSV
crawler2.save_to_csv(result2, '买卖点_603444.csv')
```

### 命令行使用

```bash
# 运行示例
python main.py
```

## 买卖点计算策略（方案2 - 优化版）

### 策略特点

- **加权评分系统**：使用多维度技术指标综合评分，而非简单计数
- **多指标确认**：结合均线、MACD、RSI、KDJ、布林带、成交量等6大类指标
- **趋势过滤**：使用长期均线（MA60）确认大趋势方向
- **信号强度分级**：根据评分自动分为强/中/弱三个等级
- **避免频繁交易**：设置最小间隔天数，减少假信号

### 买入点（B点）评分标准

**总分需达到2.5分以上（可配置）才会标记为买入点**

#### 1. 均线系统（权重1.5分）
- MA5上穿MA10：+0.5分
- MA5上穿MA20：+1.0分
- 价格在MA60上方（趋势确认）：+0.5分

#### 2. MACD指标（权重1.5分）
- MACD金叉（MACD线上穿信号线）：+1.0分
- MACD柱状图转正：+0.5分

#### 3. RSI指标（权重1.0分）
- RSI < 30（超卖）：+0.8分
- RSI < 40且上升：+0.5分

#### 4. KDJ指标（权重1.0分）
- K线上穿D线（金叉）：+0.5分
- J值 < 20（超卖）：+0.5分

#### 5. 布林带（权重1.0分）
- 价格触及或跌破下轨：+0.8分
- 价格从下轨反弹：+0.5分

#### 6. 成交量确认（权重1.0分）
- 量比 > 1.5（放量）：+0.5分
- 成交量突破均量：+0.5分

### 卖出点（S点）评分标准

**总分需达到2.5分以上（可配置）才会标记为卖出点**

#### 1. 均线系统（权重1.5分）
- MA5下穿MA10：+0.5分
- MA5下穿MA20：+1.0分
- 价格在MA60下方（趋势确认）：+0.5分

#### 2. MACD指标（权重1.5分）
- MACD死叉（MACD线下穿信号线）：+1.0分
- MACD柱状图转负：+0.5分

#### 3. RSI指标（权重1.0分）
- RSI > 70（超买）：+0.8分
- RSI > 60且下降：+0.5分

#### 4. KDJ指标（权重1.0分）
- K线下穿D线（死叉）：+0.5分
- J值 > 80（超买）：+0.5分

#### 5. 布林带（权重1.0分）
- 价格触及或突破上轨：+0.8分
- 价格从上轨回落：+0.5分

#### 6. 成交量确认（权重1.0分）
- 量比 > 1.5（放量）：+0.5分

### 信号强度分级

- **强信号**：评分 ≥ 4.0分
- **中信号**：评分 3.0-3.9分
- **弱信号**：评分 2.5-2.9分

### 技术指标说明

- **MA5/MA10/MA20/MA60**：5日、10日、20日、60日移动平均线
- **RSI**：相对强弱指标，周期14
- **MACD**：指数平滑移动平均线，参数(12, 26, 9)
- **KDJ**：随机指标，周期9
- **布林带**：周期20，标准差2.0
- **成交量指标**：5日成交量均线，量比 = 当日成交量 / 5日均量

## 数据格式

### 返回数据结构

```python
{
    'stock_code': '603444',  # 股票代码
    'method': 'calculate',   # 计算方法
    'calculate_time': '2025-01-26 10:30:00',  # 计算时间
    'total_buy_points': 5,   # 买入点总数
    'total_sell_points': 3,  # 卖出点总数
    'avg_buy_score': 3.2,     # 平均买入信号评分
    'avg_sell_score': 3.5,   # 平均卖出信号评分
    'buy_points': [          # 买入点列表
        {
            'date': '2025-01-15',
            'price': 450.50,
            'volume': 12345,
            'score': 3.2,      # 信号评分
            'strength': '中',   # 信号强度（强/中/弱）
            'rsi': 28.5,        # RSI值
            'macd_hist': 0.15   # MACD柱状图值
        },
        ...
    ],
    'sell_points': [         # 卖出点列表
        {
            'date': '2025-01-20',
            'price': 480.30,
            'volume': 23456,
            'score': 3.5,      # 信号评分
            'strength': '中',   # 信号强度（强/中/弱）
            'rsi': 72.3,       # RSI值
            'macd_hist': -0.12 # MACD柱状图值
        },
        ...
    ],
    'data': [...]  # 完整数据（如果数据量小于1000条）
}
```

## 股票代码格式

支持以下格式的股票代码：

- `603444` - 纯数字
- `603444.SH` - Tushare格式
- `sh603444` - 新浪财经格式

系统会自动识别并转换。

## 配置说明

### 环境变量

创建 `.env` 文件（可选，仅方案2需要）：

```env
TUSHARE_TOKEN=your_tushare_token_here
```

### 自定义参数

可以自定义买卖点计算参数：

```python
from main import BuySellPointCalculator

calculator = BuySellPointCalculator(
    ma_short=5,                    # 短期均线周期（默认5）
    ma_mid=10,                     # 中期均线周期（默认10）
    ma_long=20,                    # 长期均线周期（默认20）
    ma_trend=60,                   # 趋势均线周期（默认60）
    rsi_period=14,                 # RSI周期（默认14）
    macd_fast=12,                  # MACD快线周期（默认12）
    macd_slow=26,                  # MACD慢线周期（默认26）
    macd_signal=9,                 # MACD信号线周期（默认9）
    boll_period=20,                # 布林带周期（默认20）
    boll_std=2.0,                  # 布林带标准差倍数（默认2.0）
    kdj_period=9,                  # KDJ周期（默认9）
    volume_ma_period=5,            # 成交量均线周期（默认5）
    min_signal_score=2.5,          # 最小信号评分阈值（默认2.5，越高越严格）
    min_days_between_signals=3     # 买卖点之间的最小间隔天数（默认3）
)
```

**参数调整建议：**

- **更严格的策略**：`min_signal_score=3.5` 或 `4.0`（减少信号数量，提高质量）
- **更宽松的策略**：`min_signal_score=2.0`（增加信号数量，可能包含更多假信号）
- **减少频繁交易**：`min_days_between_signals=5` 或 `7`（避免频繁买卖）
- **更敏感的趋势判断**：`ma_trend=30`（使用30日均线判断趋势）

## 注意事项

1. **方案1（爬取）的限制**：
   - 新浪财经的买卖点数据可能通过JavaScript动态加载
   - 需要分析网页结构和网络请求找到真实API
   - 可能遇到反爬机制，需要添加更多处理逻辑

2. **方案2（计算）的推荐**：
   - 使用Tushare Pro API需要积分（免费版有限制）
   - AKShare是免费的备用方案
   - 可以根据自己的策略调整买卖点判断条件

3. **数据源选择**：
   - Tushare Pro：数据质量高，但需要token和积分
   - AKShare：免费，但可能不稳定
   - 也可以使用项目中的其他数据源（如XtQuant）

## 扩展开发

### 添加新的买卖点策略

修改 `BuySellPointCalculator.calculate_buy_sell_points()` 方法，添加自己的判断逻辑。

### 集成到项目

可以将此爬虫集成到项目的策略系统中：

```python
from 新浪财经买卖点爬虫.main import BuySellPointCrawler

# 在策略中使用买卖点数据
crawler = BuySellPointCrawler(method='calculate', tushare_token=token)
buy_sell_data = crawler.get_buy_sell_points(stock_code)

# 根据买卖点生成交易信号
for buy_point in buy_sell_data['buy_points']:
    # 执行买入逻辑
    pass
```

## 常见问题

**Q: 方案1爬取不到数据怎么办？**  
A: 新浪财经的买卖点数据可能是动态加载的，需要：
   - 使用Selenium或Playwright等浏览器自动化工具
   - 分析Network请求找到真实API接口
   - 或者直接使用方案2自行计算

**Q: Tushare token如何获取？**  
A: 访问 https://tushare.pro/ 注册账号，获取token。

**Q: 如何调整买卖点判断的严格程度？**  
A: 调整 `BuySellPointCalculator` 的参数：
   - `min_signal_score`：提高此值（如3.5或4.0）使策略更严格
   - `min_days_between_signals`：增加此值（如5或7）减少交易频率
   - 也可以修改各个指标的权重和评分标准

**Q: 信号强度如何理解？**  
A: 信号强度根据评分自动分级：
   - 强信号（≥4.0分）：多个指标同时确认，可靠性高
   - 中信号（3.0-3.9分）：部分指标确认，可靠性中等
   - 弱信号（2.5-2.9分）：仅达到最低阈值，建议谨慎操作

**Q: 为什么有些日期没有买卖点？**  
A: 可能原因：
   - 评分未达到阈值（`min_signal_score`）
   - 距离上次信号太近（受`min_days_between_signals`限制）
   - 数据不足无法计算所有指标

## 验证和测试

### 快速测试

运行快速测试脚本，验证功能是否正常工作：

```bash
python quick_test.py
```

这会：
- 测试基本的买卖点计算功能
- 显示计算结果摘要
- 保存测试结果到CSV文件

### 完整验证

运行完整的验证工具：

```bash
python verify.py
```

验证工具提供以下功能：

1. **验证单只股票**：检查买卖点计算的正确性和数据质量
2. **回测策略**：模拟交易，计算收益率、胜率、最大回撤等指标
3. **对比不同策略**：比较保守/平衡/激进三种策略的表现
4. **批量验证**：验证多只股票

### 验证示例

```python
from verify import BuySellPointVerifier

# 创建验证器
verifier = BuySellPointVerifier(tushare_token="your_token")

# 验证单只股票
verifier.verify_single_stock('603444', days=250)

# 回测策略
backtest_result = verifier.backtest_strategy('603444', days=250, initial_capital=100000)
print(f"总收益率: {backtest_result['total_return']:.2f}%")
print(f"胜率: {backtest_result['win_rate']:.2f}%")

# 对比不同策略
verifier.compare_strategies('603444', days=250)
```

### 验证指标说明

- **数据质量验证**：检查买卖点数量、评分合理性、信号强度分布等
- **回测指标**：
  - 总收益率：策略整体收益
  - 胜率：盈利交易占比
  - 最大回撤：最大亏损幅度
  - 平均收益：平均每次交易收益
- **策略对比**：比较不同参数设置下的信号数量和评分

## 更新日志

- **v1.1** (2025-01-26)
  - 优化买卖点计算策略，使用加权评分系统
  - 新增KDJ、布林带、成交量等指标
  - 添加信号强度分级（强/中/弱）
  - 新增验证和回测工具

- **v1.0** (2025-01-26)
  - 初始版本
  - 支持两种方案获取买卖点
  - 支持Tushare和AKShare数据源
