#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问财智能选股工具
使用 pywencai 进行智能选股
"""
import sys
from pathlib import Path

# 添加项目根目录到 sys.path，以便可以导入 module_task 模块
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from typing import List, Dict, Any, Optional, Union
import pandas as pd
import pywencai as wc
import tushare as ts
from datetime import datetime
import asyncio
import logging

# 配置日志
logger = logging.getLogger(__name__)


def select_by_wencai(query: str) -> List[Dict[str, Any]]:
    """
    用pywencai智能选股（同步版本）
    
    Args:
        query: 问财查询语句，例如："连续3年ROE大于15%的股票"
        
    Returns:
        List[Dict[str, Any]]: 股票列表，每个字典包含 symbol（股票代码）和 name（股票名称）
        
    Example:
        >>> result = select_by_wencai("连续3年ROE大于15%的股票")
        >>> print(result)
        [{'symbol': '000001.SZ', 'name': '平安银行'}, ...]
    """
    try:
        df = wc.get(query=query)
        logger.debug(f"问财查询结果: {df}")
        if df is None or df.empty:
            return []
        
        # 识别代码列和名称列（兼容不同的列名）
        code_col = 'code' if 'code' in df.columns else '股票代码'
        name_col = 'name' if 'name' in df.columns else '股票简称'
        
        # 确保列存在
        if code_col not in df.columns or name_col not in df.columns:
            logger.warning(f"未找到预期的列，可用列: {df.columns.tolist()}")
            return []
        
        # 提取指定列（返回所有结果）
        result = df[[code_col, name_col]]
        
        # 重命名列为标准格式
        result = result.rename(columns={code_col: 'symbol', name_col: 'name'})
        
        # 转换为字典列表
        return result.to_dict(orient='records')
    except Exception as e:
        logger.error(f"问财查询失败: {e}", exc_info=True)
        return []


async def async_select_by_wencai(query: str) -> List[Dict[str, Any]]:
    """
    异步版本的问财选股
    
    Args:
        query: 问财查询语句
        
    Returns:
        List[Dict[str, Any]]: 股票列表
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, select_by_wencai, query)


def is_strictly_decreasing(sequence: List[float]) -> bool:
    """
    判断序列是否严格递减
    
    满足以下任一条件即返回True：
    1. 序列严格递减（前一个元素大于后一个元素，即 x > y）
    2. 序列的和小于等于平均值的负2倍（说明整体下降趋势明显）
    
    Args:
        sequence: 数值序列
        
    Returns:
        bool: 如果满足条件返回True，否则返回False
    """
    if len(sequence) < 2:
        return False
    
    # 条件1：检查是否严格递增
    is_increasing = all(x < y for x, y in zip(sequence[:-1], sequence[1:]))
    if is_increasing:
        return True
    
    # 条件2：检查序列和是否 <= 平均值的2倍
    sequence_sum = sum(sequence)
    average = sequence_sum / len(sequence)
    # 平均值的2倍
    two_times_avg = 2 * average
    
    # 如果序列和 <= 平均值的2倍，返回True
    if sequence_sum <= two_times_avg:
        return True
    
    return False


async def async_analyze_retail_investor_change(stock_symbol: str) -> bool:
    """
    异步分析股票散户数量变化
    
    Args:
        stock_symbol: 股票代码
        
    Returns:
        bool: 如果散户数量严格递减返回True，否则返回False
    """
    def _analyze():
        try:
            df = wc.get(query=f"{stock_symbol} 散户数量变化")
            logger.debug(f"{stock_symbol} 散户数量变化数据: {df}")
            
            if df is None:
                return False
            
            
            multi_day_df = df['多日累计dde散户数量']
            if multi_day_df is None or multi_day_df.empty:
                return False
            
            # 获取前5日的散户数量数据
            head_data = multi_day_df.head(5)
            if '区间dde散户数量' not in head_data.columns:
                logger.warning(f"{stock_symbol}: 未找到'区间dde散户数量'列")
                return False
            
            numbers = head_data['区间dde散户数量'].tolist()
            # 转换为浮点数列表，过滤掉无效值
            try:
                numbers = [float(i) for i in numbers if i is not None and str(i).strip() != '']
            except (ValueError, TypeError) as e:
                logger.warning(f"{stock_symbol}: 转换散户数量数据失败: {e}")
                return False
            
            if len(numbers) < 2:
                return False
            
            return is_strictly_decreasing(numbers)
        except Exception as e:
            logger.error(f"分析{stock_symbol}散户数量变化失败: {e}", exc_info=True)
            return False
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _analyze)


async def async_get_stock_info(stock_pool: List[str], stock_name_map: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    异步获取股票详细信息
    
    Args:
        stock_pool: 股票代码列表
        stock_name_map: 股票代码到名称的映射
        
    Returns:
        List[Dict[str, Any]]: 包含股票详细信息的列表，每个字典包含 ts_code, symbol, name, area, industry
    """
    def _get_info():
        try:
            from utils.environment_manager import get_env_manager
            env_manager = get_env_manager()
            tushare_token = env_manager.get_tushare_token()
        except Exception as e:
            logger.warning(f"无法从环境管理器获取tushare token: {e}")
            import os
            tushare_token = os.getenv('TUSHARE_TOKEN')
            if not tushare_token:
                logger.error("未找到tushare token，无法获取股票名称")
                return []
        
        try:
            pro = ts.pro_api(tushare_token)
            stock_info = pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry'
            )
            
            # 创建映射关系
            code_to_name = {}
            name_to_code = {}
            symbol_to_code = {}
            
            for _, row in stock_info.iterrows():
                ts_code = row['ts_code']
                symbol = row['symbol']
                name = row['name']
                
                code_to_name[ts_code] = {
                    'name': name,
                    'symbol': symbol,
                    'area': row.get('area', ''),
                    'industry': row.get('industry', '')
                }
                
                if name not in name_to_code:
                    name_to_code[name] = ts_code
                
                symbol_to_code[symbol] = ts_code
            
            # 匹配股票信息
            result = []
            for code in stock_pool:
                info = None
                matched_code = None
                
                if code in code_to_name:
                    info = code_to_name[code]
                    matched_code = code
                elif code in symbol_to_code:
                    matched_code = symbol_to_code[code]
                    info = code_to_name[matched_code]
                elif code in stock_name_map:
                    stock_name = stock_name_map[code]
                    if stock_name in name_to_code:
                        matched_code = name_to_code[stock_name]
                        info = code_to_name[matched_code]
                
                if info:
                    result.append({
                        'ts_code': matched_code if matched_code else code,
                        'symbol': info.get('symbol', code.split('.')[0] if '.' in code else code),
                        'name': info.get('name', stock_name_map.get(code, '未找到')),
                        'area': info.get('area', ''),
                        'industry': info.get('industry', 'N/A')
                    })
                else:
                    result.append({
                        'ts_code': code,
                        'symbol': code.split('.')[0] if '.' in code else code,
                        'name': stock_name_map.get(code, '未找到'),
                        'area': '',
                        'industry': 'N/A'
                    })
            
            return result
        except Exception as e:
            logger.error(f"获取股票信息失败: {e}", exc_info=True)
            return []
    
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_info)


async def async_select_stocks_by_wencai(
    question_list: List[str],
    filter_by_retail_investor: bool = True,
    include_info: bool = False
) -> Union[List[str], List[Dict[str, Any]]]:
    """
    异步问财智能选股主函数
    
    Args:
        question_list: 问财查询语句列表，例如：["突破十日均线，散户数量下降，龙头股，剔除st"]
        filter_by_retail_investor: 是否根据散户数量变化进行筛选（默认True）
        include_info: 是否包含股票详细信息（默认False，仅返回代码列表）
        
    Returns:
        Union[List[str], List[Dict[str, Any]]]: 
            - 如果include_info=False: 返回股票代码列表（ts_code格式）
            - 如果include_info=True: 返回包含详细信息的字典列表，每个字典包含 ts_code, symbol, name, area, industry
        
    Example:
        >>> import asyncio
        >>> questions = ["突破十日均线，散户数量下降，龙头股，剔除st"]
        >>> # 仅返回代码列表
        >>> result = asyncio.run(async_select_stocks_by_wencai(questions, include_info=False))
        >>> print(result)
        ['000001.SZ', '000002.SZ', ...]
        >>> # 返回详细信息列表
        >>> result = asyncio.run(async_select_stocks_by_wencai(questions, include_info=True))
        >>> print(result)
        [{'ts_code': '000001.SZ', 'symbol': '000001', 'name': '平安银行', ...}, ...]
    """
    stock_list = []
    stock_name_map = {}  # {symbol: name}
    
    # 第一步：根据问题列表获取股票
    logger.info(f"开始问财选股，问题数量: {len(question_list)}")
    for question in question_list:
        result = await async_select_by_wencai(question)
        stock_list.extend(result)
        # 保存名称映射
        for stock in result:
            stock_name_map[stock['symbol']] = stock.get('name', '')
    
    logger.info(f"初步筛选出 {len(stock_list)} 只股票")
    
    # 第二步：根据散户数量变化筛选（如果启用）
    stock_pool = []
    if filter_by_retail_investor:
        logger.info("开始分析散户数量变化...")
        tasks = [async_analyze_retail_investor_change(stock['symbol']) for stock in stock_list]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for stock, is_decreasing in zip(stock_list, results):
            if isinstance(is_decreasing, Exception):
                logger.warning(f"分析{stock['symbol']}时出错: {is_decreasing}")
                continue
            if is_decreasing:
                stock_pool.append(stock['symbol'])
        
        logger.info(f"散户数量筛选后剩余 {len(stock_pool)} 只股票")
    else:
        # 如果不筛选，直接使用所有股票代码
        stock_pool = [stock['symbol'] for stock in stock_list]
    
    # 第三步：获取股票详细信息（如果需要）
    if include_info and stock_pool:
        stock_info_list = await async_get_stock_info(stock_pool, stock_name_map)
        # 返回详细信息列表
        return stock_info_list
    
    # 第四步：如果需要详细信息但stock_pool为空，返回空列表
    if include_info:
        return []
    
    # 默认返回股票代码列表
    return stock_pool


async def main():
    """主程序入口"""
    question_list = []
    # question_list.append("突破十日均线，散户数量下降")
    question_list.append("突破十日均线，散户数量下降，龙头股，剔除st")
    
    # 使用异步函数获取股票列表（包含详细信息）
    stock_info_list = await async_select_stocks_by_wencai(
        question_list=question_list,
        filter_by_retail_investor=True,
        include_info=True
    )
    
    if stock_info_list:
        # 获取当前时间（年月日时分秒）
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 提取股票代码列表
        final_stock_pool = [stock['ts_code'] for stock in stock_info_list]
        
        # 打印股票代码和全称
        print(f"\n{'='*60}")
        print(f"时间: {current_time}")
        print(f"{'='*60}")
        print(f"\n筛选出的股票池（共 {len(final_stock_pool)} 只）:")
        print(f"{'-'*60}")
        print(f"{'序号':<4} | {'股票代码':<12} | {'代码':<8} | {'股票名称':<20} | {'行业':<15}")
        print(f"{'-'*60}")
        for i, stock_info in enumerate(stock_info_list, 1):
            print(f"{i:2d}.  | {stock_info['ts_code']:12s} | {stock_info['symbol']:8s} | {stock_info['name']:20s} | {stock_info['industry']:15s}")
        print(f"{'-'*60}")
        
        # 输出年月日+时分秒+股票代码列表+对应的提示词
        print(f"\n{'='*60}")
        print(f"【选股结果汇总】")
        print(f"{'='*60}")
        print(f"时间: {current_time}")
        print(f"提示词: {', '.join(question_list)}")
        print(f"股票代码列表: {final_stock_pool}")
        print(f"股票数量: {len(final_stock_pool)} 只")
        print(f"{'='*60}")
        
        # 格式化输出（便于复制使用）
        print(f"\n【格式化输出】")
        print(f"{current_time} | 提示词: {' | '.join(question_list)} | 股票代码: {','.join(final_stock_pool)}")
    else:
        print("\n未筛选出符合条件的股票")


if __name__ == "__main__":
    # 配置日志级别
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行异步主程序
    asyncio.run(main())