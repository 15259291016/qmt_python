# coding=utf-8
"""
动态持仓管理器
根据账户资金体量自动调整持仓参数，实现智能资金管理
"""
import logging
from typing import Dict, Optional, Tuple
from xtquant.xttype import StockAccount

logger = logging.getLogger(__name__)


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
        (50000, 2, 10000, 25000, 0.50),       # < 5万：1-2只，超集中持仓（单股1万，成本0.20%）
        (100000, 3, 10000, 35000, 0.35),      # 5-10万：2-3只，集中持仓
        (500000, 10, 10000, 80000, 0.15),     # 10-50万：5-10只，适度分散
        (1000000, 15, 20000, 150000, 0.12),   # 50-100万：8-15只，良好分散
        (5000000, 20, 50000, 500000, 0.10),   # 100-500万：12-20只，充分分散
        (10000000, 25, 100000, 1000000, 0.08), # 500-1000万：15-25只，高度分散
        (50000000, 30, 200000, 3000000, 0.08), # 1000-5000万：20-30只，专业级分散（适合2500万）
        (float('inf'), 40, 500000, 5000000, 0.06), # > 5000万：30-40只，机构级分散
    ]
    
    def __init__(self, xt_trader, account: StockAccount):
        """
        初始化动态持仓管理器
        
        Args:
            xt_trader: 交易接口对象
            account: 股票账户对象
        """
        self.xt_trader = xt_trader
        self.account = account
        self._cached_total_asset = None
        self._cached_params = None
        
    def get_total_asset(self) -> float:
        """
        获取账户总资产（含持仓市值）
        
        Returns:
            float: 总资产金额（元）
        """
        try:
            asset = self.xt_trader.query_stock_asset(self.account)
            
            # 获取可用资金
            available_cash = getattr(asset, 'cash', 0) or getattr(asset, 'available_cash', 0)
            
            # 获取持仓市值
            market_value = getattr(asset, 'market_value', 0) or 0
            
            # 总资产 = 可用资金 + 持仓市值
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
    
    def get_position_params(
        self, 
        fear_greed_index: Optional[float] = None
    ) -> Dict[str, float]:
        """
        根据账户资金体量获取持仓参数
        
        Args:
            fear_greed_index: 恐贪指数（0-100），用于微调参数
        
        Returns:
            Dict: 持仓参数字典
                {
                    'max_stocks': 最大持股数量,
                    'min_position_value': 单股最小持仓金额,
                    'max_position_value': 单股最大持仓金额,
                    'max_position_ratio': 单股最大仓位比例,
                    'total_asset': 账户总资产
                }
        """
        # 获取账户总资产
        total_asset = self.get_total_asset()
        
        # 根据资金体量确定基础参数
        base_params = self._get_base_params_by_asset(total_asset)
        
        # 根据恐贪指数微调参数
        if fear_greed_index is not None:
            adjusted_params = self._adjust_params_by_fear_greed(base_params, fear_greed_index)
        else:
            adjusted_params = base_params
        
        # 添加总资产信息
        adjusted_params['total_asset'] = total_asset
        
        # 缓存参数
        self._cached_params = adjusted_params
        
        # 输出参数信息
        logger.info(
            f"[资金管理] 持仓参数: 总资产={total_asset:.0f}元, "
            f"最大持股={adjusted_params['max_stocks']}只, "
            f"单股范围={adjusted_params['min_position_value']:.0f}-{adjusted_params['max_position_value']:.0f}元, "
            f"最大仓位={adjusted_params['max_position_ratio']*100:.0f}%"
        )
        
        return adjusted_params
    
    def _get_base_params_by_asset(self, total_asset: float) -> Dict[str, float]:
        """
        根据资金体量确定基础参数
        
        Args:
            total_asset: 账户总资产
        
        Returns:
            Dict: 基础参数字典
        """
        # 遍历配置，找到对应的资金分级
        for asset_limit, max_stocks, min_value, max_value, max_ratio in self.TIER_CONFIG:
            if total_asset <= asset_limit:
                return {
                    'max_stocks': max_stocks,
                    'min_position_value': min_value,
                    'max_position_value': max_value,
                    'max_position_ratio': max_ratio
                }
        
        # 默认返回最高级别配置（理论上不会到这里）
        return {
            'max_stocks': 30,
            'min_position_value': 100000,
            'max_position_value': 1000000,
            'max_position_ratio': 0.08
        }
    
    def _adjust_params_by_fear_greed(
        self, 
        base_params: Dict[str, float], 
        fear_greed_index: float
    ) -> Dict[str, float]:
        """
        根据恐贪指数微调参数
        
        策略：
        - 恐慌市场（<20）：降低持股数量至70%，集中资金
        - 正常市场（20-80）：使用基础参数
        - 贪婪市场（>80）：降低持股数量至80%，控制风险
        
        Args:
            base_params: 基础参数
            fear_greed_index: 恐贪指数（0-100）
        
        Returns:
            Dict: 调整后的参数
        """
        adjusted_params = base_params.copy()
        
        # 根据恐贪指数调整最大持股数量
        if fear_greed_index < 20:  # 恐慌市场
            adjusted_params['max_stocks'] = int(base_params['max_stocks'] * 0.7)
            logger.info(f"[资金管理] 恐慌市场（恐贪指数={fear_greed_index:.1f}），降低最大持股数量至{adjusted_params['max_stocks']}只")
        elif fear_greed_index > 80:  # 贪婪市场
            adjusted_params['max_stocks'] = int(base_params['max_stocks'] * 0.8)
            logger.info(f"[资金管理] 贪婪市场（恐贪指数={fear_greed_index:.1f}），控制最大持股数量至{adjusted_params['max_stocks']}只")
        
        # 确保至少持有1只股票
        adjusted_params['max_stocks'] = max(1, adjusted_params['max_stocks'])
        
        return adjusted_params
    
    def calculate_buy_amount(
        self,
        symbol: str,
        current_price: float,
        params: Optional[Dict[str, float]] = None
    ) -> int:
        """
        计算合理的买入股数
        
        Args:
            symbol: 股票代码
            current_price: 当前价格
            params: 持仓参数（可选，如果不提供则自动获取）
        
        Returns:
            int: 建议买入股数（已调整为100的整数倍）
        """
        # 如果没有提供参数，使用缓存或重新获取
        if params is None:
            if self._cached_params is None:
                params = self.get_position_params()
            else:
                params = self._cached_params
        
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
        
        # 如果价格无效，返回最小买入单位
        if current_price is None or current_price <= 0:
            return min_unit
        
        try:
            # 2. 查询账户可用资金
            asset = self.xt_trader.query_stock_asset(self.account)
            available_cash = getattr(asset, 'cash', 0) or getattr(asset, 'available_cash', 0)
            
            if available_cash <= 0:
                logger.warning(f"{symbol}: 账户可用资金为0或无法获取，返回最小买入单位 {min_unit}")
                return min_unit
            
            # 3. 计算基于资金限制的最大可买金额
            # 考虑单只股票最大仓位比例
            max_buy_value_by_ratio = available_cash * params['max_position_ratio']
            
            # 考虑最大持仓金额限制
            max_buy_value = min(max_buy_value_by_ratio, params['max_position_value'])
            
            # 确保不低于最小持仓金额
            if max_buy_value < params['min_position_value']:
                logger.debug(f"{symbol}: 计算出的最大买入金额({max_buy_value:.2f})小于最小持仓金额({params['min_position_value']:.2f})")
                # 如果可用资金足够，使用最小持仓金额
                if available_cash >= params['min_position_value']:
                    max_buy_value = params['min_position_value']
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
                    logger.warning(f"{symbol}: 可用资金{available_cash:.2f}元不足，无法买入最小单位{min_unit}股")
                    return 0  # 修复：返回0表示不买入
            
            # 8. 最终验证：确保买入金额不低于最小持仓金额
            final_value = shares * current_price
            if final_value < params['min_position_value']:
                logger.warning(f"{symbol}: 最终买入金额{final_value:.2f}元低于最小持仓金额{params['min_position_value']:.2f}元，不买入")
                return 0  # 返回0表示不买入
            
            logger.info(f"{symbol}: 计算买入股数 - 可用资金={available_cash:.2f}, 价格={current_price:.2f}, "
                       f"建议股数={shares}, 预计金额={shares * current_price:.2f}")
            
            return shares
            
        except Exception as e:
            logger.error(f"{symbol}: 计算买入股数失败: {e}，返回最小买入单位 {min_unit}", exc_info=True)
            return min_unit
    
    def get_cached_params(self) -> Optional[Dict[str, float]]:
        """
        获取缓存的参数（避免频繁查询账户资产）
        
        Returns:
            Optional[Dict]: 缓存的参数，如果没有缓存则返回None
        """
        return self._cached_params
    
    def refresh_params(self, fear_greed_index: Optional[float] = None) -> Dict[str, float]:
        """
        刷新参数（重新查询账户资产）
        
        Args:
            fear_greed_index: 恐贪指数（0-100）
        
        Returns:
            Dict: 刷新后的参数
        """
        return self.get_position_params(fear_greed_index)

