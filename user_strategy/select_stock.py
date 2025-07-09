'''
代码说明
MySQL 数据库集成：

使用 pymysql 连接 MySQL 数据库。

数据保存和加载通过 save_data 和 load_data 方法实现。

多线程实现：

update_daily_data：数据更新线程，每天更新一次数据。

daily_auto_execution：策略执行线程，每天生成交易信号。

real_time_monitoring：实时监控线程，每小时检查策略表现。

功能整合：

数据缓存与增量更新。

因子扩展与动态中性化。

机器学习优化因子权重。

交易成本与风险控制。

绩效分析与实时监控。


+=====================================================================
运行说明
安装依赖库：

bash
复制
pip install tushare scikit-learn talib tqdm pymysql
替换以下配置：

your_tushare_token：您的 Tushare API Token。

db_config：您的 MySQL 数据库配置。

运行代码：

bash
复制
python main.py
程序将自动启动数据更新、策略执行和实时监控线程，并在控制台输出运行日志。

'''

import numpy as np
import pandas as pd
import pymysql
import tushare as ts
import talib
from scipy.stats import zscore
from sklearn.linear_model import LinearRegression, Lasso
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
import time
from tqdm import tqdm
import threading
import config.ConfigServer as Cs


class QuantitativeStockSelector:
    def __init__(self, token, start_date='20180101', end_date='20231231', db_config=None):
        self.pro = ts.pro_api(token)
        self.start_date = start_date
        self.end_date = end_date
        self.factor_weights = None
        self.db_config = db_config
        connection_string = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}@"
            f"{db_config['host']}:{db_config['port']}/{db_config['database']}?"
            f"charset={db_config['charset']}"
        )
        self.engine = create_engine(connection_string, echo=True)
        self.conn = pymysql.connect(**db_config)
        self.cursor = self.conn.cursor()

    def save_data(self, table_name, data):
        """将数据保存到 MySQL 数据库"""
        # data.to_sql(table_name, self.conn, if_exists='replace', index=False, method='multi')
        # data.to_sql(table_name, self.engine, if_exists='replace', index=False, method='multi')
        data.to_sql(table_name, self.engine, if_exists='append', index=False, method='multi')

    def load_data(self, table_name):
        """从 MySQL 数据库加载数据"""
        query = f"SELECT * FROM {table_name}"
        return pd.read_sql(query, self.conn)

    def close(self):
        """关闭数据库连接"""
        self.conn.close()

    def update_daily_data(self):
        """增量更新日频数据"""
        while True:
            latest_date = self.pro.trade_cal(exchange='SSE', is_open='1')['cal_date'].iloc[-1]
            new_data = self.pro.daily(trade_date=latest_date)

            # 加载本地数据
            local_data = self.load_data('daily_data')

            # 合并新数据
            updated_data = pd.concat([local_data, new_data]).drop_duplicates(subset=['ts_code', 'trade_date'])

            # 保存更新后的数据
            self.save_data('daily_data', updated_data)
            print(f"数据已更新至 {latest_date}")
            time.sleep(86400)  # 每天更新一次

    def get_factor_exposure(self):
        """幻方风格多因子体系"""
        return {
            'value': ['pe', 'pb', 'ps_ttm'],
            'growth': ['revenue_yoy', 'profit_yoy', 'np_yoy'],
            'quality': ['roe', 'grossprofit_margin', 'ocfps'],
            'momentum': ['1m_return', '3m_momentum', 'rsi_14'],
            'risk': ['beta', 'volatility_20d']
        }

    def prepare_dataset(self):
        """准备全量因子数据"""
        print("正在加载基础数据...")
        # 获取股票池
        stock_list = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,industry,list_date')

        # 获取日频数据
        df_daily = self.load_data('daily_data')
        df_adj = self.pro.adj_factor(start_date=self.start_date, end_date=self.end_date)
        daily_merged = pd.merge(df_daily, df_adj, on=['ts_code', 'trade_date'])

        # 获取财务数据
        fina = self.pro.fina_indicator(period=self.end_date[:4] + '1231', fields='ts_code,roe,gp,ocfps,debt_to_assets')

        # 合并数据集
        full_data = pd.merge(stock_list, daily_merged, on='ts_code')
        full_data = pd.merge(full_data, fina, on='ts_code', how='left')

        # 计算复权价格
        full_data['adj_close'] = full_data['close'] * full_data['adj_factor']
        return full_data

    def calculate_factors(self, df):
        """计算多因子指标"""
        print("正在计算因子值...")
        grouped = df.groupby('ts_code')

        # 动量类因子
        df['1m_return'] = grouped['adj_close'].pct_change(20)
        df['3m_momentum'] = grouped['adj_close'].apply(lambda x: x.pct_change(60))

        # 波动率因子
        df['volatility_20d'] = grouped['adj_close'].transform(lambda x: x.pct_change().rolling(20).std())

        # 质量类因子
        df['grossprofit_margin'] = df['gp'] / df['revenue']

        # 风险因子（Beta计算）
        market_return = self.pro.index_daily(ts_code='000001.SH', start_date=self.start_date, end_date=self.end_date)[
                            'pct_chg'] / 100
        df['beta'] = grouped['pct_chg'].transform(
            lambda x: x.rolling(60).cov(market_return) / market_return.rolling(60).var())

        # 技术指标
        df['rsi_14'] = grouped['adj_close'].transform(lambda x: talib.RSI(x, timeperiod=14))

        return df.dropna()

    def factor_processing(self, df):
        """因子标准化与中性化"""
        print("因子预处理中...")
        # 行业中性化
        industry_dummies = pd.get_dummies(df['industry'])
        for factor in self.get_factor_exposure().keys():
            for f in self.get_factor_exposure()[factor]:
                model = LinearRegression()
                model.fit(industry_dummies, df[f])
                df[f] = df[f] - model.predict(industry_dummies)

        # 市值中性化
        df['circ_mv'] = df['close'] * df['circ_mv']  # 假设有流通市值字段
        for factor in self.get_factor_exposure().keys():
            for f in self.get_factor_exposure()[factor]:
                df[f] = df[f] - df[f].mean()  # 简化处理

        # Z-score标准化
        numeric_cols = [col for col in df.columns if col in self.get_all_factors()]
        df[numeric_cols] = df.groupby('trade_date')[numeric_cols].transform(zscore)

        return df

    def optimize_weights_with_ml(self, df):
        """使用机器学习优化因子权重"""
        X = df[self.get_all_factors()]
        y = df['1m_forward_return']

        # 使用Lasso回归
        model = Lasso(alpha=0.01)
        model.fit(X, y)
        self.factor_weights = pd.Series(model.coef_, index=self.get_all_factors())

        return self.factor_weights

    def stock_scoring(self, df):
        """生成综合评分"""
        print("计算股票评分...")
        factors = self.get_all_factors()
        df['score'] = df[factors].dot(self.factor_weights.reindex(factors, fill_value=0))
        return df

    def backtest_with_costs(self, signals, commission=0.0003, slippage=0.0005):
        """考虑交易成本的回测"""
        portfolio_returns = []
        for i in range(len(signals) - 1):
            stocks = signals.iloc[i]
            next_returns = self.pro.daily(trade_date=signals.index[i + 1]).set_index('ts_code')['pct_chg'] / 100

            # 计算组合收益（考虑交易成本）
            portfolio_ret = next_returns.loc[next_returns.index.isin(stocks)].mean()
            portfolio_ret -= commission + slippage  # 扣除佣金和滑点
            portfolio_returns.append(portfolio_ret)

        return portfolio_returns

    def build_portfolio_with_risk_control(self, df, max_stock_weight=0.05, max_industry_weight=0.2):
        """加入风险控制的组合构建"""
        df['weight'] = df['score'] / df['score'].sum()

        # 单只股票权重上限
        df['weight'] = df['weight'].apply(lambda x: min(x, max_stock_weight))

        # 行业权重上限
        industry_weights = df.groupby('industry')['weight'].sum()
        for industry, weight in industry_weights.items():
            if weight > max_industry_weight:
                df.loc[df['industry'] == industry, 'weight'] *= max_industry_weight / weight

        return df

    def generate_performance_report(self, returns):
        """生成绩效分析报告"""
        annual_return = np.prod([1 + r for r in returns]) ** (252 / len(returns)) - 1
        sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        max_drawdown = self.calculate_max_drawdown(pd.Series(returns))
        win_rate = len([r for r in returns if r > 0]) / len(returns)

        report = f"""
        === 策略绩效报告 ===
        年化收益率：{annual_return:.2%}
        夏普比率：{sharpe_ratio:.2f}
        最大回撤：{max_drawdown:.2%}
        胜率：{win_rate:.2%}
        """
        return report

    def daily_auto_execution(self):
        """每日自动化执行"""
        while True:
            self.update_daily_data()
            self.optimize_weights()
            signals = self.backtest_engine()
            print("今日交易信号已生成：", signals)
            time.sleep(86400)  # 每天执行一次
    def calculate_current_performance(self):
        data = {'drawdown':1}
        return data
        pass

    def adjust_portfolio(self):
        pass

    def real_time_monitoring(self):
        """实时监控策略表现"""
        while True:
            current_performance = self.calculate_current_performance()
            if current_performance['drawdown'] > 0.1:  # 假设最大回撤阈值为10%
                self.adjust_portfolio()  # 调整组合
            print("当前策略表现：", current_performance)
            time.sleep(3600)  # 每小时检查一次

#================================================================================================
def run_strategy():
    # MySQL 数据库配置
    configData = Cs.returnConfigData()
    # miniQMT安装路径
    path = configData["QMT_PATH"][0]
    # QMT账号
    toshare_token = configData["toshare_token"]
    db_config = {
        'host': 'localhost',
        'user': 'root',
        'password': '6116988.niu',
        'database': 'stock_data',
        'port': 3306,
        'charset': 'utf8mb4'
    }

    qs = QuantitativeStockSelector(token=toshare_token, db_config=db_config)
    # top50 = qs.get_top50_stocks()
    # print("\n当前推荐Top50股票：")
    # print(top50.to_string(index=False))

    # 启动数据更新线程
    data_update_thread = threading.Thread(target=qs.update_daily_data)
    data_update_thread.daemon = True
    data_update_thread.start()

    # 启动策略执行线程
    strategy_execution_thread = threading.Thread(target=qs.daily_auto_execution)
    strategy_execution_thread.daemon = True
    strategy_execution_thread.start()

    # 启动实时监控线程
    monitoring_thread = threading.Thread(target=qs.real_time_monitoring)
    monitoring_thread.daemon = True
    monitoring_thread.start()

    # 主线程保持运行
    while True:
        time.sleep(1)

if __name__ == '__main__':
    run_strategy()
