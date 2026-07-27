# Quantitative Trading System - Position Analysis Module

## Project Overview

This is a Python-based quantitative trading system integrating complete position analysis functions, including:
- Position data management
- Technical analysis
- Risk control
- Visualization reports
- XtQuant integration

## Main Features

### 1. Backtesting Framework
- **Backtrader Integration**: Uses the mature Backtrader backtesting framework.
- **Multi-strategy Support**: Supports backtesting multiple strategies simultaneously.
- **Parameter Optimization**: Automatic parameter optimization and strategy selection.
- **Detailed Analysis**: Comprehensive performance analysis and risk metrics.

### 2. Position Analysis Module
- **Position Query**: Supports retrieving real-time position data from XtQuant.
- **Risk Analysis**: Calculates concentration risk, volatility risk, VaR, and other metrics.
- **Performance Evaluation**: Analyzes return rates, maximum drawdown, Sharpe ratio, etc.
- **Visualization Reports**: Generates charts and PDF reports.

### 2. Technical Analysis Module
- **Technical Indicators**: Supports indicators such as MA, MACD, RSI, KDJ, Bollinger Bands, etc.
- **Trading Signals**: Generates buy/sell signals based on a comprehensive multi-indicator score.
- **Trend Analysis**: Identifies bullish/bearish trends.
- **Signal Filtering**: Supports confidence filtering and risk control.

### 3. XtQuant Integration
- **Real-time Data**: Retrieves position and market data from XtQuant.
- **Automatic Analysis**: Regularly analyzes positions and provides trading suggestions.
- **Risk Monitoring**: Real-time monitoring of position risks.

## Python Environment

Python 3.11.9 is recommended.

```bash
conda create -n py311 python=3.11.9
conda activate py311
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

**Important Dependency Notes**:
- `backtrader`: Backtesting framework
- `tushare`: Financial data interface
- `talib-binary`: Technical analysis library
- `xtquant`: Xuntou quantitative trading interface
- `matplotlib`: Chart generation
- `pandas`: Data processing
- `numpy`: Numerical computation

## Environment Configuration

When using the project for the first time, you need to complete two types of configurations: `.env` environment variables and `config/Config.yaml` account configuration.

### 1. .env Environment Variables

```bash
# Copy the environment variable example file
cp .env.example .env

# Edit the .env file to configure sensitive information required for operation,
# such as: TUSHARE_TOKEN, MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, etc.
```

This file is read by modules like `modules/data_service/config.py` and `utils/environment_manager.py` for:
- `TUSHARE_TOKEN`: Used for data collection and indicator calculation.
- `MYSQL_*`: Database connections.
- Other third-party service credentials.

**Note**: The `.env` file contains sensitive information and will not be submitted to the Git repository. Please ensure it is maintained locally.

### 2. config/Config.yaml Trading Environment

`config/ConfigServer.py` reads this file to provide unified trading environment configurations for the Web/API, strategies, and demo scripts.

Key field descriptions:
- `SIMULATION` / `PRODUCTION`: Configures `QMT_PATH`, `ACCOUNT`, `NAME`, etc., for simulation and live trading respectively.
- `toshare_token`: Keep consistent with `TUSHARE_TOKEN` in `.env`, allowing the Tornado API and XtQuant modules to retrieve it quickly.
- `DATABASE`: Maintained here when database configuration needs to be loaded via YAML.

To switch trading environments, simply update `Config.yaml` and restart the relevant scripts/services without needing to maintain duplicate `configs/ConfigServer.py` files.

## Quick Start

### 1. Start Web Server

```bash
python main.py
```

### 2. Run Demo Scripts

```bash
# Position analysis demo
python demo_position_analysis.py

# XtQuant technical analysis demo
python demo_xtquant_analysis.py

# Backtrader backtest demo
python demo_backtrader_example.py

# Backtrader framework test
python test_backtrader_framework.py

# BYD strategy backtest demo
python simple_byd_backtest.py

# BYD strategy demo
python demo_byd_strategy.py

# BYD strategy simple test
python test_byd_simple.py
```

### 3. Access API Interface

After starting the server, you can access the following API endpoints:

#### API Documentation (Swagger)
- `GET /api-docs` - Swagger UI interface (interactive API documentation)
- `GET /api-docs/swagger.json` - OpenAPI specification JSON

Visit `http://localhost:8888/api-docs` in your browser to view the full API documentation.

#### API Endpoint List

#### Position Analysis API
- `GET /api/position/analysis?account_id=demo` - Get position analysis
- `GET /api/position/detail?account_id=demo` - Get position details
- `GET /api/position/report?account_id=demo&type=summary` - Generate position report

#### Technical Analysis API
- `GET /api/technical/analysis?account_id=demo` - Get technical analysis
- `GET /api/technical/signals?account_id=demo&min_confidence=0.7` - Get trading signals
- `GET /api/technical/indicators?symbol=000001.SZ&days=60` - Get technical indicators

## Usage Examples

### 1. Position Analysis

```python
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer

# Create analyzer
analyzer = PositionAnalyzer(tushare_token)

# Analyze positions
positions_data = [
    {
        "symbol": "000001.SZ",
        "volume": 1000,
        "avg_price": 15.50,
        "current_price": 16.20
    }
]

analysis = analyzer.analyze_positions(positions_data, cash=50000)
print(f"Total Return: {analysis.summary.total_unrealized_pnl_pct:.2f}%")
```

### 2. Backtest Analysis

```python
from modules.backtrader_engine import BacktraderEngine, TushareDataFeed, MAStrategy

# Create backtest engine
engine = BacktraderEngine(initial_cash=1000000, commission=0.001)

# Add data source and strategy
data_feed = TushareDataFeed(symbol='000001.SZ', start_date='20230101', 
                           end_date='20231231', tushare_token='your_token')
engine.add_data(data_feed)
engine.add_strategy(MAStrategy)

# Run backtest
result = engine.run_backtest()
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

### 3. BYD Strategy Backtest

```python
from strategies.byd_strategy import BYDStrategy, BYDEnhancedStrategy, BYDConservativeStrategy

# Run BYD strategy backtest
python simple_byd_backtest.py

# View detailed explanation
# Refer to BYD_STRATEGY_SUMMARY.md file
```

### 3. Technical Analysis

```python
from modules.tornadoapp.position.xtquant_position_manager import XtQuantPositionManager

# Create XtQuant manager
manager = XtQuantPositionManager(tushare_token)

# Analyze positions
results = await manager.analyze_all_positions("demo_account")

# Get trading recommendations
recommendations = manager.generate_trading_recommendations(results)
for rec in recommendations:
    print(f"{rec['symbol']}: {rec['action']} (Confidence: {rec['confidence']:.2f})")
```

### 3. Visualization Report

```python
from modules.tornadoapp.position.position_visualizer import PositionVisualizer

# Create visualization tool
visualizer = PositionVisualizer()

# Generate charts
charts = visualizer.generate_comprehensive_report(analysis)
```

## Project Structure

```
modules/tornadoapp/position/
├── __init__.py                    # Module initialization
├── position_analyzer.py           # Position analyzer
├── position_visualizer.py         # Visualization tool
├── xtquant_position_manager.py    # XtQuant integration
└── position_api.py               # API routes

modules/tornadoapp/handler/
├── position_handler.py            # Position analysis API handler
└── technical_analysis_handler.py  # Technical analysis API handler

modules/tornadoapp/model/
└── position_model.py              # Position data model
```

## Technical Indicator Specifications

### Supported Indicators
- **Moving Average**: MA5, MA10, MA20, MA60
- **MACD**: Trend indicator
- **RSI**: Relative Strength Index
- **KDJ**: Stochastic oscillator
- **Bollinger Bands**: Volatility indicator
- **Volume**: Price-volume relationship analysis

### Trading Signal Generation
The system generates trading signals based on a comprehensive multi-indicator score:
- **Buy Signal**: Score >= 3.0
- **Sell Signal**: Score <= -3.0
- **Hold Signal**: -3.0 < Score < 3.0

## Live Trading Records

📊 **Live Operation Records**: [View Detailed Records](https://www.yuque.com/u22168851/efpig6/cyhmt81dze3g8676)

Real-time tracking of the system's performance in a real market environment, including:
- Daily trading records
- Strategy execution status
- Return and risk analysis
- Lessons learned and optimization suggestions

## Risk Warning

⚠️ **Important Reminder**:
- Analysis results provided by this system are for reference only and do not constitute investment advice.
- Technical analysis has a lag; please combine it with fundamental analysis.
- Investing involves risk; enter the market with caution.
- Sufficient backtesting validation is recommended before live trading.
- **Live trading involves real funds; please ensure strict risk control.**

## Development Instructions

### Adding New Technical Indicators

```python
def calculate_custom_indicator(self, df: pd.DataFrame) -> float:
    """Calculate custom indicator"""
    close_prices = df['close'].values.astype(np.float64)
    # Implement indicator calculation logic
    return indicator_value
```

### Extending Trading Signal Logic

```python
def generate_custom_signals(self, indicators: Dict, current_price: float) -> Dict:
    """Generate custom trading signals"""
    # Implement signal generation logic
    return signals
```

## Market Data Storage

### Database Design

This project uses a MySQL database specifically designed for recording market data to prepare data for future quantitative AI models.

#### Database Features

- **Focused Data Storage**: Simplified design focusing on market data storage and querying.
- **Xuntou Support**: Full support for Xuntou's 3-second tick data, minute-level, and daily data.
- **AI-Friendly**: Provides convenient data access interfaces for machine learning models.
- **High Performance**: Optimized indexing strategies and query performance.
- **Easy Maintenance**: Simple table structure and clear data management.

#### Core Table Structure

##### 1. Stock Basic Information
- `stock_basic`: Stock basic information table

##### 2. Market Data Tables
- `tick_data`: 3-second level tick data
- `minute_data`: Minute-level market data
- `daily_data`: Daily market data
- `adj_factor`: Adjustment factor table

##### 3. Technical Indicators
- `technical_indicators`: Technical indicators table

##### 4. Data Management
- `data_sync_status`: Data synchronization status table
- `system_config`: System configuration table

#### Quick Start

##### 1. Initialize Database
```bash
# One-click database initialization
python database/init_market_data.py --host localhost --user root --password your_password

# Test connection
python database/init_market_data.py --test-only --host localhost --user root --password your_password
```

##### 2. Basic Usage
```python
from database.market_data_manager import MarketDataManager

# Create data manager
manager = MarketDataManager(
    host='localhost',
    port=3306,
    user='market_data_app',
    password='app_password',
    database='market_data'
)

# Test connection
if manager.test_connection():
    print("✅ Database connection successful!")
```

##### 3. Store Market Data
```python
import pandas as pd

# Store stock basic info
stocks_data = pd.DataFrame({
    'ts_code': ['000001.SZ', '000002.SZ', '600519.SH'],
    'symbol': ['000001', '000002', '600519'],
    'name': ['Ping An Bank', 'Vanke A', 'Kweichow Moutai'],
    'industry': ['Bank', 'Real Estate', 'Food & Beverage'],
    'market': ['Main Board', 'Main Board', 'Main Board']
})
manager.insert_stock_basic(stocks_data)

# Store daily data
daily_data = pd.DataFrame({
    'symbol': ['000001.SZ'],
    'trade_date': ['2025-01-15'],
    'open': [15.50], 'high': [15.80], 'low': [15.40], 'close': [15.70],
    'volume': [1000000], 'amount': [15700000], 'pct_chg': [1.29]
})
manager.insert_daily_data(daily_data)

# Store tick data
tick_data = pd.DataFrame({
    'symbol': ['000001.SZ'] * 100,
    'tick_time': pd.date_range('2025-01-15 09:30:00', periods=100, freq='3S'),
    'last_price': [15.50 + i * 0.01 for i in range(100)],
    'volume': [1000] * 100,
    'amount': [15500 + i * 10 for i in range(100)]
})
manager.insert_tick_data(tick_data)
```

##### 4. Query Market Data
```python
# Get stock list
stocks = manager.get_stock_list()
print(f"Total stocks: {len(stocks)}")

# Get daily data
daily_data = manager.get_daily_data('000001.SZ', '2025-01-01', '2025-01-15')
print(f"Daily data records: {len(daily_data)}")

# Get tick data
tick_data = manager.get_tick_data('000001.SZ', '2025-01-15 09:30:00', '2025-01-15 10:00:00')
print(f"Tick data records: {len(tick_data)}")

# Get latest price
latest_price = manager.get_latest_price('000001.SZ')
print(f"Latest price of Ping An Bank: {latest_price}")
```

##### 5. Prepare Data for AI Models
```python
# Get training data
def get_training_data(symbol, start_date, end_date):
    """Retrieve data for AI model training"""
    # Get daily data
    daily_data = manager.get_daily_data(symbol, start_date, end_date)
    
    # Get technical indicators
    indicators = manager.get_technical_indicators(symbol, start_date, end_date)
    
    # Merge data
    training_data = daily_data.merge(indicators, on=['symbol', 'trade_date'], how='left')
    
    # Calculate features
    training_data['price_change'] = training_data['close'].pct_change()
    training_data['volume_change'] = training_data['volume'].pct_change()
    training_data['ma5_ma20_diff'] = training_data['ma5'] - training_data['ma20']
    
    return training_data

# Get training data
training_data = get_training_data('000001.SZ', '2024-01-01', '2024-12-31')
print(f"Training data shape: {training_data.shape}")
```

#### Data Export

```python
# Export data to CSV
csv_file = manager.export_data_to_csv(
    symbol='000001.SZ',
    data_type='daily',
    start_date='2025-01-01',
    end_date='2025-01-15',
    output_dir='data/export'
)
print(f"Data exported to: {csv_file}")
```

#### Detailed Usage Guide

For more detailed usage and examples, please refer to:
- `database/MARKET_DATA_GUIDE.md` - Complete usage guide
- `database/market_data_manager.py` - Data manager source code
- `database/market_data_schema.sql` - Database table schema

## License

This project is for learning and research purposes only. Please do not use it for commercial purposes.

## Contact

If you have any questions or suggestions, please contact via:
- Submit an Issue
- Send an email
- Project discussion area

### Add on WeChat

Scan the QR code below to add me on WeChat and exchange quantitative trading experience:

<div align="center">
  <img src="docs/images/wechat_qrcode.jpg" alt="WeChat QR Code" width="300"/>
  <p>Scan the QR code above to add me as a friend.</p>
</div>

**WeChat ID**: nzc  
**Region**: Kaifeng, Henan

### Join Quantitative Investment Exchange Group

Scan the QR code below to join the WeChat group and exchange ideas with more quantitative trading enthusiasts:

<div align="center">
  <img src="docs/images/wechat_group_qrcode.jpg" alt="WeChat Group QR Code" width="300"/>
  <p><strong>Group: Quantitative Investment Exchange Group</strong></p>
  <p>⚠️ This QR code is valid for 7 days (until March 16); it will be updated upon re-entry.</p>
</div>

**Group Discussion Topics**:
- Quantitative strategy discussions
- Live trading experience sharing
- Technical Q&A
- Market analysis
- Code optimization suggestions
