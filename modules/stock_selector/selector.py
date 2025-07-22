import pandas as pd
from typing import List, Optional, Dict, Any
import tushare as ts
import numpy as np

class HotIndustrySelector:
    """
    热点行业自动识别与多因子选股
    """
    def __init__(self, tushare_token, top_n_industries=3, stock_per_industry=5):
        self.pro = ts.pro_api(tushare_token)
        self.top_n_industries = top_n_industries
        self.stock_per_industry = stock_per_industry

    def get_hot_industries(self, period_days=5):
        today = pd.Timestamp.today().strftime('%Y%m%d')
        start = (pd.Timestamp.today() - pd.Timedelta(days=period_days)).strftime('%Y%m%d')
        stock_info = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,industry')
        daily = self.pro.daily(start_date=start, end_date=today)
        last_day = daily.groupby('ts_code').tail(1).set_index('ts_code')
        first_day = daily.groupby('ts_code').head(1).set_index('ts_code')
        pct = (last_day['close'] - first_day['close']) / first_day['close']
        stock_info = stock_info.set_index('ts_code')
        stock_info['pct'] = pct
        industry_pct = stock_info.groupby('industry')['pct'].mean().sort_values(ascending=False)
        hot_industries = industry_pct.head(self.top_n_industries).index.tolist()
        return hot_industries

    def select_stocks(self, hot_industries):
        stock_info = self.pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,industry')
        selected_stocks = []
        for industry in hot_industries:
            codes = stock_info[stock_info['industry'] == industry]['ts_code'].tolist()
            # 剔除北交所股票（.BJ结尾）
            codes = [code for code in codes if not code.endswith('.BJ')]
            if not codes:
                continue
            basics = self.pro.daily_basic(ts_code=','.join(codes), fields='ts_code,pe,pb,roe,turnover_rate,close')
            basics = basics.dropna()
            # 字段健壮性判断
            required_fields = ['pe', 'pb']
            for f in required_fields:
                if f not in basics.columns:
                    print(f"[警告] {industry}行业缺少{f}字段，跳过该行业")
                    basics = pd.DataFrame()  # 置空
                    break
            if basics.empty:
                continue
            # roe可选
            if 'roe' in basics.columns:
                basics = basics[(basics['pe'] > 0) & (basics['pe'] < 30) & (basics['pb'] < 3) & (basics['roe'] > 10)]
                basics['score'] = (1 / basics['pe']) + basics['roe'] + (1 / basics['pb'])
            else:
                basics = basics[(basics['pe'] > 0) & (basics['pe'] < 30) & (basics['pb'] < 3)]
                basics['score'] = (1 / basics['pe']) + (1 / basics['pb'])
            basics = basics.sort_values('score', ascending=False).head(self.stock_per_industry)
            selected_stocks.extend(basics['ts_code'].tolist())
        return selected_stocks

    def run(self):
        hot_industries = self.get_hot_industries()
        selected_stocks = self.select_stocks(hot_industries)
        return selected_stocks

class StockSelector:
    """
    标准选股服务，支持多条件筛选和pywencai智能选股。
    """
    def __init__(self, data_source=None, tushare_token=None):
        self.data_source = data_source
        self.tushare_token = tushare_token

    def select(
        self,
        min_pe: Optional[float] = None,
        max_pe: Optional[float] = None,
        min_mv: Optional[float] = None,
        max_mv: Optional[float] = None,
        industry: Optional[str] = None,
        min_change: Optional[float] = None,
        max_change: Optional[float] = None,
        ma_cross: Optional[Dict[str, int]] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        df = self.data_source.get_all_stocks()
        if min_pe is not None:
            df = df[df['pe'] >= min_pe]
        if max_pe is not None:
            df = df[df['pe'] <= max_pe]
        if min_mv is not None:
            df = df[df['market_value'] >= min_mv]
        if max_mv is not None:
            df = df[df['market_value'] <= max_mv]
        if industry:
            df = df[df['industry'] == industry]
        if min_change is not None:
            df = df[df['pct_chg'] >= min_change]
        if max_change is not None:
            df = df[df['pct_chg'] <= max_change]
        if ma_cross:
            short = ma_cross.get('short', 5)
            long = ma_cross.get('long', 20)
            if f'ma{short}' in df.columns and f'ma{long}' in df.columns:
                df = df[df[f'ma{short}'] > df[f'ma{long}']]
        result = df[['symbol', 'name', 'industry', 'pe', 'market_value', 'pct_chg']].head(limit)
        return result.to_dict(orient='records')

    def select_by_wencai(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """用pywencai智能选股"""
        try:
            import pywencai
        except ImportError:
            raise RuntimeError("请先安装 pywencai: pip install pywencai")
        df = pywencai.get(query = query)
        if df is None or df.empty:
            return []
        code_col = 'code' if 'code' in df.columns else '股票代码'
        name_col = 'name' if 'name' in df.columns else '股票简称'
        result = df[[code_col, name_col]].head(limit)
        result = result.rename(columns={code_col: 'symbol', name_col: 'name'})
        return result.to_dict(orient='records')

    def select_by_hot_industry(self, period_days=5, top_n_industries=3, stock_per_industry=5):
        """
        自适应热点行业多因子选股，返回股票代码列表。
        """
        if not self.tushare_token:
            raise ValueError("请在StockSelector初始化时传入tushare_token参数")
        selector = HotIndustrySelector(self.tushare_token, top_n_industries, stock_per_industry)
        return selector.run() 