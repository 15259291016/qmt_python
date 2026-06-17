# coding=utf-8
"""
动态持仓管理器
根据账户资金体量自动调整持仓参数，实现智能资金管理
"""
import logging
from typing import Dict, Optional
from xtquant.xttype import StockAccount

logger = logging.getLogger(__name__)

try:
    # 统一的交易事件记录（写入 Excel），用于事后复盘
    from .trade_event_recorder import record_trade_event
except Exception:
    # 如果导入失败（例如未安装依赖），提供一个空实现，不影响主流程
    def record_trade_event(*args, **kwargs):  # type: ignore[no-redef]
        return None


class DynamicPositionManager:
    """
    动态持仓管理器
    
    根据账户总资金自动调整以下参数：
    1. 最大持股数量
    2. 单股最小持仓金额
    3. 单股最大持仓金额
    4. 单股最大仓位比例
    
    设计原则：
    - 小账户：集中持仓，降低交易成本占比
    - 大账户：分散持仓，降低单股风险
    - 动态调整：根据资金变化自动适配
    """
    
    # 资金分级配置（单位：元）
    # 注意：考虑佣金最低5元的影响，单股最小金额应 >= 10000元以降低成本占比
    TIER_CONFIG = [
        # (资金上限, 最大持股数, 单股最小金额, 单股最大金额, 单股最大仓位比例)
        # 实盘小资金账户（<5万）：单只股票最高 80% 仓位，避免满仓单票风险。
        (50000, 2, 10000, 25000, 0.80),       # < 5万：1-2只，单票最高80%仓位
        (100000, 3, 10000, 35000, 0.35),      # 5-10万：2-3只，集中持仓
        (500000, 10, 10000, 80000, 0.15),     # 10-50万：5-10只，适度分散
        (1000000, 15, 20000, 150000, 0.12),   # 50-100万：8-15只，良好分散
        (5000000, 20, 50000, 500000, 0.10),   # 100-500万：12-20只，充分分散
        (10000000, 25, 100000, 1000000, 0.08), # 500-1000万：15-25只，高度分散
        (50000000, 30, 200000, 3000000, 0.08), # 1000-5000万：20-30只，专业级分散
        (float('inf'), 40, 500000, 5000000, 0.06), # > 5000万：30-40只，机构级分散
    ]

    # 卖出策略分级配置（按资金体量细化，不再一刀切）
    # 字段说明：
    #   technical_sell_min_profit_pct : 技术指标触发卖出所需的最低浮盈（%）
    #   macd_hist_confirm_bars        : MACD柱状图转负需连续确认的K线根数
    #   trailing_take_profit_activate_pct  : 追踪止盈激活阈值（浮盈达到该值开始追踪）
    #   trailing_take_profit_drawdown_pct  : 从峰值回撤多少%触发止盈卖出
    # 设计思路：
    #   小账户波动大、成本占比高 → 低门槛快速锁利；大账户持仓稳 → 给利润更大奔跑空间
    SELL_TIER_CONFIG = [
        # (资金上限, 技术卖出最低盈利%, MACD确认根数, 追踪止盈激活%, 追踪止盈回撤%)
        (50000,      4.0, 1, 5.0,  2.0),   # < 5万：低门槛快速锁利，回撤2%防日内噪声洗出
        (100000,     5.0, 1, 5.5,  2.0),   # 5-10万：追踪止盈5.5%激活，技术卖出5%门槛
        (500000,     8.0, 2, 6.0,  2.0),   # 10-50万：追踪止盈6%先激活，技术卖出8%补充
        (1000000,   10.0, 2, 8.0,  2.5),   # 50-100万：追踪止盈8%激活，技术卖出10%补充
        (5000000,   12.0, 2, 10.0, 3.0),   # 100-500万：追踪止盈10%激活，MACD确认2根
        (10000000,  15.0, 2, 12.0, 3.5),   # 500-1000万：追踪止盈12%激活，MACD确认2根
        (50000000,  15.0, 3, 13.0, 4.0),   # 1000-5000万：专业级，回撤容忍更大
        (float('inf'), 15.0, 3, 14.0, 5.0), # > 5000万：机构级，充分让利润奔跑
    ]
    
    def __init__(self, xt_trader, account: StockAccount):
        self.xt_trader = xt_trader
        self.account = account
        self._cached_total_asset = None
        self._cached_params = None
        
    def get_total_asset(self) -> float:
        """获取账户总资产（含持仓市值）"""
        try:
            asset = self.xt_trader.query_stock_asset(self.account)
            _cash = getattr(asset, 'cash', None)
            available_cash = _cash if _cash is not None else getattr(asset, 'available_cash', 0.0)
            market_value = getattr(asset, 'market_value', None)
            market_value = float(market_value) if market_value is not None else 0.0
            total_asset = available_cash + market_value
            if total_asset <= 0:
                logger.warning(f"账户总资产为0或无法获取，使用默认值100000元")
                return 100000.0
            logger.info(f"[资金管理] 账户总资产={total_asset:.2f}元（可用资金={available_cash:.2f}，持仓市值={market_value:.2f}）")
            self._cached_total_asset = total_asset
            return total_asset
        except Exception as e:
            logger.error(f"获取账户总资产失败: {e}，使用默认值100000元", exc_info=True)
            return 100000.0
    
    def get_position_params(self, fear_greed_index: Optional[float] = None) -> Dict[str, float]:
        """根据账户资金体量获取持仓参数"""
        total_asset = self.get_total_asset()
        base_params = self._get_base_params_by_asset(total_asset)
        if fear_greed_index is not None:
            adjusted_params = self._adjust_params_by_fear_greed(base_params, fear_greed_index)
        else:
            adjusted_params = base_params
        adjusted_params['total_asset'] = total_asset

        # 卖出策略相关参数：按资金体量分级，不再一刀切
        sell_params = self._get_sell_params_by_asset(total_asset)
        adjusted_params.setdefault('technical_sell_min_profit_pct',       sell_params['technical_sell_min_profit_pct'])
        adjusted_params.setdefault('macd_hist_confirm_bars',               sell_params['macd_hist_confirm_bars'])
        adjusted_params.setdefault('trailing_take_profit_activate_pct',    sell_params['trailing_take_profit_activate_pct'])
        adjusted_params.setdefault('trailing_take_profit_drawdown_pct',    sell_params['trailing_take_profit_drawdown_pct'])
        
        self._cached_params = adjusted_params
        logger.info(
            f"[资金管理] 持仓参数: 总资产={total_asset:.0f}元, "
            f"最大持股={adjusted_params['max_stocks']}只, "
            f"单股范围={adjusted_params['min_position_value']:.0f}-{adjusted_params['max_position_value']:.0f}元, "
            f"最大仓位={adjusted_params['max_position_ratio']*100:.0f}%"
        )
        return adjusted_params
    
    def _get_sell_params_by_asset(self, total_asset: float) -> Dict[str, float]:
        """根据资金体量确定卖出策略参数（止盈/追踪止盈分级细化）"""
        for asset_limit, tech_min, macd_bars, trailing_activate, trailing_drawdown in self.SELL_TIER_CONFIG:
            if total_asset <= asset_limit:
                params = {
                    'technical_sell_min_profit_pct':    tech_min,
                    'macd_hist_confirm_bars':           macd_bars,
                    'trailing_take_profit_activate_pct': trailing_activate,
                    'trailing_take_profit_drawdown_pct': trailing_drawdown,
                }
                logger.info(
                    f"[资金管理] 卖出策略分级: 总资产={total_asset:.0f}元, "
                    f"技术卖出最低盈利={tech_min}%, MACD确认={macd_bars}根, "
                    f"追踪止盈激活={trailing_activate}%, 回撤触发={trailing_drawdown}%"
                )
                return params
        # 兜底（理论上不会走到这里）
        return {
            'technical_sell_min_profit_pct':    15.0,
            'macd_hist_confirm_bars':           3,
            'trailing_take_profit_activate_pct': 15.0,
            'trailing_take_profit_drawdown_pct': 5.0,
        }

    def _get_base_params_by_asset(self, total_asset: float) -> Dict[str, float]:
        """根据资金体量确定基础参数"""
        for asset_limit, max_stocks, min_value, max_value, max_ratio in self.TIER_CONFIG:
            if total_asset <= asset_limit:
                return {
                    'max_stocks': max_stocks,
                    'min_position_value': min_value,
                    'max_position_value': max_value,
                    'max_position_ratio': max_ratio,
                    'max_total_position_ratio': 0.80,  # 总仓位上限：任意资金体量最多使用80%资金
                }
        # 兜底：取配置表最后一档（与 TIER_CONFIG 保持同步）
        last = self.TIER_CONFIG[-1]
        return {
            'max_stocks': last[1],
            'min_position_value': last[2],
            'max_position_value': last[3],
            'max_position_ratio': last[4],
            'max_total_position_ratio': 0.80,  # 总仓位上限：任意资金体量最多使用80%资金
        }
    
    def _adjust_params_by_fear_greed(self, base_params: Dict[str, float], fear_greed_index: float) -> Dict[str, float]:
        """根据恐贪指数微调参数"""
        adjusted_params = base_params.copy()
        if fear_greed_index < 20:  # 恐慌市场
            adjusted_params['max_stocks'] = int(base_params['max_stocks'] * 0.7)
            logger.info(f"[资金管理] 恐慌市场（恐贪指数={fear_greed_index:.1f}），降低最大持股数量至{adjusted_params['max_stocks']}只")
        elif fear_greed_index > 80:  # 贪婪市场
            adjusted_params['max_stocks'] = int(base_params['max_stocks'] * 0.8)
            logger.info(f"[资金管理] 贪婪市场（恐贪指数={fear_greed_index:.1f}），控制最大持股数量至{adjusted_params['max_stocks']}只")
        adjusted_params['max_stocks'] = max(1, adjusted_params['max_stocks'])
        return adjusted_params
    
    def calculate_buy_amount(self, symbol: str, current_price: float, params: Optional[Dict[str, float]] = None) -> int:
        """计算合理的买入股数（已调整为100的整数倍）"""
        if params is None:
            if self._cached_params is None:
                params = self.get_position_params()
            else:
                params = self._cached_params
        
        # 确定最小买入单位和单笔最大委托数量
        # 科创板（688开头）：最小200股，单笔最大委托10万股
        # 普通A股：最小100股，单笔最大委托100万股
        min_unit = 100
        max_single_order_shares = 1000000  # 普通A股单笔最大100万股
        if symbol.startswith('688'):
            min_unit = 200
            max_single_order_shares = 100000  # 科创板单笔最大10万股
        
        if current_price is None or current_price <= 0:
            logger.warning(f"{symbol}: 价格无效（{current_price}），不买入（返回0）")
            return 0
        
        try:
            asset = self.xt_trader.query_stock_asset(self.account)
            _cash = getattr(asset, 'cash', None)
            available_cash = _cash if _cash is not None else getattr(asset, 'available_cash', 0.0)
            market_value = float(getattr(asset, 'market_value', None) or 0.0)
            total_asset = float(available_cash) + market_value

            if available_cash <= 0:
                logger.warning(f"{symbol}: 账户可用资金为0或无法获取，不买入（返回0）")
                return 0

            # 新增：总仓位上限控制（任何资金体量最多使用80%总资产）
            max_total_position_ratio = float(params.get('max_total_position_ratio', 0.80))
            max_allowed_market_value = total_asset * max_total_position_ratio
            remaining_position_budget = max_allowed_market_value - market_value
            if remaining_position_budget < params['min_position_value']:
                logger.warning(
                    f"{symbol}: 总仓位已接近上限（当前持仓市值={market_value:.2f}，"
                    f"上限={max_allowed_market_value:.2f}，剩余额度={remaining_position_budget:.2f}），不买入"
                )
                return 0

            max_buy_value_by_ratio = available_cash * params['max_position_ratio']
            max_buy_value = min(max_buy_value_by_ratio, params['max_position_value'], remaining_position_budget)
            
            if max_buy_value < params['min_position_value']:
                if available_cash >= params['min_position_value']:
                    max_buy_value = params['min_position_value']
                else:
                    logger.warning(
                        f"{symbol}: 可用资金{available_cash:.2f}元不足最小持仓金额{params['min_position_value']:.2f}元，不买入（返回0）"
                    )
                    try:
                        record_trade_event(
                            event_type="买入失败",
                            symbol=symbol,
                            side="买",
                            reason=(
                                f"可用资金{available_cash:.2f}元不足最小持仓金额"
                                f"{params['min_position_value']:.2f}元，不买入（返回0）"
                            ),
                            extra={
                                "可用资金": float(available_cash),
                                "最小持仓金额": float(params["min_position_value"]),
                            },
                        )
                    except Exception:
                        pass
                    return 0
            
            commission_rate = 0.0003
            max_shares = int(max_buy_value / (current_price * (1 + commission_rate)))
            shares = (max_shares // min_unit) * min_unit

            # 限制单笔最大委托数量（科创板10万股，普通A股100万股）
            if shares > max_single_order_shares:
                shares = (max_single_order_shares // min_unit) * min_unit
                logger.info(
                    f"{symbol}: 计算股数{max_shares}超过单笔最大委托{max_single_order_shares}股，"
                    f"已截断为{shares}股"
                )

            if shares < min_unit:
                shares = min_unit
            
            final_cost = shares * current_price * (1 + commission_rate)
            if final_cost > available_cash:
                max_affordable_shares = int(available_cash / (current_price * (1 + commission_rate)))
                shares = (max_affordable_shares // min_unit) * min_unit
                if shares < min_unit:
                    logger.warning(f"{symbol}: 可用资金{available_cash:.2f}元不足，无法买入最小单位{min_unit}股")
                    return 0
            
            final_value = shares * current_price
            if final_value < params['min_position_value']:
                logger.warning(f"{symbol}: 最终买入金额{final_value:.2f}元低于最小持仓金额{params['min_position_value']:.2f}元，不买入")
                return 0
            
            logger.info(f"{symbol}: 计算买入股数 - 可用资金={available_cash:.2f}, 价格={current_price:.2f}, "
                       f"建议股数={shares}, 预计金额={shares * current_price:.2f}")
            return shares
            
        except Exception as e:
            logger.error(f"{symbol}: 计算买入股数失败: {e}，不买入（返回0）", exc_info=True)
            return 0
    
    def get_cached_params(self) -> Optional[Dict[str, float]]:
        """获取缓存的参数（避免频繁查询账户资产）"""
        return self._cached_params
    
    def refresh_params(self, fear_greed_index: Optional[float] = None) -> Dict[str, float]:
        """刷新参数（重新查询账户资产）"""
        return self.get_position_params(fear_greed_index)
