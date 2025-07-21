import asyncio
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import talib
import tushare as ts

from xtquant.xttrader import XtQuantTrader
from xtquant.xttype import StockAccount
from ..model.position_model import Position, PositionType
from .position_analyzer import PositionAnalyzer

class XtQuantPositionManager:
    """XtQuant持仓管理器"""
    
    def __init__(self, tushare_token: str, xt_trader: Optional[XtQuantTrader] = None):
        self.pro = ts.pro_api(tushare_token)
        self.xt_trader = xt_trader
        self.analyzer = PositionAnalyzer(tushare_token)
        
    async def get_xtquant_positions(self, account_id: str) -> List[Dict]:
        """从XtQuant获取持仓数据"""
        try:
            if not self.xt_trader:
                print("警告: XtQuant交易器未初始化，返回模拟数据")
                return await self.get_mock_positions()
            
            # 查询持仓
            positions = self.xt_trader.query_stock_positions(account_id)
            
            if not positions:
                print(f"账户 {account_id} 没有持仓")
                return []
            
            # 转换为标准格式
            position_data = []
            for pos in positions:
                # 获取当前价格
                current_price = await self.get_current_price(pos.stock_code)
                
                position_data.append({
                    "symbol": pos.stock_code,
                    "volume": pos.volume,
                    "available_volume": getattr(pos, 'enable_amount', pos.volume),
                    "avg_price": pos.avg_price,
                    "current_price": current_price
                })
            
            return position_data
            
        except Exception as e:
            print(f"获取XtQuant持仓失败: {e}")
            return await self.get_mock_positions()
    
    async def get_mock_positions(self) -> List[Dict]:
        """获取模拟持仓数据"""
        return [
            {
                "symbol": "000001.SZ",
                "volume": 1000,
                "available_volume": 1000,
                "avg_price": 15.50,
                "current_price": 16.20
            },
            {
                "symbol": "000002.SZ", 
                "volume": 500,
                "available_volume": 500,
                "avg_price": 25.80,
                "current_price": 24.50
            },
            {
                "symbol": "600519.SH",
                "volume": 200,
                "available_volume": 200,
                "avg_price": 1800.00,
                "current_price": 1850.00
            }
        ]
    
    async def get_current_price(self, symbol: str) -> float:
        """获取当前价格"""
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: self.pro.daily(ts_code=symbol, limit=1))
            if not df.empty:
                return float(df['close'].iloc[0])
            else:
                return 0.0
        except Exception as e:
            print(f"获取 {symbol} 价格失败: {e}")
            return 0.0
    
    async def get_historical_data(self, symbol: str, days: int = 60) -> pd.DataFrame:
        """获取历史数据用于技术分析"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, lambda: self.pro.daily(ts_code=symbol, start_date=start_date, end_date=end_date)
            )
            
            if df.empty:
                return pd.DataFrame()
            
            # 按日期排序
            df = df.sort_values('trade_date')
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)
            
            return df
            
        except Exception as e:
            print(f"获取 {symbol} 历史数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算技术指标"""
        if df.empty or len(df) < 20:
            return {}
        
        try:
            close_prices = df['close'].values.astype(np.float64)
            high_prices = df['high'].values.astype(np.float64)
            low_prices = df['low'].values.astype(np.float64)
            volume = df['vol'].values.astype(np.float64)
            
            indicators = {}
            
            # 移动平均线
            indicators['ma5'] = float(talib.SMA(close_prices, timeperiod=5)[-1])
            indicators['ma10'] = float(talib.SMA(close_prices, timeperiod=10)[-1])
            indicators['ma20'] = float(talib.SMA(close_prices, timeperiod=20)[-1])
            indicators['ma60'] = float(talib.SMA(close_prices, timeperiod=60)[-1])
            
            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close_prices)
            indicators['macd'] = float(macd[-1])
            indicators['macd_signal'] = float(macd_signal[-1])
            indicators['macd_hist'] = float(macd_hist[-1])
            
            # RSI
            indicators['rsi'] = float(talib.RSI(close_prices, timeperiod=14)[-1])
            
            # 布林带
            bb_upper, bb_middle, bb_lower = talib.BBANDS(close_prices)
            indicators['bb_upper'] = float(bb_upper[-1])
            indicators['bb_middle'] = float(bb_middle[-1])
            indicators['bb_lower'] = float(bb_lower[-1])
            
            # KDJ
            k, d = talib.STOCH(high_prices, low_prices, close_prices)
            j = 3 * k - 2 * d
            indicators['kdj_k'] = float(k[-1])
            indicators['kdj_d'] = float(d[-1])
            indicators['kdj_j'] = float(j[-1])
            
            # 成交量指标
            indicators['volume_ma5'] = float(talib.SMA(volume, timeperiod=5)[-1])
            indicators['volume_ratio'] = float(volume[-1] / indicators['volume_ma5'])
            
            # 价格位置
            current_price = float(close_prices[-1])
            indicators['price_position'] = float((current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1]))
            
            return indicators
            
        except Exception as e:
            print(f"计算技术指标失败: {e}")
            return {}
    
    def generate_trading_signals(self, indicators: Dict[str, Any], current_price: float, avg_price: float) -> Dict[str, Any]:
        """生成交易信号"""
        signals = {
            'action': 'hold',  # buy, sell, hold
            'confidence': 0.0,
            'reasons': [],
            'target_price': 0.0,
            'stop_loss': 0.0
        }
        
        if not indicators:
            return signals
        
        score = 0.0
        reasons = []
        
        # 移动平均线信号
        ma5 = indicators.get('ma5', 0)
        ma10 = indicators.get('ma10', 0)
        ma20 = indicators.get('ma20', 0)
        ma60 = indicators.get('ma60', 0)
        
        if current_price > ma5 > ma10 > ma20:
            score += 2.0
            reasons.append("均线多头排列")
        elif current_price < ma5 < ma10 < ma20:
            score -= 2.0
            reasons.append("均线空头排列")
        
        # MACD信号
        macd = indicators.get('macd', 0)
        macd_signal = indicators.get('macd_signal', 0)
        macd_hist = indicators.get('macd_hist', 0)
        
        if macd > macd_signal and macd_hist > 0:
            score += 1.5
            reasons.append("MACD金叉")
        elif macd < macd_signal and macd_hist < 0:
            score -= 1.5
            reasons.append("MACD死叉")
        
        # RSI信号
        rsi = indicators.get('rsi', 50)
        if rsi < 30:
            score += 1.0
            reasons.append("RSI超卖")
        elif rsi > 70:
            score -= 1.0
            reasons.append("RSI超买")
        
        # 布林带信号
        bb_upper = indicators.get('bb_upper', current_price)
        bb_lower = indicators.get('bb_lower', current_price)
        price_position = indicators.get('price_position', 0.5)
        
        if current_price < bb_lower:
            score += 1.0
            reasons.append("价格触及布林带下轨")
        elif current_price > bb_upper:
            score -= 1.0
            reasons.append("价格触及布林带上轨")
        
        # KDJ信号
        kdj_k = indicators.get('kdj_k', 50)
        kdj_d = indicators.get('kdj_d', 50)
        kdj_j = indicators.get('kdj_j', 50)
        
        if kdj_k < 20 and kdj_d < 20:
            score += 1.0
            reasons.append("KDJ超卖")
        elif kdj_k > 80 and kdj_d > 80:
            score -= 1.0
            reasons.append("KDJ超买")
        
        # 成交量信号
        volume_ratio = indicators.get('volume_ratio', 1.0)
        if volume_ratio > 1.5:
            if score > 0:
                score += 0.5
                reasons.append("放量上涨")
            else:
                score -= 0.5
                reasons.append("放量下跌")
        
        # 盈亏情况
        pnl_pct = (current_price - avg_price) / avg_price * 100
        if pnl_pct > 20:
            score -= 1.0
            reasons.append("盈利较多，考虑止盈")
        elif pnl_pct < -10:
            score += 0.5
            reasons.append("亏损较多，考虑补仓")
        
        # 确定交易动作
        if score >= 3.0:
            signals['action'] = 'buy'
            signals['confidence'] = min(score / 5.0, 1.0)
            signals['target_price'] = current_price * 1.05
            signals['stop_loss'] = current_price * 0.95
        elif score <= -3.0:
            signals['action'] = 'sell'
            signals['confidence'] = min(abs(score) / 5.0, 1.0)
            signals['target_price'] = current_price * 0.95
            signals['stop_loss'] = current_price * 1.05
        else:
            signals['action'] = 'hold'
            signals['confidence'] = 0.5
        
        signals['reasons'] = reasons
        return signals
    
    async def analyze_position_with_technical_analysis(self, position_data: Dict) -> Dict[str, Any]:
        """对单个持仓进行技术分析"""
        symbol = position_data['symbol']
        current_price = position_data['current_price']
        avg_price = position_data['avg_price']
        
        # 获取历史数据
        df = await self.get_historical_data(symbol)
        
        # 计算技术指标
        indicators = self.calculate_technical_indicators(df)
        
        # 生成交易信号
        signals = self.generate_trading_signals(indicators, current_price, avg_price)
        
        return {
            'symbol': symbol,
            'current_price': current_price,
            'avg_price': avg_price,
            'indicators': indicators,
            'signals': signals,
            'analysis_time': datetime.now().isoformat()
        }
    
    async def analyze_all_positions(self, account_id: str) -> Dict[str, Any]:
        """分析所有持仓的技术指标和交易信号"""
        # 获取持仓数据
        positions = await self.get_xtquant_positions(account_id)
        
        if not positions:
            return {
                'account_id': account_id,
                'positions': [],
                'summary': {
                    'total_positions': 0,
                    'buy_signals': 0,
                    'sell_signals': 0,
                    'hold_signals': 0
                },
                'analysis_time': datetime.now().isoformat()
            }
        
        # 分析每个持仓
        analysis_results = []
        buy_count = 0
        sell_count = 0
        hold_count = 0
        
        for position in positions:
            analysis = await self.analyze_position_with_technical_analysis(position)
            analysis_results.append(analysis)
            
            # 统计信号
            action = analysis['signals']['action']
            if action == 'buy':
                buy_count += 1
            elif action == 'sell':
                sell_count += 1
            else:
                hold_count += 1
        
        return {
            'account_id': account_id,
            'positions': analysis_results,
            'summary': {
                'total_positions': len(positions),
                'buy_signals': buy_count,
                'sell_signals': sell_count,
                'hold_signals': hold_count
            },
            'analysis_time': datetime.now().isoformat()
        }
    
    def generate_trading_recommendations(self, analysis_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成交易建议"""
        recommendations = []
        
        for position in analysis_results['positions']:
            symbol = position['symbol']
            signals = position['signals']
            indicators = position['indicators']
            
            if signals['action'] != 'hold':
                recommendation = {
                    'symbol': symbol,
                    'action': signals['action'],
                    'confidence': signals['confidence'],
                    'current_price': position['current_price'],
                    'target_price': signals['target_price'],
                    'stop_loss': signals['stop_loss'],
                    'reasons': signals['reasons'],
                    'key_indicators': {
                        'rsi': indicators.get('rsi', 0),
                        'macd': indicators.get('macd', 0),
                        'ma_trend': 'bullish' if position['current_price'] > indicators.get('ma20', 0) else 'bearish'
                    }
                }
                recommendations.append(recommendation)
        
        # 按置信度排序
        recommendations.sort(key=lambda x: x['confidence'], reverse=True)
        
        return recommendations 