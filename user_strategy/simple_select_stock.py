#!/usr/bin/env python3
"""
简化的股票选择器
避免复杂的财务数据获取问题
"""

import pandas as pd
import numpy as np
import tushare as ts
import logging
from datetime import datetime, timedelta
import pymysql
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ConfigServer as Cs

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleStockSelector:
    """简化的股票选择器"""
    
    def __init__(self, token, db_config=None):
        """
        初始化股票选择器
        
        Args:
            token: tushare token
            db_config: 数据库配置
        """
        self.token = token
        self.db_config = db_config
        self.pro = ts.pro_api(token)
        self.factor_weights = None
        
        # 设置日期范围
        self.end_date = datetime.now().strftime('%Y%m%d')
        self.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        # 连接数据库
        if db_config:
            try:
                self.connection = pymysql.connect(**db_config)
                logger.info("数据库连接成功")
            except Exception as e:
                logger.error(f"数据库连接失败: {e}")
                self.connection = None
        else:
            self.connection = None
    
    def get_stock_list(self):
        """获取股票列表"""
        try:
            # 获取A股股票列表
            stock_list = self.pro.stock_basic(
                exchange='', 
                list_status='L', 
                fields='ts_code,name,industry,list_date'
            )
            logger.info(f"获取到 {len(stock_list)} 只股票")
            return stock_list
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_daily_data(self, ts_codes, days=60):
        """获取日线数据"""
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            # 分批获取数据，每批最多1000只股票
            batch_size = 1000
            all_daily_data = []
            
            for i in range(0, len(ts_codes), batch_size):
                batch_codes = ts_codes[i:i + batch_size]
                logger.info(f"获取第 {i//batch_size + 1} 批数据，包含 {len(batch_codes)} 只股票")
                
                try:
                    batch_data = self.pro.daily(
                        ts_code=','.join(batch_codes),
                        start_date=start_date,
                        end_date=end_date,
                        fields='ts_code,trade_date,open,high,low,close,vol,amount,pct_chg'
                    )
                    if not batch_data.empty:
                        all_daily_data.append(batch_data)
                except Exception as e:
                    logger.warning(f"第 {i//batch_size + 1} 批数据获取失败: {e}")
                    continue
            
            if all_daily_data:
                daily_data = pd.concat(all_daily_data, ignore_index=True)
                logger.info(f"总共获取到 {len(daily_data)} 条日线数据")
                return daily_data
            else:
                logger.error("所有批次数据获取都失败")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取日线数据失败: {e}")
            return pd.DataFrame()
    
    def calculate_technical_factors(self, df):
        """计算技术指标因子"""
        try:
            # 按股票分组计算
            grouped = df.groupby('ts_code', group_keys=False)
            
            # 1. 动量因子 - 20日收益率
            df['momentum_20d'] = grouped['close'].transform(lambda x: x.pct_change(20))
            
            # 2. 波动率因子 - 20日波动率
            df['volatility_20d'] = grouped['close'].transform(lambda x: x.pct_change().rolling(20).std())
            
            # 3. 相对强弱指标 (RSI)
            def calculate_rsi(prices, period=14):
                delta = prices.diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
                rs = gain / loss
                rsi = 100 - (100 / (1 + rs))
                return rsi
            df['rsi_14'] = grouped['close'].transform(calculate_rsi)
            
            # 4. 移动平均线
            df['ma5'] = grouped['close'].transform(lambda x: x.rolling(5).mean())
            df['ma20'] = grouped['close'].transform(lambda x: x.rolling(20).mean())
            df['ma_ratio'] = df['ma5'] / df['ma20']
            
            # 5. 成交量因子
            df['volume_ma5'] = grouped['vol'].transform(lambda x: x.rolling(5).mean())
            df['volume_ratio'] = df['vol'] / df['volume_ma5']
            
            logger.info("技术指标计算完成")
            return df
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return df
    
    def calculate_quality_factors(self, df):
        """计算质量因子（简化版）"""
        try:
            # 1. 价格稳定性 - 价格波动率
            grouped = df.groupby('ts_code')
            df['price_stability'] = 1 / (1 + grouped['close'].transform(
                lambda x: x.pct_change().rolling(20).std()
            ))
            
            # 2. 流动性因子 - 基于成交量
            df['liquidity'] = df['vol'] * df['close']  # 成交金额
            
            # 3. 趋势强度
            df['trend_strength'] = abs(df['ma5'] - df['ma20']) / df['ma20']
            
            logger.info("质量因子计算完成")
            return df
            
        except Exception as e:
            logger.error(f"计算质量因子失败: {e}")
            return df
    
    def normalize_factors(self, df):
        """因子标准化"""
        try:
            # 需要标准化的因子列表
            factor_columns = [
                'momentum_20d', 'volatility_20d', 'rsi_14', 'ma_ratio',
                'volume_ratio', 'price_stability', 'liquidity', 'trend_strength'
            ]
            
            # 只处理存在的列
            existing_factors = [col for col in factor_columns if col in df.columns]
            
            # Z-score标准化
            for factor in existing_factors:
                df[f'{factor}_zscore'] = (df[factor] - df[factor].mean()) / df[factor].std()
            
            logger.info("因子标准化完成")
            return df
            
        except Exception as e:
            logger.error(f"因子标准化失败: {e}")
            return df
    
    def calculate_composite_score(self, df):
        """计算综合评分"""
        try:
            # 获取所有zscore因子
            zscore_columns = [col for col in df.columns if col.endswith('_zscore')]
            
            if not zscore_columns:
                logger.warning("没有找到标准化因子，使用原始因子")
                factor_columns = [
                    'momentum_20d', 'volatility_20d', 'rsi_14', 'ma_ratio',
                    'volume_ratio', 'price_stability', 'liquidity', 'trend_strength'
                ]
                zscore_columns = [col for col in factor_columns if col in df.columns]
            
            # 等权重评分
            weights = pd.Series(1.0 / len(zscore_columns), index=zscore_columns)
            
            # 计算综合评分
            df['composite_score'] = df[zscore_columns].dot(weights)
            
            # 处理缺失值
            df['composite_score'] = df['composite_score'].fillna(0)
            
            logger.info("综合评分计算完成")
            return df
            
        except Exception as e:
            logger.error(f"计算综合评分失败: {e}")
            df['composite_score'] = 0
            return df
    
    def get_top_stocks(self, top_n=10, min_volume=1000000):
        """获取Top N股票"""
        try:
            logger.info("开始选股流程...")
            
            # 1. 获取股票列表
            stock_list = self.get_stock_list()
            if stock_list.empty:
                logger.error("无法获取股票列表")
                return []
            
            # 2. 获取日线数据
            ts_codes = stock_list['ts_code'].tolist()
            daily_data = self.get_daily_data(ts_codes)
            if daily_data.empty:
                logger.error("无法获取日线数据")
                return []
            
            # 3. 计算技术指标
            daily_data = self.calculate_technical_factors(daily_data)
            
            # 4. 计算质量因子
            daily_data = self.calculate_quality_factors(daily_data)
            
            # 5. 因子标准化
            daily_data = self.normalize_factors(daily_data)
            
            # 6. 计算综合评分
            daily_data = self.calculate_composite_score(daily_data)
            
            # 7. 筛选条件
            # 获取最新数据
            latest_date = daily_data['trade_date'].max()
            latest_data = daily_data[daily_data['trade_date'] == latest_date].copy()
            
            # 筛选条件
            filtered_data = latest_data[
                (latest_data['vol'] >= min_volume) &  # 最小成交量
                (latest_data['close'] > 0) &  # 价格大于0
                (latest_data['composite_score'].notna())  # 评分不为空
            ]
            
            # 8. 排序并返回Top N
            top_stocks = filtered_data.nlargest(top_n, 'composite_score')
            
            logger.info(f"选股完成，返回 {len(top_stocks)} 只股票")
            
            # 返回股票代码列表
            return top_stocks['ts_code'].tolist()
            
        except Exception as e:
            logger.error(f"选股过程失败: {e}")
            return []
    
    def get_stock_details(self, ts_codes):
        """获取股票详细信息"""
        try:
            stock_list = self.get_stock_list()
            details = stock_list[stock_list['ts_code'].isin(ts_codes)]
            return details
        except Exception as e:
            logger.error(f"获取股票详情失败: {e}")
            return pd.DataFrame()
    
    def close(self):
        """关闭数据库连接"""
        if self.connection:
            self.connection.close()
            logger.info("数据库连接已关闭")


def run_simple_strategy(environment: str = 'SIMULATION'):
    """运行简化策略"""
    try:
        from utils.environment_manager import get_env_manager
        env_manager = get_env_manager()
        
        # 切换到指定环境
        if not env_manager.switch_environment(environment):
            logger.error(f"切换到 {environment} 环境失败")
            return []
        
        # 获取配置
        toshare_token = env_manager.get_tushare_token()
        db_config = env_manager.get_database_config()
        
        logger.info(f"使用 {environment} 环境运行选股策略")
        
        # 创建选股器
        selector = SimpleStockSelector(token=toshare_token, db_config=db_config)
        
        # 获取Top 10股票
        top_stocks = selector.get_top_stocks(top_n=10)
        
        if top_stocks:
            print(f"\n推荐股票列表 (Top 10):")
            print("=" * 50)
            for i, stock in enumerate(top_stocks, 1):
                print(f"{i:2d}. {stock}")
            
            # 获取详细信息
            details = selector.get_stock_details(top_stocks)
            if not details.empty:
                print(f"\n股票详细信息:")
                print("=" * 50)
                print(details.to_string(index=False))
        else:
            print("未找到符合条件的股票")
        
        # 关闭连接
        selector.close()
        
        return top_stocks
        
    except Exception as e:
        logger.error(f"策略运行失败: {e}")
        return []


if __name__ == "__main__":
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='简化选股策略')
    parser.add_argument('--env', '--environment', 
                       choices=['SIMULATION', 'PRODUCTION'], 
                       default='SIMULATION',
                       help='运行环境 (SIMULATION: 模拟环境, PRODUCTION: 实盘环境)')
    
    args = parser.parse_args()
    
    print(f"🚀 启动简化选股策略 - 环境: {args.env}")
    run_simple_strategy(args.env) 