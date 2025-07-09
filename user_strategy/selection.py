import pandas as pd
import numpy as np
import tushare as ts
import talib
from scipy.stats import zscore
from sklearn.linear_model import Lasso, LinearRegression

class StockSelector:
    def __init__(self, token, start_date='20250101', end_date='20250310'):
        self.pro = ts.pro_api(token)
        self.start_date = start_date
        self.end_date = end_date
        self.factor_weights = None

    def get_factor_exposure(self):
        """幻方风格多因子体系"""
        return {
            'value': ['pe', 'pb', 'ps_ttm'],
            # 'growth': ['revenue_yoy', 'profit_yoy', 'np_yoy'],
            'quality': ['roe', 'grossprofit_margin', 'ocfps'],
            'momentum': ['1m_return', '3m_momentum', 'rsi_14'],
            # 'risk': ['beta', 'volatility_20d']
            'risk': ['volatility_20d']
        }

    def prepare_dataset(self):
        """准备全量因子数据"""
        print("正在加载基础数据...")
        # 获取股票池
        stock_list = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,industry,list_date')

        # 获取日频数据
        df_daily = self.pro.daily(start_date=self.start_date, end_date=self.end_date)
        df_adj = self.pro.adj_factor(start_date=self.start_date, end_date=self.end_date)
        daily_merged = pd.merge(df_daily, df_adj, on=['ts_code', 'trade_date'])

        # 获取财务数据
        # fina = self.pro.fina_indicator(ts_code="000002.SZ", period=self.end_date[:4] + '1231', fields='ts_code,roe,gp,ocfps,debt_to_assets')
        # fina = self.pro.fina_indicator(ts_code="000002.SZ", end_date=self.end_date[:4] + '1231', fields='ts_code,roe,gp,ocfps,debt_to_assets')
        full_data = pd.merge(stock_list, daily_merged, on='ts_code')
        fina = pd.DataFrame()
        i = 0
        for stock in stock_list.iterrows():
            f1 = self.pro.fina_indicator(ts_code=stock[1]['ts_code'], end_date=self.end_date, fields='ts_code,roe,grossprofit_margin,ocfps,debt_to_assets')
            f2 = self.pro.daily_basic(ts_code=stock[1]['ts_code'], trade_date=int(self.end_date)-1, fields='ts_code,pe,pb,ps_ttm')
            income_data = self.pro.income(ts_code=stock[1]['ts_code'], end_date=self.end_date, fields='end_date,total_revenue')
            income_data['end_date'] = pd.to_datetime(income_data['end_date'])
            income_data['revenue_yoy'] = income_data['total_revenue'].pct_change(periods=1) * 100
            fina = pd.concat([fina, pd.merge(f1.head(1), f2, on='ts_code', how='left')], ignore_index=True)
            if i >= 100:
                break
            i = i+1
            # 合并数据集
        full_data = pd.merge(full_data, fina, on='ts_code', how='left')

        # 计算复权价格
        full_data['adj_close'] = full_data['close'] * full_data['adj_factor']
        return full_data

    def calculate_beta(self, stock_return, market_return):
        """计算单个股票的 Beta 值"""
        if pd.isna(stock_return) or pd.isna(market_return):
            return np.nan
        cov = np.cov([stock_return, market_return])[0][1]
        var = np.var(market_return)
        if var == 0:
            return 0
        return cov / var
    def calculate_factors(self, df):
        """计算多因子指标"""
        print("正在计算因子值...")
        # grouped = df.groupby('ts_code')

        # 动量类因子
        df['1m_return'] = df['adj_close'].pct_change(20)
        df['3m_momentum'] = df['adj_close'].transform(lambda x: x.pct_change(60))

        # 波动率因子
        df['volatility_20d'] = df['adj_close'].transform(lambda x: x.pct_change().rolling(20).std())

        # 质量类因子（如果需要计算）
        # df['grossprofit_margin'] = df['gpr'] / df['revenue']

        # 风险因子（Beta计算）
        market_return = self.pro.index_daily(ts_code='000001.SH', start_date=self.start_date, end_date=self.end_date)['pct_chg'] / 100
        df['beta'] = df['pct_chg'].transform(lambda x: x.rolling(60).cov(market_return) / market_return.rolling(60).var())
        # df['beta'] = df.apply(lambda row: self.calculate_beta(row['pct_chg'], row['market_return']), axis=1)

        # 技术指标
        df['rsi_14'] = df['adj_close'].transform(lambda x: talib.RSI(x, timeperiod=14))
        df['1m_forward_return'] = df['adj_close'].shift(-20) / df['adj_close'] - 1

        return df.fillna(0)

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
                pass

        # Z-score标准化
        numeric_cols = [col for col in df.columns if col in self.get_all_factors()]
        df[numeric_cols] = df.groupby('trade_date')[numeric_cols].transform(zscore)

        return df

    def optimize_weights_with_ml(self, df):
        """使用机器学习优化因子权重"""
        all_factors = self.get_all_factors()
        available_factors = [factor for factor in all_factors if factor in df.columns]

        if not available_factors:
            print("警告: 没有可用的因子用于优化权重")
            return pd.Series()

        X = df[available_factors]
        y = df['1m_forward_return']

        # 使用Lasso回归
        model = Lasso(alpha=0.01)
        y = y[~np.isnan(X).any(axis=1)]
        X = X[~np.isnan(X).any(axis=1)]
        model.fit(X, y)
        self.factor_weights = pd.Series(model.coef_, index=available_factors)

        return self.factor_weights

    def get_all_factors(self):
        """获取所有因子"""
        all_factors = []
        factors_exposure = self.get_factor_exposure()
        for factor_type in factors_exposure.values():
            all_factors.extend(factor_type)
        return all_factors

    def stock_scoring(self, df):
        """生成综合评分"""
        print("计算股票评分...")
        all_factors = self.get_all_factors()
        available_factors = [factor for factor in all_factors if factor in df.columns]

        # 如果self.factor_weights为空，则重新计算权重
        if self.factor_weights is None or set(self.factor_weights.index) != set(available_factors):
            self.optimize_weights_with_ml(df)

        # 使用仅存在的因子来计算分数
        if available_factors and not self.factor_weights.empty:
            df['score'] = df[available_factors].dot(self.factor_weights.reindex(available_factors, fill_value=0))
        else:
            print("警告: 无可用因子用于计算综合评分")
            df['score'] = 0

        return df

    def get_top_stocks(self, top_n=50):
        """获取评分最高的股票"""
        df = self.prepare_dataset()
        df = self.calculate_factors(df)
        df = self.factor_processing(df)
        df = self.stock_scoring(df)
        top_stocks = df.sort_values(by='score', ascending=False).head(top_n)
        return top_stocks[['ts_code', 'score']]
