STRATEGY_CONFIG = [
    {'name': 'ma_5_20', 'class': 'MAStrategy', 'params': {'short': 5, 'long': 20}},
    {'name': 'ma_10_30', 'class': 'MAStrategy', 'params': {'short': 10, 'long': 30}},
    {'name': 'ma_15_60', 'class': 'MAStrategy', 'params': {'short': 15, 'long': 60}},
    {'name': 'byd_strategy', 'class': 'BYDStrategy', 'params': {}},
    {'name': 'byd_enhanced', 'class': 'BYDEnhancedStrategy', 'params': {}},
    {'name': 'byd_conservative', 'class': 'BYDConservativeStrategy', 'params': {}},
    # 可扩展更多策略
] 