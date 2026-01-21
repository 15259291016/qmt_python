#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新浪财经/同花顺买卖点爬虫
支持两种方案：
1. 直接爬取新浪财经网页的买卖点数据
2. 自行计算买卖点指标（基于技术分析）

作者: AI Assistant
创建时间: 2025-01-26
版本: 1.0
"""

import requests
import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
import json
import logging
import time
from bs4 import BeautifulSoup
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StockCodeConverter:
    """股票代码转换工具类"""
    
    @staticmethod
    def to_sina_code(stock_code: str) -> str:
        """
        将标准股票代码转换为新浪财经格式
        
        Args:
            stock_code: 股票代码，如 '000001' 或 '600000' 或 '000001.SZ'
        
        Returns:
            新浪财经格式代码，如 'sz000001' 或 'sh600000'
        """
        # 移除可能的交易所后缀
        code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.sh', '').replace('.sz', '')
        
        # 判断是上海还是深圳
        if code.startswith('6'):
            return f'sh{code}'
        elif code.startswith('0') or code.startswith('3'):
            return f'sz{code}'
        else:
            raise ValueError(f"无法识别股票代码: {stock_code}")
    
    @staticmethod
    def to_tushare_code(stock_code: str) -> str:
        """
        将股票代码转换为Tushare格式
        
        Args:
            stock_code: 股票代码
        
        Returns:
            Tushare格式代码，如 '000001.SZ' 或 '600000.SH'
        """
        code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.sh', '').replace('.sz', '')
        
        if code.startswith('6'):
            return f'{code}.SH'
        elif code.startswith('0') or code.startswith('3'):
            return f'{code}.SZ'
        else:
            raise ValueError(f"无法识别股票代码: {stock_code}")


class SinaFinanceCrawler:
    """
    新浪财经买卖点爬虫（方案1：直接爬取）
    
    注意：新浪财经的买卖点基于葛兰碧八大法则（Granville's Eight Rules）
    这是一种经典的均线交易策略，通过分析股价与均线的关系来确定买卖点
    
    参考文档：
    - B1-B4: 四个买入点（均线突破、回撤不破、跌破后反弹、急跌反弹）
    - S1-S4: 四个卖出点（均线跌破、反弹不破、突破后回落、急涨回落）
    """
    
    def __init__(self):
        self.base_url = "https://finance.sina.com.cn/realstock/company"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Referer': 'https://finance.sina.com.cn/'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_stock_url(self, stock_code: str) -> str:
        """
        构建股票详情页URL
        
        Args:
            stock_code: 股票代码
        
        Returns:
            完整的URL
        """
        sina_code = StockCodeConverter.to_sina_code(stock_code)
        # 新浪财经URL格式: https://finance.sina.com.cn/realstock/company/sh603444/nc.shtml
        return f"{self.base_url}/{sina_code}/nc.shtml"
    
    def crawl_stock_page(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        爬取股票页面，尝试提取买卖点数据
        
        Args:
            stock_code: 股票代码
        
        Returns:
            包含买卖点信息的字典，如果失败返回None
        """
        try:
            url = self.get_stock_url(stock_code)
            logger.info(f"正在爬取: {url}")
            
            response = self.session.get(url, timeout=10)
            response.encoding = 'utf-8'
            
            if response.status_code != 200:
                logger.error(f"请求失败，状态码: {response.status_code}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 尝试从页面中提取买卖点数据
            # 注意：新浪财经的买卖点数据可能是通过JavaScript动态加载的
            # 这里提供一个基础框架，实际需要根据页面结构调整
            
            result = {
                'stock_code': stock_code,
                'url': url,
                'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'buy_points': [],
                'sell_points': []
            }
            
            # 方法1: 尝试查找包含买卖点的script标签
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and ('buy' in script.string.lower() or 'sell' in script.string.lower()):
                    # 尝试解析JSON数据
                    try:
                        # 查找可能的JSON数据
                        json_match = re.search(r'\{.*"buy.*"sell.*\}', script.string, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group())
                            if 'buy_points' in data:
                                result['buy_points'] = data['buy_points']
                            if 'sell_points' in data:
                                result['sell_points'] = data['sell_points']
                    except:
                        pass
            
            # 方法2: 尝试从API获取（需要分析网络请求）
            # 新浪财经可能通过API接口提供买卖点数据
            # 可以通过浏览器开发者工具分析Network请求找到API地址
            
            logger.info(f"爬取完成: {stock_code}")
            return result
            
        except Exception as e:
            logger.error(f"爬取失败 {stock_code}: {e}")
            return None
    
    def crawl_api_data(self, stock_code: str) -> Optional[Dict[str, Any]]:
        """
        尝试通过API接口获取买卖点数据
        注意：需要分析新浪财经的实际API接口
        
        Args:
            stock_code: 股票代码
        
        Returns:
            买卖点数据
        """
        try:
            sina_code = StockCodeConverter.to_sina_code(stock_code)
            
            # 示例API URL（需要根据实际情况调整）
            # 可以通过浏览器开发者工具分析Network请求找到真实API
            api_url = f"https://finance.sina.com.cn/realstock/api/bs/{sina_code}"
            
            response = self.session.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'stock_code': stock_code,
                    'buy_points': data.get('buy_points', []),
                    'sell_points': data.get('sell_points', []),
                    'crawl_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                logger.warning(f"API请求失败: {api_url}")
                return None
                
        except Exception as e:
            logger.error(f"API获取失败 {stock_code}: {e}")
            return None


class BuySellPointCalculator:
    """买卖点计算器（方案2：自行计算）- 优化版"""
    
    def __init__(self, 
                 ma_short: int = 5,
                 ma_mid: int = 10,
                 ma_long: int = 20,
                 ma_trend: int = 60,
                 rsi_period: int = 14,
                 macd_fast: int = 12,
                 macd_slow: int = 26,
                 macd_signal: int = 9,
                 boll_period: int = 20,
                 boll_std: float = 2.0,
                 kdj_period: int = 9,
                 volume_ma_period: int = 5,
                 min_signal_score: float = 2.5,
                 min_days_between_signals: int = 3):
        """
        初始化买卖点计算器（优化版）
        
        Args:
            ma_short: 短期均线周期（默认5）
            ma_mid: 中期均线周期（默认10）
            ma_long: 长期均线周期（默认20）
            ma_trend: 趋势均线周期（默认60，用于判断大趋势）
            rsi_period: RSI周期（默认14）
            macd_fast: MACD快线周期（默认12）
            macd_slow: MACD慢线周期（默认26）
            macd_signal: MACD信号线周期（默认9）
            boll_period: 布林带周期（默认20）
            boll_std: 布林带标准差倍数（默认2.0）
            kdj_period: KDJ周期（默认9）
            volume_ma_period: 成交量均线周期（默认5）
            min_signal_score: 最小信号评分阈值（默认2.5，越高越严格）
            min_days_between_signals: 买卖点之间的最小间隔天数（默认3，避免频繁交易）
        """
        self.ma_short = ma_short
        self.ma_mid = ma_mid
        self.ma_long = ma_long
        self.ma_trend = ma_trend
        self.rsi_period = rsi_period
        self.macd_fast = macd_fast
        self.macd_slow = macd_slow
        self.macd_signal = macd_signal
        self.boll_period = boll_period
        self.boll_std = boll_std
        self.kdj_period = kdj_period
        self.volume_ma_period = volume_ma_period
        self.min_signal_score = min_signal_score
        self.min_days_between_signals = min_days_between_signals
    
    def calculate_ma(self, prices: pd.Series, period: int) -> pd.Series:
        """计算移动平均线"""
        return prices.rolling(window=period).mean()
    
    def calculate_rsi(self, prices: pd.Series, period: int = None) -> pd.Series:
        """计算RSI指标"""
        if period is None:
            period = self.rsi_period
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_macd(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD指标"""
        ema_fast = prices.ewm(span=self.macd_fast, adjust=False).mean()
        ema_slow = prices.ewm(span=self.macd_slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal, adjust=False).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def calculate_bollinger_bands(self, prices: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算布林带"""
        middle = prices.rolling(window=self.boll_period).mean()
        std = prices.rolling(window=self.boll_period).std()
        upper = middle + (std * self.boll_std)
        lower = middle - (std * self.boll_std)
        return upper, middle, lower
    
    def calculate_kdj(self, high: pd.Series, low: pd.Series, close: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算KDJ指标"""
        low_min = low.rolling(window=self.kdj_period).min()
        high_max = high.rolling(window=self.kdj_period).max()
        
        rsv = (close - low_min) / (high_max - low_min) * 100
        
        # K值 = 2/3 * 前K值 + 1/3 * RSV
        k = rsv.ewm(com=2, adjust=False).mean()
        # D值 = 2/3 * 前D值 + 1/3 * K值
        d = k.ewm(com=2, adjust=False).mean()
        # J值 = 3 * K值 - 2 * D值
        j = 3 * k - 2 * d
        
        return k, d, j
    
    def calculate_volume_indicators(self, volume: pd.Series) -> Tuple[pd.Series, pd.Series]:
        """计算成交量指标"""
        volume_ma = volume.rolling(window=self.volume_ma_period).mean()
        volume_ratio = volume / volume_ma  # 量比
        return volume_ma, volume_ratio
    
    def calculate_buy_sell_points(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算买卖点（优化版策略）
        
        策略说明（使用加权评分系统）：
        
        **买入点(B点)评分标准：**
        1. 均线系统（权重1.5）：
           - MA5上穿MA10：+0.5分
           - MA5上穿MA20：+1.0分
           - 价格在MA60上方（趋势确认）：+0.5分
        
        2. MACD指标（权重1.5）：
           - MACD金叉：+1.0分
           - MACD柱状图转正：+0.5分
        
        3. RSI指标（权重1.0）：
           - RSI < 30（超卖）：+0.8分
           - RSI < 40且上升：+0.5分
        
        4. KDJ指标（权重1.0）：
           - K线上穿D线（金叉）：+0.5分
           - J值 < 20（超卖）：+0.5分
        
        5. 布林带（权重1.0）：
           - 价格触及或跌破下轨：+0.8分
           - 价格从下轨反弹：+0.5分
        
        6. 成交量确认（权重1.0）：
           - 量比 > 1.5（放量）：+0.5分
           - 成交量突破均量：+0.5分
        
        **卖出点(S点)评分标准：**
        1. 均线系统（权重1.5）：
           - MA5下穿MA10：+0.5分
           - MA5下穿MA20：+1.0分
           - 价格在MA60下方（趋势确认）：+0.5分
        
        2. MACD指标（权重1.5）：
           - MACD死叉：+1.0分
           - MACD柱状图转负：+0.5分
        
        3. RSI指标（权重1.0）：
           - RSI > 70（超买）：+0.8分
           - RSI > 60且下降：+0.5分
        
        4. KDJ指标（权重1.0）：
           - K线下穿D线（死叉）：+0.5分
           - J值 > 80（超买）：+0.5分
        
        5. 布林带（权重1.0）：
           - 价格触及或突破上轨：+0.8分
           - 价格从上轨回落：+0.5分
        
        6. 成交量确认（权重1.0）：
           - 量比 > 1.5（放量）：+0.5分
        
        **信号过滤：**
        - 最小评分阈值：默认2.5分（可配置）
        - 最小间隔：买卖点之间至少间隔N天（默认3天），避免频繁交易
        
        Args:
            df: 包含 'date', 'open', 'high', 'low', 'close', 'volume' 列的DataFrame
        
        Returns:
            添加了买卖点标记和评分的DataFrame
        """
        min_period = max(self.ma_trend, self.rsi_period, self.macd_slow, self.boll_period, self.kdj_period)
        if df.empty or len(df) < min_period:
            logger.warning(f"数据不足，需要至少{min_period}条数据，当前只有{len(df)}条")
            return df
        
        df = df.copy()
        df['date'] = pd.to_datetime(df['date']) if 'date' in df.columns else df.index
        
        # 计算技术指标
        close_prices = df['close']
        high_prices = df['high']
        low_prices = df['low']
        volume = df['volume']
        
        # 均线系统
        df['ma_short'] = self.calculate_ma(close_prices, self.ma_short)
        df['ma_mid'] = self.calculate_ma(close_prices, self.ma_mid)
        df['ma_long'] = self.calculate_ma(close_prices, self.ma_long)
        df['ma_trend'] = self.calculate_ma(close_prices, self.ma_trend)
        
        # RSI
        df['rsi'] = self.calculate_rsi(close_prices)
        
        # MACD
        macd_line, signal_line, histogram = self.calculate_macd(close_prices)
        df['macd'] = macd_line
        df['macd_signal'] = signal_line
        df['macd_hist'] = histogram
        
        # 布林带
        boll_upper, boll_middle, boll_lower = self.calculate_bollinger_bands(close_prices)
        df['boll_upper'] = boll_upper
        df['boll_middle'] = boll_middle
        df['boll_lower'] = boll_lower
        
        # KDJ
        k, d, j = self.calculate_kdj(high_prices, low_prices, close_prices)
        df['kdj_k'] = k
        df['kdj_d'] = d
        df['kdj_j'] = j
        
        # 成交量指标
        volume_ma, volume_ratio = self.calculate_volume_indicators(volume)
        df['volume_ma'] = volume_ma
        df['volume_ratio'] = volume_ratio
        
        # 初始化买卖点标记
        df['buy_point'] = 0
        df['sell_point'] = 0
        df['buy_score'] = 0.0
        df['sell_score'] = 0.0
        df['signal'] = ''
        df['signal_strength'] = ''  # 信号强度：弱/中/强
        
        last_signal_idx = -self.min_days_between_signals - 1  # 上次信号位置
        
        # 计算买卖点（使用加权评分）
        for i in range(min_period, len(df)):
            # 跳过距离上次信号太近的日期
            if i - last_signal_idx < self.min_days_between_signals:
                continue
            
            buy_score = 0.0
            sell_score = 0.0
            
            # ========== 买入信号评分 ==========
            
            # 1. 均线系统（权重1.5）
            if not pd.isna(df.iloc[i]['ma_short']) and not pd.isna(df.iloc[i]['ma_mid']):
                # MA5上穿MA10
                if (df.iloc[i-1]['ma_short'] < df.iloc[i-1]['ma_mid'] and 
                    df.iloc[i]['ma_short'] > df.iloc[i]['ma_mid']):
                    buy_score += 0.5
            
            if not pd.isna(df.iloc[i]['ma_short']) and not pd.isna(df.iloc[i]['ma_long']):
                # MA5上穿MA20
                if (df.iloc[i-1]['ma_short'] < df.iloc[i-1]['ma_long'] and 
                    df.iloc[i]['ma_short'] > df.iloc[i]['ma_long']):
                    buy_score += 1.0
            
            # 趋势确认：价格在MA60上方
            if not pd.isna(df.iloc[i]['ma_trend']):
                if df.iloc[i]['close'] > df.iloc[i]['ma_trend']:
                    buy_score += 0.5
            
            # 2. MACD指标（权重1.5）
            if (not pd.isna(df.iloc[i-1]['macd']) and not pd.isna(df.iloc[i-1]['macd_signal']) and
                not pd.isna(df.iloc[i]['macd']) and not pd.isna(df.iloc[i]['macd_signal'])):
                # MACD金叉
                if (df.iloc[i-1]['macd'] < df.iloc[i-1]['macd_signal'] and 
                    df.iloc[i]['macd'] > df.iloc[i]['macd_signal']):
                    buy_score += 1.0
                
                # MACD柱状图转正
                if (not pd.isna(df.iloc[i-1]['macd_hist']) and not pd.isna(df.iloc[i]['macd_hist'])):
                    if df.iloc[i-1]['macd_hist'] < 0 and df.iloc[i]['macd_hist'] > 0:
                        buy_score += 0.5
            
            # 3. RSI指标（权重1.0）
            if not pd.isna(df.iloc[i]['rsi']):
                rsi_val = df.iloc[i]['rsi']
                if rsi_val < 30:  # 超卖
                    buy_score += 0.8
                elif rsi_val < 40 and i > 0 and not pd.isna(df.iloc[i-1]['rsi']):
                    if df.iloc[i]['rsi'] > df.iloc[i-1]['rsi']:  # RSI上升
                        buy_score += 0.5
            
            # 4. KDJ指标（权重1.0）
            if (not pd.isna(df.iloc[i]['kdj_k']) and not pd.isna(df.iloc[i]['kdj_d']) and
                not pd.isna(df.iloc[i-1]['kdj_k']) and not pd.isna(df.iloc[i-1]['kdj_d'])):
                # K线上穿D线
                if (df.iloc[i-1]['kdj_k'] < df.iloc[i-1]['kdj_d'] and 
                    df.iloc[i]['kdj_k'] > df.iloc[i]['kdj_d']):
                    buy_score += 0.5
                
                # J值超卖
                if not pd.isna(df.iloc[i]['kdj_j']) and df.iloc[i]['kdj_j'] < 20:
                    buy_score += 0.5
            
            # 5. 布林带（权重1.0）
            if not pd.isna(df.iloc[i]['boll_lower']):
                # 价格触及或跌破下轨
                if df.iloc[i]['close'] <= df.iloc[i]['boll_lower']:
                    buy_score += 0.8
                # 价格从下轨反弹
                elif i > 0 and df.iloc[i-1]['close'] <= df.iloc[i-1]['boll_lower']:
                    if df.iloc[i]['close'] > df.iloc[i-1]['close']:
                        buy_score += 0.5
            
            # 6. 成交量确认（权重1.0）
            if not pd.isna(df.iloc[i]['volume_ratio']):
                if df.iloc[i]['volume_ratio'] > 1.5:  # 放量
                    buy_score += 0.5
                if df.iloc[i]['volume'] > df.iloc[i]['volume_ma']:
                    buy_score += 0.5
            
            # ========== 卖出信号评分 ==========
            
            # 1. 均线系统（权重1.5）
            if not pd.isna(df.iloc[i]['ma_short']) and not pd.isna(df.iloc[i]['ma_mid']):
                # MA5下穿MA10
                if (df.iloc[i-1]['ma_short'] > df.iloc[i-1]['ma_mid'] and 
                    df.iloc[i]['ma_short'] < df.iloc[i]['ma_mid']):
                    sell_score += 0.5
            
            if not pd.isna(df.iloc[i]['ma_short']) and not pd.isna(df.iloc[i]['ma_long']):
                # MA5下穿MA20
                if (df.iloc[i-1]['ma_short'] > df.iloc[i-1]['ma_long'] and 
                    df.iloc[i]['ma_short'] < df.iloc[i]['ma_long']):
                    sell_score += 1.0
            
            # 趋势确认：价格在MA60下方
            if not pd.isna(df.iloc[i]['ma_trend']):
                if df.iloc[i]['close'] < df.iloc[i]['ma_trend']:
                    sell_score += 0.5
            
            # 2. MACD指标（权重1.5）
            if (not pd.isna(df.iloc[i-1]['macd']) and not pd.isna(df.iloc[i-1]['macd_signal']) and
                not pd.isna(df.iloc[i]['macd']) and not pd.isna(df.iloc[i]['macd_signal'])):
                # MACD死叉
                if (df.iloc[i-1]['macd'] > df.iloc[i-1]['macd_signal'] and 
                    df.iloc[i]['macd'] < df.iloc[i]['macd_signal']):
                    sell_score += 1.0
                
                # MACD柱状图转负
                if (not pd.isna(df.iloc[i-1]['macd_hist']) and not pd.isna(df.iloc[i]['macd_hist'])):
                    if df.iloc[i-1]['macd_hist'] > 0 and df.iloc[i]['macd_hist'] < 0:
                        sell_score += 0.5
            
            # 3. RSI指标（权重1.0）
            if not pd.isna(df.iloc[i]['rsi']):
                rsi_val = df.iloc[i]['rsi']
                if rsi_val > 70:  # 超买
                    sell_score += 0.8
                elif rsi_val > 60 and i > 0 and not pd.isna(df.iloc[i-1]['rsi']):
                    if df.iloc[i]['rsi'] < df.iloc[i-1]['rsi']:  # RSI下降
                        sell_score += 0.5
            
            # 4. KDJ指标（权重1.0）
            if (not pd.isna(df.iloc[i]['kdj_k']) and not pd.isna(df.iloc[i]['kdj_d']) and
                not pd.isna(df.iloc[i-1]['kdj_k']) and not pd.isna(df.iloc[i-1]['kdj_d'])):
                # K线下穿D线
                if (df.iloc[i-1]['kdj_k'] > df.iloc[i-1]['kdj_d'] and 
                    df.iloc[i]['kdj_k'] < df.iloc[i]['kdj_d']):
                    sell_score += 0.5
                
                # J值超买
                if not pd.isna(df.iloc[i]['kdj_j']) and df.iloc[i]['kdj_j'] > 80:
                    sell_score += 0.5
            
            # 5. 布林带（权重1.0）
            if not pd.isna(df.iloc[i]['boll_upper']):
                # 价格触及或突破上轨
                if df.iloc[i]['close'] >= df.iloc[i]['boll_upper']:
                    sell_score += 0.8
                # 价格从上轨回落
                elif i > 0 and df.iloc[i-1]['close'] >= df.iloc[i-1]['boll_upper']:
                    if df.iloc[i]['close'] < df.iloc[i-1]['close']:
                        sell_score += 0.5
            
            # 6. 成交量确认（权重1.0）
            if not pd.isna(df.iloc[i]['volume_ratio']):
                if df.iloc[i]['volume_ratio'] > 1.5:  # 放量
                    sell_score += 0.5
            
            # 保存评分
            df.iloc[i, df.columns.get_loc('buy_score')] = buy_score
            df.iloc[i, df.columns.get_loc('sell_score')] = sell_score
            
            # 判断买卖点（使用评分阈值）
            if buy_score >= self.min_signal_score:
                df.iloc[i, df.columns.get_loc('buy_point')] = 1
                df.iloc[i, df.columns.get_loc('signal')] = 'B'
                # 信号强度
                if buy_score >= 4.0:
                    df.iloc[i, df.columns.get_loc('signal_strength')] = '强'
                elif buy_score >= 3.0:
                    df.iloc[i, df.columns.get_loc('signal_strength')] = '中'
                else:
                    df.iloc[i, df.columns.get_loc('signal_strength')] = '弱'
                last_signal_idx = i
            elif sell_score >= self.min_signal_score:
                df.iloc[i, df.columns.get_loc('sell_point')] = 1
                df.iloc[i, df.columns.get_loc('signal')] = 'S'
                # 信号强度
                if sell_score >= 4.0:
                    df.iloc[i, df.columns.get_loc('signal_strength')] = '强'
                elif sell_score >= 3.0:
                    df.iloc[i, df.columns.get_loc('signal_strength')] = '中'
                else:
                    df.iloc[i, df.columns.get_loc('signal_strength')] = '弱'
                last_signal_idx = i
        
        return df
    
    def get_buy_sell_points_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取买卖点摘要信息（优化版，包含评分和强度）
        
        Args:
            df: 包含买卖点标记的DataFrame
        
        Returns:
            买卖点摘要字典
        """
        buy_points = df[df['buy_point'] == 1].copy()
        sell_points = df[df['sell_point'] == 1].copy()
        
        return {
            'total_buy_points': len(buy_points),
            'total_sell_points': len(sell_points),
            'avg_buy_score': float(buy_points['buy_score'].mean()) if len(buy_points) > 0 else 0.0,
            'avg_sell_score': float(sell_points['sell_score'].mean()) if len(sell_points) > 0 else 0.0,
            'buy_points': [
                {
                    'date': row['date'].strftime('%Y-%m-%d') if 'date' in row else str(row.name),
                    'price': float(row['close']),
                    'volume': float(row['volume']) if 'volume' in row else 0,
                    'score': float(row['buy_score']) if 'buy_score' in row else 0.0,
                    'strength': str(row['signal_strength']) if 'signal_strength' in row else '',
                    'rsi': float(row['rsi']) if 'rsi' in row and not pd.isna(row['rsi']) else None,
                    'macd_hist': float(row['macd_hist']) if 'macd_hist' in row and not pd.isna(row['macd_hist']) else None
                }
                for _, row in buy_points.iterrows()
            ],
            'sell_points': [
                {
                    'date': row['date'].strftime('%Y-%m-%d') if 'date' in row else str(row.name),
                    'price': float(row['close']),
                    'volume': float(row['volume']) if 'volume' in row else 0,
                    'score': float(row['sell_score']) if 'sell_score' in row else 0.0,
                    'strength': str(row['signal_strength']) if 'signal_strength' in row else '',
                    'rsi': float(row['rsi']) if 'rsi' in row and not pd.isna(row['rsi']) else None,
                    'macd_hist': float(row['macd_hist']) if 'macd_hist' in row and not pd.isna(row['macd_hist']) else None
                }
                for _, row in sell_points.iterrows()
            ]
        }


class StockDataFetcher:
    """股票数据获取器（用于方案2）"""
    
    def __init__(self, tushare_token: Optional[str] = None):
        """
        初始化数据获取器
        
        Args:
            tushare_token: Tushare API token（可选）
        """
        self.tushare_token = tushare_token
        self.pro = None
        
        if tushare_token:
            try:
                import tushare as ts
                ts.set_token(tushare_token)
                self.pro = ts.pro_api()
                logger.info("Tushare初始化成功")
            except Exception as e:
                logger.warning(f"Tushare初始化失败: {e}")
    
    def fetch_from_tushare(self, stock_code: str, days: int = 250) -> Optional[pd.DataFrame]:
        """
        从Tushare获取股票历史数据
        
        Args:
            stock_code: 股票代码
            days: 获取最近多少天的数据
        
        Returns:
            包含股票数据的DataFrame
        """
        if not self.pro:
            logger.error("Tushare未初始化")
            return None
        
        try:
            tushare_code = StockCodeConverter.to_tushare_code(stock_code)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            df = self.pro.daily(ts_code=tushare_code, start_date=start_date, end_date=end_date)
            
            if df.empty:
                logger.warning(f"未获取到 {stock_code} 的数据")
                return None
            
            # 重命名列
            df = df.rename(columns={
                'trade_date': 'date',
                'vol': 'volume'
            })
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            df = df.sort_values('date').reset_index(drop=True)
            
            logger.info(f"成功获取 {stock_code} 的 {len(df)} 条数据")
            return df
            
        except Exception as e:
            logger.error(f"获取Tushare数据失败 {stock_code}: {e}")
            return None
    
    def fetch_from_akshare(self, stock_code: str, days: int = 250) -> Optional[pd.DataFrame]:
        """
        从AKShare获取股票历史数据（备用方案）
        
        Args:
            stock_code: 股票代码
            days: 获取最近多少天的数据
        
        Returns:
            包含股票数据的DataFrame
        """
        try:
            import akshare as ak
            
            # AKShare代码格式：'000001' 或 '600000'
            code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.sh', '').replace('.sz', '')
            
            # 获取历史数据
            df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="")
            
            if df.empty:
                logger.warning(f"未获取到 {stock_code} 的数据")
                return None
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # 只保留最近days天的数据
            if len(df) > days:
                df = df.tail(days).reset_index(drop=True)
            
            logger.info(f"成功获取 {stock_code} 的 {len(df)} 条数据（AKShare）")
            return df
            
        except Exception as e:
            logger.error(f"获取AKShare数据失败 {stock_code}: {e}")
            return None


class BuySellPointCrawler:
    """买卖点爬虫主类（整合两种方案）"""
    
    def __init__(self, 
                 method: str = 'calculate',
                 tushare_token: Optional[str] = None):
        """
        初始化爬虫
        
        Args:
            method: 方法选择，'crawl'（爬取新浪财经）或 'calculate'（自行计算）
            tushare_token: Tushare API token（用于方案2）
        """
        self.method = method
        self.sina_crawler = SinaFinanceCrawler()
        self.calculator = BuySellPointCalculator()
        self.data_fetcher = StockDataFetcher(tushare_token)
    
    def get_buy_sell_points(self, stock_code: str, days: int = 250) -> Dict[str, Any]:
        """
        获取买卖点数据
        
        Args:
            stock_code: 股票代码
            days: 数据天数（仅用于方案2）
        
        Returns:
            买卖点数据字典
        """
        if self.method == 'crawl':
            # 方案1: 直接爬取新浪财经
            result = self.sina_crawler.crawl_stock_page(stock_code)
            if not result or (not result.get('buy_points') and not result.get('sell_points')):
                # 如果网页爬取失败，尝试API
                result = self.sina_crawler.crawl_api_data(stock_code)
            return result or {}
        
        else:
            # 方案2: 自行计算
            # 获取历史数据
            df = self.data_fetcher.fetch_from_tushare(stock_code, days)
            if df is None or df.empty:
                # 尝试使用AKShare
                df = self.data_fetcher.fetch_from_akshare(stock_code, days)
            
            if df is None or df.empty:
                return {
                    'stock_code': stock_code,
                    'error': '无法获取股票数据'
                }
            
            # 计算买卖点
            df_with_signals = self.calculator.calculate_buy_sell_points(df)
            summary = self.calculator.get_buy_sell_points_summary(df_with_signals)
            
            return {
                'stock_code': stock_code,
                'method': 'calculate',
                'calculate_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                **summary,
                'data': df_with_signals.to_dict('records') if len(df_with_signals) < 1000 else None  # 避免数据过大
            }
    
    def save_to_csv(self, data: Dict[str, Any], filename: Optional[str] = None):
        """
        保存买卖点数据到CSV文件
        
        Args:
            data: 买卖点数据字典
            filename: 文件名（可选）
        """
        if filename is None:
            stock_code = data.get('stock_code', 'unknown')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"买卖点_{stock_code}_{timestamp}.csv"
        
        if 'data' in data and data['data']:
            # 如果有完整数据，保存完整数据
            df = pd.DataFrame(data['data'])
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            logger.info(f"数据已保存到: {filename}")
        else:
            # 否则保存摘要数据
            buy_df = pd.DataFrame(data.get('buy_points', []))
            sell_df = pd.DataFrame(data.get('sell_points', []))
            
            if not buy_df.empty or not sell_df.empty:
                with pd.ExcelWriter(filename.replace('.csv', '.xlsx'), engine='openpyxl') as writer:
                    if not buy_df.empty:
                        buy_df.to_excel(writer, sheet_name='买入点', index=False)
                    if not sell_df.empty:
                        sell_df.to_excel(writer, sheet_name='卖出点', index=False)
                logger.info(f"数据已保存到: {filename.replace('.csv', '.xlsx')}")


def main():
    """主函数 - 示例用法"""
    import os
    from dotenv import load_dotenv
    
    # 加载环境变量
    load_dotenv()
    tushare_token = os.getenv('TUSHARE_TOKEN')
    
    # 示例：获取股票买卖点
    stock_code = '603444'  # 吉比特
    
    print("=" * 60)
    print("买卖点爬虫示例")
    print("=" * 60)
    
    # 方案1: 直接爬取新浪财经（可能不稳定）
    print("\n【方案1】直接爬取新浪财经数据")
    print("-" * 60)
    crawler_crawl = BuySellPointCrawler(method='crawl', tushare_token=tushare_token)
    result_crawl = crawler_crawl.get_buy_sell_points(stock_code)
    print(f"爬取结果: {json.dumps(result_crawl, ensure_ascii=False, indent=2)}")
    
    # 方案2: 自行计算（推荐）
    print("\n【方案2】自行计算买卖点指标")
    print("-" * 60)
    crawler_calc = BuySellPointCrawler(method='calculate', tushare_token=tushare_token)
    result_calc = crawler_calc.get_buy_sell_points(stock_code, days=250)
    
    if 'error' not in result_calc:
        print(f"股票代码: {result_calc['stock_code']}")
        print(f"买入点数量: {result_calc['total_buy_points']}")
        print(f"卖出点数量: {result_calc['total_sell_points']}")
        print(f"\n最近5个买入点:")
        for point in result_calc['buy_points'][-5:]:
            print(f"  日期: {point['date']}, 价格: {point['price']:.2f}")
        print(f"\n最近5个卖出点:")
        for point in result_calc['sell_points'][-5:]:
            print(f"  日期: {point['date']}, 价格: {point['price']:.2f}")
        
        # 保存数据
        crawler_calc.save_to_csv(result_calc)
    else:
        print(f"错误: {result_calc['error']}")


if __name__ == '__main__':
    main()
