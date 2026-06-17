# coding=utf-8
"""
市场择时策略配置文件
用户可以根据自己的风险偏好调整这些参数
"""

# ========== 基础配置 ==========
MARKET_TIMING_CONFIG = {
    # 市场指数
    'index_code': '000001.SH',  # 上证指数
    
    # 时间控制
    'check_interval': 30,  # 市场检查间隔（秒）
    'min_buy_interval': 180,  # 最小买入间隔（秒），防止频繁交易
    
    # 市场状态买入激进程度（越大越敢买）
    'market_aggressiveness': {
        'bull': 1.20,     # 牛市：更积极
        'neutral': 1.00,  # 震荡市：标准
        'bear': 0.80,     # 熊市：更保守
    },
    
    # 启动型强势票独立通道
    'breakout': {
        'enabled': True,
        'min_market_trend': 'neutral',   # bull/neutral 才允许
        'min_score': 78.0,               # 启动型票最低总分
        'min_trend_score': 70.0,         # 趋势分门槛
        'min_volume_score': 65.0,        # 量能分门槛
        'min_rs_score': 60.0,            # 相对强弱门槛
        'max_daily_rise_pct': 8.0,       # 日内涨幅过大则不追
        'min_breakout_high_pct': 0.0,    # 突破前高/20日高点的最小要求
    },
    
    # 信号阈值（降低阈值=更容易买入，提高阈值=更谨慎）
    'thresholds': {
        'strong': 0.55,   # 强买入信号阈值（原0.6）
        'medium': 0.35,   # 中等买入信号阈值（原0.4）
        'weak': 0.15      # 弱买入信号阈值（原0.25，降低40%更容易触发）
    },
    
    # ========== 权重配置（总和应为100%） ==========
    'weights': {
        'ma_system': 0.25,      # 均线系统权重 25%
        'rsi': 0.30,            # RSI指标权重 30%（提高，让超卖更重要）
        'price_change': 0.20,   # 价格跌幅权重 20%（新增）
        'macd': 0.15,           # MACD指标权重 15%
        'volume': 0.10,         # 成交量权重 10%
        'fear_greed': 0.15      # 市场情绪权重 15%（提高）
    },
    
    # ========== 均线系统配置 ==========
    'ma_system': {
        'golden_cross': 0.25,        # 均线金叉得分
        'bullish_alignment': 0.18,   # 多头排列得分
        'price_above_ma5': 0.12,     # 价格站上MA5得分
        'near_ma20': 0.08,           # 价格接近MA20得分
        'near_ma60': 0.10,           # 价格接近MA60得分（新增，识别低点）
        'near_ma20_threshold': 0.02, # MA20支撑判断阈值（±2%）
        'near_ma60_threshold': 0.03  # MA60支撑判断阈值（±3%）
    },
    
    # ========== RSI配置 ==========
    'rsi': {
        'extreme_oversold': {       # 极度超卖（RSI < 25）
            'threshold': 25,
            'score': 0.30           # 限制在30%权重内
        },
        'oversold': {               # 超卖（RSI < 30）
            'threshold': 30,
            'score': 0.25
        },
        'weak': {                   # 偏弱（30 <= RSI < 35）
            'threshold': 35,
            'score': 0.18
        },
        'neutral_weak': {           # 中性偏弱（35 <= RSI < 45）
            'threshold': 45,
            'score': 0.10
        }
    },
    
    # ========== 价格跌幅配置 ==========
    'price_change': {
        'sharp_drop': {             # 大幅下跌（跌幅 > 8%）
            'threshold': -8,
            'score': 0.20
        },
        'significant_drop': {       # 明显下跌（跌幅 > 5%）
            'threshold': -5,
            'score': 0.15
        },
        'moderate_drop': {          # 小幅下跌（跌幅 > 3%）
            'threshold': -3,
            'score': 0.10
        },
        'stabilization': {          # 止跌企稳（-1% <= 跌幅 <= 1%）
            'threshold_low': -1,
            'threshold_high': 1,
            'score': 0.05
        }
    },
    
    # ========== MACD配置 ==========
    'macd': {
        'golden_cross': 0.12,       # MACD金叉得分
        'histogram_positive': 0.03  # MACD柱状图转正得分
    },
    
    # ========== 成交量配置 ==========
    'volume': {
        'ratio_threshold': 1.2,     # 放量判断阈值（量比 > 1.2）
        'volume_up': 0.10,          # 放量上涨得分
        'volume_down': 0.08,        # 放量下跌得分（恐慌性抛售，反而是机会）
        'volume_normal': 0.03       # 正常放量得分
    },
    
    # ========== 市场情绪配置（恐贪指数） ==========
    'fear_greed': {
        'extreme_fear': {           # 极度恐慌（恐贪指数 < 20）
            'threshold': 20,
            'score': 0.15           # 限制在15%权重内
        },
        'fear': {                   # 恐慌（恐贪指数 < 30）
            'threshold': 30,
            'score': 0.12
        },
        'weak': {                   # 偏弱（恐贪指数 < 40）
            'threshold': 40,
            'score': 0.08
        },
        'neutral_weak': {           # 中性偏弱（恐贪指数 < 50）
            'threshold': 50,
            'score': 0.04
        }
    }
}

# ========== 选股时间段配置 ==========
STOCK_SELECTION_PERIODS = [
    ('09:45', '10:15'),  # 早盘：30分钟，避开开盘剧烈波动
    ('10:30', '11:00'),  # 上午：30分钟，捕捉上午回调
    ('13:15', '13:45'),  # 午后：30分钟，避开午盘开盘波动
    ('14:00', '14:30')   # 下午：30分钟，避开尾盘波动
]

# ========== 市场广度修正配置 ==========
MARKET_BREADTH_CONFIG = {
    # 当上涨家数占比达到该阈值时，即使指数趋势偏空，也可放开上午买入窗口
    'morning_buy_override_up_ratio': 0.68,
    # 市场广度因子在综合市场趋势得分中的权重
    'breadth_weight': 0.25,
}

# ========== 候选股二次评分配置 ==========
STOCK_RANKING_CONFIG = {
    # 最终保留的候选数量
    'top_n': 3,
    # 过滤门槛
    'min_total_score': 70.0,
    'min_trend_score': 60.0,
    'min_volume_score': 50.0,
    # 分项权重（总和建议为1.0）
    'weights': {
        'trend': 0.30,
        'volume': 0.20,
        'rs': 0.20,
        'risk': 0.15,
        'liquidity': 0.15,
    }
}

# ========== 风险偏好预设 ==========
# 用户可以选择不同的风险偏好，系统会自动调整参数

RISK_PROFILES = {
    # 保守型：更高的阈值，更少的买入
    'conservative': {
        'thresholds': {
            'strong': 0.65,
            'medium': 0.45,
            'weak': 0.25
        },
        'min_buy_interval': 300  # 5分钟
    },
    
    # 平衡型：当前配置
    'balanced': {
        'thresholds': {
            'strong': 0.55,
            'medium': 0.35,
            'weak': 0.15
        },
        'min_buy_interval': 180  # 3分钟
    },
    
    # 激进型：更低的阈值，更多的买入
    'aggressive': {
        'thresholds': {
            'strong': 0.45,
            'medium': 0.25,
            'weak': 0.10
        },
        'min_buy_interval': 120  # 2分钟
    }
}

# ========== 使用说明 ==========
"""
如何调整策略参数：

1. 调整买入频率：
   - 更频繁买入：降低 thresholds['weak'] 从 0.15 到 0.10
   - 更谨慎买入：提高 thresholds['weak'] 从 0.15 到 0.20

2. 调整对低点的敏感度：
   - 更敏感：提高 weights['rsi'] 和 weights['price_change']
   - 更保守：降低 weights['rsi'] 和 weights['price_change']

3. 调整买入间隔：
   - 更频繁：降低 min_buy_interval 从 180 到 120
   - 更谨慎：提高 min_buy_interval 从 180 到 300

4. 使用风险偏好预设：
   在初始化时指定：
   MarketTimingEngine(risk_profile='conservative')  # 保守型
   MarketTimingEngine(risk_profile='balanced')      # 平衡型（默认）
   MarketTimingEngine(risk_profile='aggressive')    # 激进型

5. 调整选股时间段：
   修改 STOCK_SELECTION_PERIODS，增加或减少时间窗口

示例：
# 更激进的配置（更容易在低点买入）
MARKET_TIMING_CONFIG['thresholds']['weak'] = 0.10
MARKET_TIMING_CONFIG['weights']['rsi'] = 0.35
MARKET_TIMING_CONFIG['min_buy_interval'] = 120

# 更保守的配置（只在明确低点买入）
MARKET_TIMING_CONFIG['thresholds']['weak'] = 0.25
MARKET_TIMING_CONFIG['weights']['rsi'] = 0.25
MARKET_TIMING_CONFIG['min_buy_interval'] = 300
"""



