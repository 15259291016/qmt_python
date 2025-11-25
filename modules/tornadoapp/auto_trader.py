import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime, time

from xtquant.xttype import StockAccount
from modules.stock_selector.selector import StockSelector
from modules.tornadoapp.position.position_analyzer import PositionAnalyzer
from utils.date_util import is_trading_time
from modules.tornadoapp.risk.risk_manager import RiskManager
from modules.tornadoapp.compliance.compliance_manager import ComplianceManager
from modules.tornadoapp.audit.audit_logger import AuditLogger
from .wencai_info import async_select_stocks_by_wencai

# 配置日志
logger = logging.getLogger(__name__)
# 假设你有如下实例
# xt_trader: QMT交易API实例
# account: QMT账户
# latest_price_cache: 实时行情缓存

# 全局行情缓存
latest_price_cache = {}

class TechnicalAnalyzer:
    """技术指标分析器（示例，可扩展）"""
    def calculate_indicators(self, df):
        # 这里只做简单均线示例
        if df is None or len(df) < 20:
            return None
        ma5 = df['close'].rolling(window=5).mean().iloc[-1]
        ma20 = df['close'].rolling(window=20).mean().iloc[-1]
        last_close = df['close'].iloc[-1]
        return {"ma5": ma5, "ma20": ma20, "close": last_close}

    def is_tradable(self, indicators):
        # 示例：MA5上穿MA20
        if not indicators:
            return False
        return indicators["ma5"] > indicators["ma20"]

    def is_buy_signal(self, indicators):
        # MA5上穿MA20
        return indicators and indicators["ma5"] > indicators["ma20"]

    def is_sell_signal(self, indicators, avg_price=None, current_price=None):
        # MA5下穿MA20
        if indicators and indicators["ma5"] < indicators["ma20"]:
            return True
        # 止盈止损
        if avg_price and current_price:
            pnl = (current_price - avg_price) / avg_price * 100
            if pnl > 10 or pnl < -5:
                return True
        return False

async def auto_select_analyze_trade_monitor(
    stock_selector: StockSelector,
    xt_trader,
    account,
    position_analyzer: PositionAnalyzer,
    technical_analyzer: TechnicalAnalyzer,
    get_history_func,
    get_latest_price_func,
    interval: int = 3600
):
    """
    自动选股-分析-下单-持仓监控主流程
    get_history_func(symbol) -> DataFrame
    get_latest_price_func(symbol) -> float
    """
    while True:
        if not is_trading_time():
            print("[自动交易] 当前非交易时间，等待...")
            await asyncio.sleep(60)
            continue
        # 1. 选股（自适应热点行业多因子选股）
        try:
            selected_codes = stock_selector.select_by_hot_industry()
            print(f"热点行业选股结果: {selected_codes}")
            # 兼容原有格式，转为dict列表
            selected = [{"symbol": code} for code in selected_codes]
        except Exception as e:
            print(f"[选股] 热点行业选股失败: {e}，回退到原有条件选股")
            selected = stock_selector.select_by_wencai("市盈率小于10且银行行业，最新涨跌幅大于0，前10名")
        print(f"选股结果: {selected}")

        # 2. QMT分析选出的股票（如技术指标、风控等）
        tradable_stocks = []
        for stock in selected:
            symbol = stock['symbol']
            df = get_history_func(symbol)
            indicators = technical_analyzer.calculate_indicators(df)
            if technical_analyzer.is_tradable(indicators):
                tradable_stocks.append(symbol)

        # 3. 查询当前持仓
        positions = xt_trader.query_stock_positions(account)
        held = {p.stock_code for p in positions}

        # 4. 自动下单买入
        for symbol in tradable_stocks:
            if symbol not in held:
                price = get_latest_price_func(symbol)
                if price is None:
                    print(f"无法获取{symbol}最新价，跳过下单")
                    continue
                await xt_trader.order_manager(symbol, "买", price, 100, account)
                print(f"自动下单: {symbol} 价格: {price}")

        # 5. 持续监控持仓
        positions = xt_trader.query_stock_positions(account)
        analysis = position_analyzer.analyze_positions([
            {
                "symbol": p.stock_code,
                "volume": p.volume,
                "available_volume": getattr(p, 'enable_amount', p.volume),
                "avg_price": p.avg_price,
                "current_price": get_latest_price_func(p.stock_code)
            }
            for p in positions
        ])
        print("持仓分析结果:", analysis)

        await asyncio.sleep(interval) 

async def monitor_positions_continuously(
    xt_trader,
    account,
    position_analyzer: PositionAnalyzer,
    get_latest_price_func,
    interval: int = 60
):
    """
    持仓持续监控任务，每interval秒分析一次持仓。
    """
    while True:
        try:
            positions = xt_trader.query_stock_positions(account)
            analysis = position_analyzer.analyze_positions([
                {
                    "symbol": p.stock_code,
                    "volume": p.volume,
                    "available_volume": getattr(p, 'enable_amount', p.volume),
                    "avg_price": p.avg_price,
                    "current_price": get_latest_price_func(p.stock_code)
                }
                for p in positions
            ])
            print("[持仓监控] 最新持仓分析:", analysis)
            # 你可以在这里写入数据库、推送API、报警等
        except Exception as e:
            print(f"[持仓监控] 持仓分析失败: {e}")
        await asyncio.sleep(interval) 

# 添加多策略自动交易函数
async def monitor_positions_and_trade_multi_strategy(
    stock_selector: StockSelector,
    xt_trader,
    account: StockAccount,
    position_analyzer: PositionAnalyzer,
    technical_analyzer: TechnicalAnalyzer,
    get_history_func,
    get_latest_price_func,
    order_manager,
    interval: int = 60,
    max_stocks: int = 15
):
    """
    多策略持仓监控+自动买卖任务。
    支持多个策略并行运行，每个策略可以管理不同的股票池。
    
    Args:
        stock_selector: 选股器
        xt_trader: 交易接口
        account: 账户对象
        position_analyzer: 持仓分析器
        technical_analyzer: 技术分析器
        get_history_func: 获取历史数据函数
        get_latest_price_func: 获取最新价格函数
        order_manager: 订单管理器
        interval: 监控间隔（秒）
        max_stocks: 最大持股数量（默认15只，根据恐贪指数动态调整）
    """
    from modules.strategy_manager.manager import StrategyManager
    from modules.strategy_manager.config import STRATEGY_CONFIG
    
    # 初始化策略管理器
    risk_manager = RiskManager()
    compliance_manager = ComplianceManager()
    audit_logger = AuditLogger()
    
    strategy_manager = StrategyManager(
        xt_trader=xt_trader,
        order_manager=order_manager,
        base_path="strategy_data"
    )
    
    # 添加账户
    strategy_manager.add_account("main_account", account)
    
    # 加载策略配置
    strategy_manager.load_strategies_from_config(STRATEGY_CONFIG)
    
    # 智能策略分配函数
    def assign_strategies_to_stocks(
        held_symbols: List[str], 
        fear_greed_index: float
    ) -> Dict[str, List[str]]:
        """
        根据市场情绪（恐贪指数）智能分配策略到持仓股票
        
        该函数根据恐贪指数（0-100）将持仓股票分配到不同的交易策略：
        - 恐慌市场（<20）: 使用保守策略组合，降低风险
        - 贪婪市场（>80）: 使用增强策略组合，追求更高收益
        - 正常市场（20-80）: 使用平衡策略组合，分散风险
        
        Args:
            held_symbols: 持仓股票代码列表，例如：['000001.SZ', '000002.SZ']
            fear_greed_index: 恐贪指数，范围0-100
                - 0-20: 恐慌市场
                - 20-80: 正常市场
                - 80-100: 贪婪市场
        
        Returns:
            Dict[str, List[str]]: 策略分配字典，键为策略名称，值为分配给该策略的股票代码列表
                例如：{
                    "byd_conservative": ["000001.SZ"],
                    "ma_15_60": ["000002.SZ"]
                }
        
        Example:
            >>> stocks = ['000001.SZ', '000002.SZ', '000003.SZ']
            >>> # 恐慌市场
            >>> result = assign_strategies_to_stocks(stocks, 15)
            >>> # 返回: {"byd_conservative": ["000001.SZ"], "ma_15_60": ["000002.SZ"]}
            >>> 
            >>> # 正常市场
            >>> result = assign_strategies_to_stocks(stocks, 50)
            >>> # 返回: {"ma_5_20": ["000001.SZ"], "ma_10_30": ["000002.SZ"], "byd_strategy": ["000003.SZ"]}
        """
        # 参数验证
        if not held_symbols:
            logger.debug("持仓股票列表为空，返回空分配")
            return {}
        
        if not isinstance(held_symbols, list):
            logger.warning(f"held_symbols 应为列表类型，当前类型: {type(held_symbols)}")
            return {}
        
        # 验证恐贪指数范围
        if fear_greed_index < 0 or fear_greed_index > 100:
            logger.warning(f"恐贪指数超出正常范围(0-100): {fear_greed_index}，使用默认值50")
            fear_greed_index = 50
        
        # 去重并过滤空值
        held_symbols = list(dict.fromkeys([s for s in held_symbols if s and isinstance(s, str)]))
        
        if not held_symbols:
            logger.debug("过滤后持仓股票列表为空")
            return {}
        
        stock_count = len(held_symbols)
        logger.info(f"开始策略分配: 股票数量={stock_count}, 恐贪指数={fear_greed_index:.1f}")
        
        # 根据恐贪指数调整策略分配
        if fear_greed_index < 20:  # 恐慌市场
            # 恐慌时使用保守策略：降低风险，使用长期均线和保守策略
            # byd_conservative: 保守比亚迪策略（止损2%，止盈10%）
            # ma_15_60: 15/60日均线策略（长期均线，更稳健）
            mid_point = stock_count // 2
            assignment = {
                "byd_conservative": held_symbols[:mid_point],
                "ma_15_60": held_symbols[mid_point:]
            }
            logger.info(f"[恐慌市场] 分配策略: byd_conservative({len(assignment['byd_conservative'])}只), "
                       f"ma_15_60({len(assignment['ma_15_60'])}只)")
            
        elif fear_greed_index > 80:  # 贪婪市场
            # 贪婪时使用增强策略：追求更高收益，使用短期均线和增强策略
            # byd_enhanced: 增强比亚迪策略（止损3%，止盈20%）
            # ma_5_20: 5/20日均线策略（短期均线，更敏感）
            mid_point = stock_count // 2
            assignment = {
                "byd_enhanced": held_symbols[:mid_point],
                "ma_5_20": held_symbols[mid_point:]
            }
            logger.info(f"[贪婪市场] 分配策略: byd_enhanced({len(assignment['byd_enhanced'])}只), "
                       f"ma_5_20({len(assignment['ma_5_20'])}只)")
            
        else:  # 正常市场 (20 <= fear_greed_index <= 80)
            # 正常市场使用平衡策略：分散风险，使用多种策略组合
            # ma_5_20: 短期均线策略（5/20日均线）
            # ma_10_30: 中期均线策略（10/30日均线）
            # byd_strategy: 标准比亚迪策略（止损5%，止盈15%）
            third_point = stock_count // 3
            two_thirds_point = 2 * stock_count // 3
            
            assignment = {
                "ma_5_20": held_symbols[:third_point],
                "ma_10_30": held_symbols[third_point:two_thirds_point],
                "byd_strategy": held_symbols[two_thirds_point:]
            }
            logger.info(f"[正常市场] 分配策略: ma_5_20({len(assignment['ma_5_20'])}只), "
                       f"ma_10_30({len(assignment['ma_10_30'])}只), "
                       f"byd_strategy({len(assignment['byd_strategy'])}只)")
        
        # 过滤空列表，只返回有股票的策略
        assignment = {k: v for k, v in assignment.items() if v}
        
        # 验证分配结果：确保所有股票都被分配
        assigned_stocks = set()
        for stocks in assignment.values():
            assigned_stocks.update(stocks)
        
        if len(assigned_stocks) != stock_count:
            missing = set(held_symbols) - assigned_stocks
            logger.warning(f"部分股票未被分配: {missing}")
            # 将未分配的股票添加到第一个策略
            if assignment:
                first_strategy = list(assignment.keys())[0]
                assignment[first_strategy].extend(missing)
                logger.info(f"将未分配股票添加到策略 {first_strategy}: {missing}")
        
        logger.info(f"策略分配完成: {len(assignment)}个策略，共{stock_count}只股票")
        return assignment
    
    # 启动所有策略
    strategy_manager.start_all_strategies()
    
    last_status = None
    while True:
        trading = is_trading_time()
        if not trading:
            if last_status and last_status != 'not_trading':
                print("[多策略自动交易] 当前非交易时间，等待...")
                last_status = 'not_trading'
            await asyncio.sleep(30)
            continue
        
        last_status = 'trading'
        try:
            # 获取最新持仓分析
            positions = xt_trader.query_stock_positions(account)
            valid_positions = [p for p in positions if hasattr(p, 'stock_code') and hasattr(p, 'volume')]
            
            # 持仓分析
            analysis = position_analyzer.analyze_positions([
                {
                    "symbol": p.stock_code,
                    "volume": p.volume,
                    "available_volume": getattr(p, 'enable_amount', p.volume),
                    "avg_price": p.avg_price,
                    "current_price": get_latest_price_func(p.stock_code)
                }
                for p in valid_positions
            ])
            
            summary = analysis.summary
            fear_greed_index = getattr(summary, 'fear_greed_index', 50)
            long_term_fear_greed_index = getattr(summary, 'long_term_fear_greed_index', 50)
            print(f"[恐贪指数] 当日: {fear_greed_index:.1f}，长期: {long_term_fear_greed_index:.1f}")
            
            # 智能策略分配
            held_symbols = [p.stock_code for p in valid_positions]
            strategy_assignments = assign_strategies_to_stocks(held_symbols, fear_greed_index)
            
            # 更新策略分配
            for strategy_name, symbols in strategy_assignments.items():
                if symbols:
                    strategy_manager.assign_strategy_to_account(strategy_name, "main_account", symbols)
                    print(f"[策略分配] {strategy_name} -> {symbols}")
            
            # 获取策略状态
            strategy_status = strategy_manager.get_strategy_status()
            print(f"[策略状态] {strategy_status}")
            
            # 选股池自动买入（自适应热点行业）
            # 只在早上9:50-10:00执行问财选股，其他时间不选股
            current_time = datetime.now().time()
            stock_selection_start = time(9, 50)
            stock_selection_end = time(10, 0)
            is_stock_selection_time = stock_selection_start <= current_time <= stock_selection_end
            
            selected = []  # 默认不选股
            if is_stock_selection_time:
                try:
                    logger.info(f"[选股] 当前时间{current_time.strftime('%H:%M:%S')}在选股时间段内(9:50-10:00)，执行问财选股")
                    # selected_codes = stock_selector.select_by_hot_industry()
                    # print(f"热点行业选股结果: {selected_codes}")
                    question_list = []
                    # question_list.append("突破十日均线，散户数量下降")
                    question_list.append("突破十日均线，散户数量下降，龙头股，剔除st")
                    
                    # 使用异步函数获取股票列表（包含详细信息）
                    selected_codes = await async_select_stocks_by_wencai(
                        question_list=question_list,
                        filter_by_retail_investor=True,
                        include_info=True
                    )
                    # selected_codes = stock_selector.select_by_wencai("比亚迪")
                    selected = [{"symbol": code} for code in selected_codes]
                    logger.info(f"[选股] 问财选股完成，共选出{len(selected)}只股票")
                except Exception as e:
                    logger.error(f"[选股] 问财选股失败: {e}，本次不选股", exc_info=True)
                    print(f"[选股] 问财选股失败: {e}，本次不选股")
                    selected = []  # 选股失败时也不选股
            else:
                logger.debug(f"[选股] 当前时间{current_time.strftime('%H:%M:%S')}不在选股时间段内(9:50-10:00)，跳过选股")
            
            held = {p.stock_code for p in valid_positions}
            current_stock_count = len(held)
            
            # 根据恐贪指数动态调整最大持股数量
            # 恐慌市场：降低持股数量，集中资金（减少至70%）
            # 正常市场：标准持股数量
            # 贪婪市场：控制持股数量，预留现金（减少至80%）
            adjusted_max_stocks = max_stocks
            if fear_greed_index < 20:  # 恐慌市场
                adjusted_max_stocks = int(max_stocks * 0.7)  # 降低至70%
                logger.info(f"[资金管理] 恐慌市场（恐贪指数={fear_greed_index:.1f}），降低最大持股数量至{adjusted_max_stocks}只")
            elif fear_greed_index > 80:  # 贪婪市场
                adjusted_max_stocks = int(max_stocks * 0.8)  # 降低至80%，控制风险
                logger.info(f"[资金管理] 贪婪市场（恐贪指数={fear_greed_index:.1f}），控制最大持股数量至{adjusted_max_stocks}只")
            
            logger.info(f"[资金管理] 当前持股数量={current_stock_count}只，最大持股数量={adjusted_max_stocks}只")
            
            # 多策略买入逻辑
            for stock in selected:
                symbol = stock['symbol']
                if symbol["ts_code"] not in held:
                    # 检查是否超过最大持股数量限制
                    if current_stock_count >= adjusted_max_stocks:
                        logger.warning(f"[多策略买入] 已达到最大持股数量限制({adjusted_max_stocks}只)，跳过买入 {symbol.get('ts_code', symbol.get('symbol', 'unknown'))}")
                        print(f"[多策略买入] 已达到最大持股数量限制({adjusted_max_stocks}只)，当前持仓{current_stock_count}只，跳过买入 {symbol.get('ts_code', symbol.get('symbol', 'unknown'))}")
                        continue
                    df = get_history_func(symbol["ts_code"])
                    indicators = technical_analyzer.calculate_indicators(df)
                    current_price = get_latest_price_func(symbol["ts_code"])
                    # 计算合理的买入股数（考虑账户资金、价格、风险控制）
                    min_amount = get_min_buy_amount(
                        symbol=symbol["ts_code"],
                        account=account,
                        xt_trader=xt_trader,
                        current_price=current_price,
                        max_position_ratio=0.1,  # 单只股票最大10%仓位（风险分散原则）
                        min_position_value=10000.0,  # 最小持仓10000元（控制交易成本占比<1%）
                        max_position_value=800000.0  # 最大持仓800000元（单只股票风险上限）
                    )
                    
                    # 根据恐贪指数调整买入策略
                    buy_executed = False
                    if fear_greed_index < 10:
                        print(f"[多策略买入] 极端恐慌({fear_greed_index:.1f})，仅允许极小仓位买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount, account)
                        buy_executed = True
                    elif 10 <= fear_greed_index < 20:
                        print(f"[多策略买入] 恐慌区间({fear_greed_index:.1f})，小仓位买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount, account)
                        buy_executed = True
                    elif fear_greed_index > 90 or long_term_fear_greed_index > 90:
                        print(f"[多策略买入] 极端贪婪({fear_greed_index:.1f})，禁止买入 {symbol}")
                        continue
                    elif 80 < fear_greed_index <= 90 or 80 < long_term_fear_greed_index <= 90:
                        print(f"[多策略买入] 贪婪区间({fear_greed_index:.1f})，小仓位买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount, account)
                        buy_executed = True
                    elif fear_greed_index < 30 and long_term_fear_greed_index < 40:
                        print(f"[多策略买入] 市场恐慌，加大买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount*2, account)
                        buy_executed = True
                    elif technical_analyzer.is_buy_signal(indicators):
                        print(f"[多策略买入] 正常买入 {symbol}")
                        await order_manager(symbol["ts_code"], "买", current_price, min_amount, account)
                        buy_executed = True
                    
                    # 如果执行了买入，更新当前持股数量
                    if buy_executed:
                        current_stock_count += 1
                        logger.info(f"[资金管理] 买入后持股数量更新为{current_stock_count}只（最大{adjusted_max_stocks}只）")
                        # 如果已达到上限，提前退出循环
                        if current_stock_count >= adjusted_max_stocks:
                            logger.info(f"[资金管理] 已达到最大持股数量限制({adjusted_max_stocks}只)，停止买入新股票")
                            break
            
            # 多策略卖出逻辑：持仓股票低于20日均线卖出
            logger.info(f"开始检查持仓卖出信号，持仓数量: {len(valid_positions)}")
            for p in valid_positions:
                symbol = p.stock_code
                try:
                    # 获取历史数据
                    df = get_history_func(symbol)
                    if df is None or len(df) < 20:
                        logger.warning(f"{symbol}: 历史数据不足，无法计算20日均线，跳过卖出检查")
                        continue
                    
                    # 计算技术指标（包含20日均线）
                    indicators = technical_analyzer.calculate_indicators(df)
                    if not indicators or 'ma20' not in indicators:
                        logger.warning(f"{symbol}: 无法计算20日均线，跳过卖出检查")
                        continue
                    
                    # 获取当前价格和20日均线
                    current_price = get_latest_price_func(symbol)
                    ma20 = indicators['ma20']
                    
                    # 获取可用持仓数量
                    available_volume = getattr(p, 'enable_amount', p.volume)
                    if available_volume <= 0:
                        logger.debug(f"{symbol}: 无可用持仓，跳过卖出检查")
                        continue
                    
                    # 判断：当前价格 < 20日均线，则卖出
                    price_diff_pct = ((current_price - ma20) / ma20 * 100) if ma20 > 0 else 0
                    
                    if current_price < ma20:
                        logger.info(f"[多策略卖出] {symbol}: 当前价格({current_price:.2f}) < 20日均线({ma20:.2f})，价差={price_diff_pct:.2f}%，执行卖出")
                        print(f"[多策略卖出] {symbol}: 价格={current_price:.2f}, MA20={ma20:.2f}, 价差={price_diff_pct:.2f}%, 持仓={available_volume}股")
                        
                        # 执行卖出：卖出全部可用持仓
                        await order_manager(symbol, "卖", current_price, available_volume, account)
                        logger.info(f"[多策略卖出] {symbol}: 已提交卖出订单，数量={available_volume}股，价格={current_price:.2f}")
                    else:
                        logger.debug(f"[多策略卖出] {symbol}: 当前价格({current_price:.2f}) >= 20日均线({ma20:.2f})，价差={price_diff_pct:.2f}%，继续持有")
                        
                except Exception as e:
                    logger.error(f"[多策略卖出] {symbol}: 卖出检查失败: {e}", exc_info=True)
                    print(f"[多策略卖出] {symbol}: 卖出检查失败: {e}")
            
            # 持仓分析结果打印
            # print("[多策略持仓监控] 最新持仓分析:", analysis)
            
        except Exception as e:
            print(f"[多策略持仓监控] 自动买卖/分析失败: {e}")
        
        await asyncio.sleep(interval)

# 保留原有的单策略函数作为备用
async def monitor_positions_and_trade(
    stock_selector: StockSelector,
    xt_trader,
    account: StockAccount,
    position_analyzer: PositionAnalyzer,
    technical_analyzer: TechnicalAnalyzer,
    get_history_func,
    get_latest_price_func,
    order_manager,
    interval: int = 60
):
    """
    持仓持续监控+自动买卖任务（单策略版本）。
    - 买入信号：MA5上穿MA20且未持有
    - 卖出信号：MA5下穿MA20或止盈>10%或止损<-5%
    - 集成恐贪指数决策（极端行情优化）
    """
    last_status = None  # 记录上一次交易状态，防止刷屏
    while True:
        trading = is_trading_time()
        if not trading:
            if last_status and last_status != 'not_trading':
                print("[自动交易] 当前非交易时间，等待...")
                last_status = 'not_trading'
            await asyncio.sleep(30)  # 非交易时段加长等待，减少刷屏
            continue
        last_status = 'trading'
        try:
            positions = xt_trader.query_stock_positions(account)
            valid_positions = [p for p in positions if hasattr(p, 'stock_code') and hasattr(p, 'volume')]
            held = {p.stock_code for p in valid_positions}
            # 获取持仓分析，提取恐贪指数
            analysis = position_analyzer.analyze_positions([
                {
                    "symbol": p.stock_code,
                    "volume": p.volume,
                    "available_volume": getattr(p, 'enable_amount', p.volume),
                    "avg_price": p.avg_price,
                    "current_price": get_latest_price_func(p.stock_code)
                }
                for p in valid_positions
            ])
            summary = analysis.summary
            fear_greed_index = getattr(summary, 'fear_greed_index', 50)
            long_term_fear_greed_index = getattr(summary, 'long_term_fear_greed_index', 50)
            print(f"[恐贪指数] 当日: {fear_greed_index:.1f}，长期: {long_term_fear_greed_index:.1f}")
            # 2. 自动卖出
            for p in valid_positions:
                symbol = p.stock_code
                df = get_history_func(symbol)
                indicators = technical_analyzer.calculate_indicators(df)
                current_price = get_latest_price_func(symbol)
                # 极端恐慌下禁止卖出
                if fear_greed_index < 10:
                    print(f"[卖出决策] 极端恐慌({fear_greed_index:.1f})，禁止卖出 {symbol}，建议耐心等待情绪修复。")
                    continue
                # 恐慌区间仅允许止损卖出
                if 10 <= fear_greed_index < 20:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        pnl = (current_price - p.avg_price) / p.avg_price * 100
                        if pnl < -5:
                            await order_manager(symbol, "卖", current_price, p.m_nCanUseVolume, account)
                            print(f"[卖出决策] 恐慌区间({fear_greed_index:.1f})，仅允许止损卖出 {symbol} 价格: {current_price}")
                        else:
                            print(f"[卖出决策] 恐慌区间({fear_greed_index:.1f})，非止损不卖出 {symbol}")
                    continue
                # 极端贪婪下允许加大卖出
                if fear_greed_index > 90 or long_term_fear_greed_index > 90:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        await order_manager(symbol, "卖", current_price, p.m_nCanUseVolume, account)
                        print(f"[卖出决策] 极端贪婪({fear_greed_index:.1f})，加大卖出 {symbol} 价格: {current_price}，建议锁定收益。")
                    continue
                # 80-90区间正常卖出
                if 80 < fear_greed_index <= 90 or 80 < long_term_fear_greed_index <= 90:
                    if technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                        await order_manager(symbol, "卖", current_price, p.m_nCanUseVolume, account)
                        print(f"[卖出决策] 贪婪区间({fear_greed_index:.1f})，正常卖出 {symbol} 价格: {current_price}")
                    continue
                # 其它情况正常卖出
                if p.m_nCanUseVolume != 0 and technical_analyzer.is_sell_signal(indicators, avg_price=p.avg_price, current_price=current_price):
                    await order_manager(symbol, "卖", current_price, p.m_nCanUseVolume, account)
                    print(f"[自动卖出] {symbol} 价格: {current_price}")
            # 3. 选股池自动买入（自适应热点行业）
            try:
                selected_codes = stock_selector.select_by_hot_industry()
                print(f"热点行业选股结果: {selected_codes}")
                selected = [{"symbol": code} for code in selected_codes]
            except Exception as e:
                print(f"[选股] 热点行业选股失败: {e}，回退到原有条件选股")
                selected = stock_selector.select_by_wencai("银行行业，市盈率TTM小于10，市净率小于1.2，净利润同比增长率大于5%，近3个月涨幅大于0，波动率小于5%，按净利润同比增长率降序排列，前10名")
            for stock in selected:
                symbol = stock['symbol']
                if symbol not in held:
                    df = get_history_func(symbol)
                    indicators = technical_analyzer.calculate_indicators(df)
                    current_price = get_latest_price_func(symbol)
                    # 计算合理的买入股数（考虑账户资金、价格、风险控制）
                    min_amount = get_min_buy_amount(
                        symbol=symbol,
                        account=account,
                        xt_trader=xt_trader,
                        current_price=current_price,
                        max_position_ratio=0.1,  # 单只股票最大10%仓位（风险分散原则）
                        min_position_value=10000.0,  # 最小持仓10000元（控制交易成本占比<1%）
                        max_position_value=80000.0  # 最大持仓80000元（单只股票风险上限）
                    )
                    # 极端恐慌下仅允许极小仓位买入
                    if fear_greed_index < 10:
                        print(f"[买入决策] 极端恐慌({fear_greed_index:.1f})，仅允许极小仓位买入 {symbol}，建议谨慎抄底。买入{min_amount}股")
                        await order_manager(symbol, "买", current_price, min_amount, account)
                        continue
                    # 恐慌区间允许小仓位买入
                    if 10 <= fear_greed_index < 20:
                        print(f"[买入决策] 恐慌区间({fear_greed_index:.1f})，仅允许小仓位买入 {symbol}，建议分批建仓。买入{min_amount*0.5//min_amount*min_amount if min_amount*0.5>=min_amount else min_amount}股")
                        await order_manager(symbol, "买", current_price, min_amount, account)
                        continue
                    # 极端贪婪下禁止买入
                    if fear_greed_index > 90 or long_term_fear_greed_index > 90:
                        print(f"[买入决策] 极端贪婪({fear_greed_index:.1f})，禁止买入 {symbol}，建议耐心等待回调。")
                        continue
                    # 贪婪区间仅允许小仓位买入
                    if 80 < fear_greed_index <= 90 or 80 < long_term_fear_greed_index <= 90:
                        print(f"[买入决策] 贪婪区间({fear_greed_index:.1f})，仅允许小仓位买入 {symbol}，建议谨慎追高。买入{min_amount}股")
                        await order_manager(symbol, "买", current_price, min_amount, account)
                        continue
                    # 恐慌区间加大买入
                    if fear_greed_index < 30 and long_term_fear_greed_index < 40:
                        print(f"[买入决策] 市场恐慌(当日{fear_greed_index:.1f}/长期{long_term_fear_greed_index:.1f})，允许加大买入 {symbol}。买入{min_amount*2}股")
                        await order_manager(symbol, "买", current_price, min_amount*2, account)
                        print(f"[自动买入-加大] {symbol} 价格: {current_price}")
                        continue
                    # 其它情况正常买入
                    if technical_analyzer.is_buy_signal(indicators):
                        print(f"[买入决策] 正常买入 {symbol}，买入{min_amount}股")
                        await order_manager(symbol, "买", current_price, min_amount, account)
                        print(f"[自动买入] {symbol} 价格: {current_price}")
            # 持仓分析结果打印
            print("[持仓监控] 最新持仓分析:", analysis)
        except Exception as e:
            print(f"[持仓监控] 自动买卖/分析失败: {e}")
        await asyncio.sleep(interval)  # 交易时段内保持原有间隔

def get_min_buy_amount(
    symbol: str,
    account: Optional[StockAccount] = None,
    xt_trader=None,
    current_price: Optional[float] = None,
    max_position_ratio: float = 0.1,
    min_position_value: float = 10000.0,
    max_position_value: float = 80000.0
) -> int:
    """
    计算合理的买入股数（基于量化交易最佳实践）
    
    根据以下因素计算：
    1. 交易所最小买入单位（100股或200股）
    2. 账户可用资金
    3. 股票当前价格
    4. 单只股票最大仓位比例（默认10%，符合风险分散原则）
    5. 最小/最大持仓金额限制（基于交易成本和风险控制）
    
    策略研究说明：
    - 最小持仓10000元：确保交易成本占比<1%（佣金0.03%+印花税0.1%+过户费0.001%）
      避免小额交易导致成本侵蚀收益，提高资金利用效率
    - 最大持仓80000元：单只股票风险上限，即使账户资金较大也限制单股风险
      结合10%仓位比例，可同时持有10-12只股票，实现良好分散化
    - 10%仓位比例：基于现代投资组合理论，单只股票不超过总资金10%
      既能获得分散化收益，又能控制单股风险敞口
    
    Args:
        symbol: 股票代码，例如 '000001.SZ'
        account: 股票账户对象（可选）
        xt_trader: 交易接口对象（可选，用于查询账户资金）
        current_price: 股票当前价格（可选，如果不提供则返回最小买入单位）
        max_position_ratio: 单只股票最大仓位比例（默认0.1，即10%，风险分散原则）
        min_position_value: 最小持仓金额（默认10000元，控制交易成本占比<1%）
        max_position_value: 最大持仓金额（默认80000元，单只股票风险上限）
        
    Returns:
        int: 建议买入股数（已调整为最小买入单位的整数倍）
        
    Example:
        >>> # 仅获取最小买入单位
        >>> amount = get_min_buy_amount('000001.SZ')
        >>> # 返回: 100
        >>> 
        >>> # 根据账户资金和价格计算
        >>> amount = get_min_buy_amount('000001.SZ', account, xt_trader, current_price=10.5)
        >>> # 返回: 根据账户资金计算的合理股数（10000-80000元范围内）
    """
    # 1. 确定最小买入单位（交易所规则）
    min_unit = 100  # 默认100股
    if symbol.endswith('.BJ'):
        min_unit = 100
    elif symbol.startswith('688'):  # 科创板
        min_unit = 200
    elif symbol.startswith('300'):  # 创业板
        min_unit = 100
    elif symbol.startswith('60') or symbol.startswith('00'):  # 主板
        min_unit = 100
    
    # 如果没有提供价格或账户信息，直接返回最小买入单位
    if current_price is None or current_price <= 0:
        return min_unit
    
    # 如果没有提供账户信息，返回最小买入单位
    if account is None or xt_trader is None:
        logger.debug(f"{symbol}: 未提供账户信息，返回最小买入单位 {min_unit}")
        return min_unit
    
    try:
        # 2. 查询账户可用资金
        asset = xt_trader.query_stock_asset(account)
        available_cash = getattr(asset, 'cash', 0) or getattr(asset, 'available_cash', 0)
        
        if available_cash <= 0:
            logger.warning(f"{symbol}: 账户可用资金为0或无法获取，返回最小买入单位 {min_unit}")
            return min_unit
        
        # 3. 计算基于资金限制的最大可买金额
        # 考虑单只股票最大仓位比例
        max_buy_value_by_ratio = available_cash * max_position_ratio
        
        # 考虑最大持仓金额限制
        max_buy_value = min(max_buy_value_by_ratio, max_position_value)
        
        # 确保不低于最小持仓金额
        if max_buy_value < min_position_value:
            logger.debug(f"{symbol}: 计算出的最大买入金额({max_buy_value:.2f})小于最小持仓金额({min_position_value:.2f})")
            # 如果可用资金足够，使用最小持仓金额
            if available_cash >= min_position_value:
                max_buy_value = min_position_value
            else:
                logger.warning(f"{symbol}: 可用资金不足，返回最小买入单位 {min_unit}")
                return min_unit
        
        # 4. 计算可买股数（考虑手续费，假设0.03%）
        commission_rate = 0.0003
        # 买入金额 = 股数 * 价格 * (1 + 手续费率)
        # 股数 = 买入金额 / (价格 * (1 + 手续费率))
        max_shares = int(max_buy_value / (current_price * (1 + commission_rate)))
        
        # 5. 调整为最小买入单位的整数倍
        shares = (max_shares // min_unit) * min_unit
        
        # 6. 确保不低于最小买入单位
        if shares < min_unit:
            shares = min_unit
        
        # 7. 验证最终金额不超过可用资金
        final_cost = shares * current_price * (1 + commission_rate)
        if final_cost > available_cash:
            # 如果超出，减少到可用资金范围内
            max_affordable_shares = int(available_cash / (current_price * (1 + commission_rate)))
            shares = (max_affordable_shares // min_unit) * min_unit
            if shares < min_unit:
                logger.warning(f"{symbol}: 可用资金不足，返回最小买入单位 {min_unit}")
                return min_unit
        
        logger.info(f"{symbol}: 计算买入股数 - 可用资金={available_cash:.2f}, 价格={current_price:.2f}, "
                   f"建议股数={shares}, 预计金额={shares * current_price:.2f}")
        
        return shares
        
    except Exception as e:
        logger.error(f"{symbol}: 计算买入股数失败: {e}，返回最小买入单位 {min_unit}", exc_info=True)
        return min_unit
def get_latest_price_func(symbol, xt_trader=None):
    from main import get_latest_price_func as main_get_latest_price_func
    return main_get_latest_price_func(symbol)
