import pandas as pd
from typing import List, Optional, Dict, Any
import tushare as ts
import numpy as np
import pywencai as wc
import logging

logger = logging.getLogger(__name__)


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
                    logger.warning(f"{industry}行业缺少{f}字段，跳过该行业")
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
        df = wc.get(query = query)
        
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
    
    def analyze_sector_risk(self, period_days=30, min_stocks_per_sector=5) -> List[Dict[str, Any]]:
        """
        分析各板块风险，返回风险排名列表。
        
        Args:
            period_days: 分析周期天数（默认30天，建议范围：7-365）
            min_stocks_per_sector: 板块最小股票数量（少于该数量的板块不参与分析，默认5）
        
        Returns:
            List[Dict]: 板块风险分析结果，包含：
                - industry: 行业名称
                - risk_score: 风险得分（越高风险越大）
                - volatility: 波动率
                - avg_change: 平均涨跌幅
                - stock_count: 股票数量
                - max_drawdown: 最大回撤
        
        Raises:
            ValueError: 如果tushare_token未设置或参数无效
        """
        if not self.tushare_token:
            raise ValueError("请在StockSelector初始化时传入tushare_token参数")
        
        # 参数验证
        if period_days < 1 or period_days > 365:
            raise ValueError(f"period_days必须在1-365之间，当前值: {period_days}")
        if min_stocks_per_sector < 1:
            raise ValueError(f"min_stocks_per_sector必须大于0，当前值: {min_stocks_per_sector}")
        
        try:
            pro = ts.pro_api(self.tushare_token)
            today = pd.Timestamp.today().strftime('%Y%m%d')
            start = (pd.Timestamp.today() - pd.Timedelta(days=period_days)).strftime('%Y%m%d')
            
            # 获取股票基础信息（行业分类）
            stock_info = pro.stock_basic(exchange='', list_status='L', fields='ts_code,industry')
            stock_info = stock_info[stock_info['industry'].notna()]  # 过滤掉行业为空的股票
            
            # 获取历史行情数据
            daily = pro.daily(start_date=start, end_date=today)
            if daily.empty:
                return []
            
            # 合并行业信息
            daily = daily.merge(stock_info[['ts_code', 'industry']], on='ts_code', how='left')
            daily = daily[daily['industry'].notna()]  # 过滤掉行业为空的记录
            
            # 按行业分组计算风险指标
            sector_metrics = []
            for industry, group in daily.groupby('industry'):
                if len(group['ts_code'].unique()) < min_stocks_per_sector:
                    continue  # 跳过股票数量太少的板块
                
                # 计算每个股票在该周期内的涨跌幅
                stock_changes = []
                for ts_code in group['ts_code'].unique():
                    stock_data = group[group['ts_code'] == ts_code].sort_values('trade_date')
                    if len(stock_data) < 2:
                        continue
                    first_close = stock_data.iloc[0]['close']
                    last_close = stock_data.iloc[-1]['close']
                    change_pct = (last_close - first_close) / first_close * 100
                    stock_changes.append(change_pct)
                
                if not stock_changes:
                    continue
                
                # 计算风险指标
                volatility = float(np.std(stock_changes))  # 波动率（标准差）
                avg_change = float(np.mean(stock_changes))  # 平均涨跌幅
                max_drawdown = float(min(stock_changes))  # 最大回撤（最小涨跌幅）
                stock_count = len(group['ts_code'].unique())
                
                # 风险得分计算（综合考虑波动率、回撤、平均涨跌幅）
                # 波动率越高、回撤越大、平均涨跌幅越负，风险得分越高
                risk_score = (
                    volatility * 0.4 +  # 波动率权重40%
                    abs(max_drawdown) * 0.3 +  # 最大回撤权重30%
                    max(0, -avg_change) * 0.3  # 负平均涨跌幅权重30%
                )
                
                sector_metrics.append({
                    'industry': industry,
                    'risk_score': round(risk_score, 2),
                    'volatility': round(volatility, 2),
                    'avg_change': round(avg_change, 2),
                    'stock_count': stock_count,
                    'max_drawdown': round(max_drawdown, 2)
                })
            
            # 按风险得分降序排序（风险高的在前）
            sector_metrics.sort(key=lambda x: x['risk_score'], reverse=True)
            return sector_metrics
            
        except Exception as e:
            logger.error(f"板块风险分析失败: {e}", exc_info=True)
            return []
    
    def find_historical_low_stocks(
        self, 
        period_days: int = 250, 
        percentile: float = 0.1,
        min_price: float = 1.0,
        limit: int = 50,
        max_stocks_to_process: int = 500
    ) -> List[Dict[str, Any]]:
        """
        找出处于历史低位的股票。
        
        Args:
            period_days: 历史数据周期（默认250个交易日，约1年，建议范围：60-1000）
            percentile: 历史分位数阈值（0.1表示当前价格处于历史10%低位，范围：0.0-1.0）
            min_price: 最低价格过滤（过滤掉价格过低的股票，默认1.0元）
            limit: 返回结果数量限制（默认50，建议范围：1-200）
            max_stocks_to_process: 最大处理股票数量（避免API限制，默认500）
        
        Returns:
            List[Dict]: 历史低位股票列表，包含：
                - ts_code: 股票代码
                - name: 股票名称
                - current_price: 当前价格
                - historical_low: 历史最低价
                - historical_high: 历史最高价
                - price_percentile: 价格历史分位数（0-1，越小表示越接近历史低位）
                - distance_from_low: 距离历史最低价的百分比
        
        Raises:
            ValueError: 如果tushare_token未设置或参数无效
        """
        if not self.tushare_token:
            raise ValueError("请在StockSelector初始化时传入tushare_token参数")
        
        # 参数验证
        if period_days < 60 or period_days > 1000:
            raise ValueError(f"period_days必须在60-1000之间，当前值: {period_days}")
        if not 0.0 <= percentile <= 1.0:
            raise ValueError(f"percentile必须在0.0-1.0之间，当前值: {percentile}")
        if min_price < 0:
            raise ValueError(f"min_price必须大于等于0，当前值: {min_price}")
        if limit < 1 or limit > 200:
            raise ValueError(f"limit必须在1-200之间，当前值: {limit}")
        if max_stocks_to_process < 1:
            raise ValueError(f"max_stocks_to_process必须大于0，当前值: {max_stocks_to_process}")
        
        try:
            pro = ts.pro_api(self.tushare_token)
            today = pd.Timestamp.today().strftime('%Y%m%d')
            start = (pd.Timestamp.today() - pd.Timedelta(days=period_days * 2)).strftime('%Y%m%d')  # 多取一些数据
            
            # 获取股票基础信息
            stock_info = pro.stock_basic(exchange='', list_status='L', fields='ts_code,name,industry')
            stock_info = stock_info[~stock_info['ts_code'].str.endswith('.BJ')]  # 排除北交所
            
            # 获取最新交易日数据
            latest_daily = pro.daily(trade_date=today)
            if latest_daily.empty:
                # 如果当天没有数据，获取最近一个交易日
                trade_cal = pro.trade_cal(exchange='SSE', start_date=start, end_date=today)
                trade_cal = trade_cal[trade_cal['is_open'] == 1].sort_values('cal_date', ascending=False)
                if not trade_cal.empty:
                    latest_date = trade_cal.iloc[0]['cal_date']
                    latest_daily = pro.daily(trade_date=latest_date)
            
            if latest_daily.empty:
                return []
            
            # 获取历史数据
            hist_daily = pro.daily(start_date=start, end_date=today)
            if hist_daily.empty:
                return []
            
            results = []
            processed_count = 0
            
            # 按股票分组分析
            for ts_code in stock_info['ts_code'].head(max_stocks_to_process):
                try:
                    # 获取该股票的最新价格
                    latest = latest_daily[latest_daily['ts_code'] == ts_code]
                    if latest.empty:
                        continue
                    current_price = float(latest.iloc[0]['close'])
                    
                    if current_price < min_price:
                        continue  # 过滤价格过低的股票
                    
                    # 获取该股票的历史数据
                    stock_hist = hist_daily[hist_daily['ts_code'] == ts_code].sort_values('trade_date')
                    if len(stock_hist) < 60:  # 至少需要60个交易日的数据
                        continue
                    
                    # 计算历史价格分位数
                    close_prices = stock_hist['close'].values
                    historical_low = float(np.min(close_prices))
                    historical_high = float(np.max(close_prices))
                    
                    # 计算当前价格在历史价格中的分位数
                    price_percentile = float(np.sum(close_prices <= current_price) / len(close_prices))
                    
                    # 只保留处于历史低位的股票（分位数小于等于阈值）
                    if price_percentile <= percentile:
                        distance_from_low = ((current_price - historical_low) / historical_low * 100) if historical_low > 0 else 0
                        
                        stock_name = stock_info[stock_info['ts_code'] == ts_code]['name'].iloc[0] if not stock_info[stock_info['ts_code'] == ts_code].empty else ts_code
                        
                        results.append({
                            'ts_code': ts_code,
                            'name': stock_name,
                            'current_price': round(current_price, 2),
                            'historical_low': round(historical_low, 2),
                            'historical_high': round(historical_high, 2),
                            'price_percentile': round(price_percentile, 4),
                            'distance_from_low': round(distance_from_low, 2)
                        })
                    
                    processed_count += 1
                    if processed_count % 100 == 0:
                        logger.info(f"历史低位分析进度: 已处理 {processed_count} 只股票...")
                    
                except Exception as e:
                    logger.debug(f"处理股票 {ts_code} 时出错: {e}，跳过")
                    continue  # 跳过出错的股票
            
            # 按价格分位数升序排序（最接近历史低位的在前）
            results.sort(key=lambda x: x['price_percentile'])
            return results[:limit]
            
        except Exception as e:
            logger.error(f"历史低位分析失败: {e}", exc_info=True)
            return [] 