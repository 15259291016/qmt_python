# coding=utf-8
"""买入价格与分时高点判断工具。"""

from __future__ import annotations

import logging
import math
from typing import Optional

logger = logging.getLogger(__name__)


def get_optimized_buy_price(symbol: str, last_price: float, market_trend: str = 'neutral') -> Optional[float]:
    """
    根据分时K线和VWAP判断当前是否处于局部高点，避免买在山峰。

    逻辑改为“分级处理”而不是一刀切：
    - bull：适度放宽乖离限制，允许强势突破但避免过热
    - neutral：保持中性阈值
    - bear：收紧乖离限制，尽量避免追高

    处理方式：
    - 轻微乖离：降低挂单价，不直接拦截
    - 中度乖离：继续压价，但允许试仓
    - 严重乖离/冲高回落：直接跳过买入

    Returns:
        float: 优化挂单价（低于现价，不在严重高点时）
        None:  当前处于严重高点，跳过买入，等待回调
    """
    try:
        from xtquant import xtdata

        trend_key = (market_trend or 'neutral').lower()
        trend_params = {
            'bull': {'vwap_peak': 2.0, 'avg_peak': 2.5, 'rise_peak': 1.8},
            'neutral': {'vwap_peak': 1.2, 'avg_peak': 1.5, 'rise_peak': 1.0},
            'bear': {'vwap_peak': 0.8, 'avg_peak': 1.0, 'rise_peak': 0.7},
        }.get(trend_key, {'vwap_peak': 1.2, 'avg_peak': 1.5, 'rise_peak': 1.0})

        bars = xtdata.get_market_data(
            field_list=['close', 'high', 'low', 'volume', 'amount'],
            stock_list=[symbol],
            period='1m',
            count=30,
        )

        closes = []
        bar_volumes = []
        bar_amounts = []
        if bars and 'close' in bars and symbol in bars['close']:
            raw_close = bars['close'][symbol]
            raw_volume = bars.get('volume', {}).get(symbol, [])
            raw_amount = bars.get('amount', {}).get(symbol, [])
            for i, v in enumerate(raw_close):
                if v is not None and float(v) > 0:
                    closes.append(float(v))
                    vol = float(raw_volume[i]) if i < len(raw_volume) and raw_volume[i] else 0
                    amt = float(raw_amount[i]) if i < len(raw_amount) and raw_amount[i] else 0
                    bar_volumes.append(vol)
                    bar_amounts.append(amt)

        if len(closes) < 6:
            logger.debug(f"[分时高点] {symbol}: 分时K线不足（{len(closes)}根），将仅使用tick判断")
            closes = []

        tick_info = xtdata.get_full_tick([symbol])
        tick = tick_info.get(symbol) if tick_info else None

        bid1 = last_price
        tick_vwap = None
        if tick:
            bid_prices = tick.get('bidPrice', [])
            if bid_prices and float(bid_prices[0]) > 0:
                bid1 = float(bid_prices[0])
            t_amount = float(tick.get('amount', 0) or 0)
            t_volume = float(tick.get('volume', 0) or 0)
            t_volume_shares = t_volume * 100
            if t_volume_shares > 0 and t_amount > 0:
                tick_vwap = t_amount / t_volume_shares

        bar_vwap = None
        if closes and sum(bar_volumes) > 0:
            total_amt = sum(bar_amounts)
            total_vol = sum(bar_volumes)
            if total_vol > 0 and total_amt > 0:
                bar_vwap = total_amt / total_vol

        vwap = tick_vwap or bar_vwap or last_price

        # 分级高点判断
        vwap_dev_pct = (last_price - vwap) / vwap * 100 if vwap > 0 else 0.0
        avg_dev_pct = 0.0
        rise_5bar_pct = 0.0
        recent20 = []
        recent5 = []
        avg20 = None
        high20 = None

        if closes:
            recent20 = closes[-20:] if len(closes) >= 20 else closes
            recent5 = closes[-5:] if len(closes) >= 5 else closes
            avg20 = sum(recent20) / len(recent20)
            high20 = max(recent20)
            avg_dev_pct = (last_price - avg20) / avg20 * 100 if avg20 > 0 else 0.0
            rise_5bar_pct = (last_price - recent5[0]) / recent5[0] * 100 if recent5[0] > 0 else 0.0

        severe_peak = False
        moderate_peak = False
        peak_reason = ""

        # 严重乖离：直接拦截
        if vwap_dev_pct > trend_params['vwap_peak'] * 1.5:
            severe_peak = True
            peak_reason = (
                f"严重高于VWAP（当前{last_price:.2f} vs VWAP{vwap:.2f}，乖离{vwap_dev_pct:.2f}%）"
            )
        elif avg20 is not None and avg_dev_pct > trend_params['avg_peak'] * 1.5:
            severe_peak = True
            peak_reason = (
                f"严重高于近期均价（当前{last_price:.2f} vs 近20根均价{avg20:.2f}，乖离{avg_dev_pct:.2f}%）"
            )
        elif closes:
            price_5bar_ago = recent5[0] if recent5 else last_price
            was_below_avg = avg20 is not None and price_5bar_ago < avg20
            is_new_high = high20 is not None and last_price >= high20 * 0.998
            if rise_5bar_pct > trend_params['rise_peak'] * 1.5 and avg20 is not None and last_price > avg20:
                severe_peak = True
                peak_reason = (
                    f"近5根快速拉升过快（涨幅{rise_5bar_pct:.2f}%）且高于均价{avg20:.2f}"
                )
            elif is_new_high and was_below_avg:
                severe_peak = True
                peak_reason = (
                    f"V形拉升顶部（5根前价格{price_5bar_ago:.2f}<均价{avg20:.2f}，当前{last_price:.2f}接近近20根新高{high20:.2f}）"
                )

        # 中度乖离：压价但不拦截
        if not severe_peak:
            if vwap_dev_pct > trend_params['vwap_peak']:
                moderate_peak = True
                peak_reason = (
                    f"当前价高于VWAP（{vwap_dev_pct:.2f}%），按市场状态{trend_key}压价"
                )
            elif avg20 is not None and avg_dev_pct > trend_params['avg_peak']:
                moderate_peak = True
                peak_reason = (
                    f"当前价高于近20根均价（{avg_dev_pct:.2f}%），按市场状态{trend_key}压价"
                )
            elif closes and rise_5bar_pct > trend_params['rise_peak']:
                moderate_peak = True
                peak_reason = (
                    f"近5根快速上涨（{rise_5bar_pct:.2f}%），按市场状态{trend_key}压价"
                )

        if severe_peak:
            logger.warning(f"[分时高点] {symbol}: 严重高点，暂不买入。原因: {peak_reason}")
            print(f"[分时高点] {symbol}: 当前价={last_price:.2f}，处于严重高点，暂不买入。\n  原因: {peak_reason}")
            return None

        is_below_vwap = last_price < vwap
        base_price = bid1 if bid1 <= vwap else (bid1 + vwap) / 2

        if trend_key == 'bull':
            min_price = round(last_price * (0.998 if is_below_vwap else 0.996), 2)
        elif trend_key == 'bear':
            min_price = round(last_price * (0.996 if is_below_vwap else 0.993), 2)
        else:
            min_price = round(last_price * (0.997 if is_below_vwap else 0.995), 2)

        optimized = max(min_price, min(base_price, last_price))
        optimized = math.floor(optimized * 100) / 100
        if optimized < min_price:
            optimized = min_price

        logger.info(
            f"[优化挂单价] {symbol}: 市场={trend_key}, 最新价={last_price:.2f}, VWAP={vwap:.2f}(乖离{vwap_dev_pct:.2f}%), "
            f"买一={bid1:.2f}, 级别={'中度乖离' if moderate_peak else '正常'}, 挂单价={optimized:.2f}"
        )
        return optimized

    except Exception as e:
        logger.warning(f"[优化挂单价] {symbol}: 计算失败({e})，使用最新价 {last_price:.2f}")
        return last_price
