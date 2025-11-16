#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XtQuant持仓分析演示脚本

演示从XtQuant获取持仓数据并进行技术分析的功能，包括：
1. 从XtQuant获取持仓数据
2. 技术指标计算
3. 交易信号生成
4. 买卖建议
"""

import asyncio
import json
from typing import List, Dict
import config.ConfigServer as Cs

from modules.tornadoapp.position.xtquant_position_manager import XtQuantPositionManager

def create_sample_positions() -> List[Dict]:
    """创建示例持仓数据"""
    return [
        {
            "symbol": "000001.SZ",  # 平安银行
            "volume": 1000,
            "available_volume": 1000,
            "avg_price": 15.50,
            "current_price": 16.20
        },
        {
            "symbol": "000002.SZ",  # 万科A
            "volume": 500,
            "available_volume": 500,
            "avg_price": 25.80,
            "current_price": 24.50
        },
        {
            "symbol": "600519.SH",  # 贵州茅台
            "volume": 200,
            "available_volume": 200,
            "avg_price": 1800.00,
            "current_price": 1850.00
        },
        {
            "symbol": "000858.SZ",  # 五粮液
            "volume": 300,
            "available_volume": 300,
            "avg_price": 120.50,
            "current_price": 118.80
        },
        {
            "symbol": "002415.SZ",  # 海康威视
            "volume": 400,
            "available_volume": 400,
            "avg_price": 35.20,
            "current_price": 38.50
        }
    ]

async def demo_xtquant_analysis():
    """演示XtQuant持仓分析功能"""
    print("=" * 60)
    print("XtQuant持仓分析模块演示")
    print("=" * 60)
    
    # 获取配置
    tushare_token = Cs.getTushareToken()
    
    if not tushare_token:
        print("警告: 未找到Tushare token，将使用模拟数据")
        tushare_token = "demo_token"
    
    # 创建XtQuant持仓管理器
    position_manager = XtQuantPositionManager(tushare_token)
    
    # 模拟账户ID
    account_id = "demo_account"
    
    print(f"\n📊 分析XtQuant持仓数据...")
    print(f"账户ID: {account_id}")
    
    # 分析所有持仓
    analysis_results = await position_manager.analyze_all_positions(account_id)
    
    # 显示分析结果
    print("\n" + "=" * 40)
    print("📈 技术分析结果")
    print("=" * 40)
    
    # 汇总信息
    summary = analysis_results['summary']
    print(f"总持仓数量: {summary['total_positions']}")
    print(f"买入信号: {summary['buy_signals']}")
    print(f"卖出信号: {summary['sell_signals']}")
    print(f"持有信号: {summary['hold_signals']}")
    
    # 显示每个持仓的分析结果
    print(f"\n📋 持仓详细分析:")
    for i, position in enumerate(analysis_results['positions'], 1):
        symbol = position['symbol']
        current_price = position['current_price']
        avg_price = position['avg_price']
        signals = position['signals']
        indicators = position['indicators']
        
        print(f"\n{i}. {symbol}")
        print(f"   当前价格: ¥{current_price:.2f}")
        print(f"   平均成本: ¥{avg_price:.2f}")
        print(f"   盈亏率: {((current_price - avg_price) / avg_price * 100):.2f}%")
        print(f"   交易信号: {signals['action'].upper()}")
        print(f"   置信度: {signals['confidence']:.2f}")
        print(f"   目标价格: ¥{signals['target_price']:.2f}")
        print(f"   止损价格: ¥{signals['stop_loss']:.2f}")
        print(f"   信号原因: {', '.join(signals['reasons'])}")
        
        # 显示关键指标
        if indicators:
            print(f"   技术指标:")
            print(f"     RSI: {indicators.get('rsi', 0):.2f}")
            print(f"     MACD: {indicators.get('macd', 0):.4f}")
            print(f"     MA20: {indicators.get('ma20', 0):.2f}")
            print(f"     KDJ-K: {indicators.get('kdj_k', 0):.2f}")
            print(f"     KDJ-D: {indicators.get('kdj_d', 0):.2f}")
            print(f"     布林带位置: {indicators.get('price_position', 0.5):.2f}")
    
    # 生成交易建议
    print(f"\n💡 交易建议:")
    recommendations = position_manager.generate_trading_recommendations(analysis_results)
    
    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['symbol']} - {rec['action'].upper()}")
            print(f"   置信度: {rec['confidence']:.2f}")
            print(f"   当前价格: ¥{rec['current_price']:.2f}")
            print(f"   目标价格: ¥{rec['target_price']:.2f}")
            print(f"   止损价格: ¥{rec['stop_loss']:.2f}")
            print(f"   原因: {', '.join(rec['reasons'])}")
            print(f"   关键指标: RSI={rec['key_indicators']['rsi']:.2f}, "
                  f"MACD={rec['key_indicators']['macd']:.4f}, "
                  f"趋势={rec['key_indicators']['ma_trend']}")
    else:
        print("暂无明确的交易建议")
    
    # 演示单个股票分析
    print(f"\n🔍 单个股票技术分析演示:")
    sample_positions = create_sample_positions()
    if sample_positions:
        test_position = sample_positions[0]
        single_analysis = await position_manager.analyze_position_with_technical_analysis(test_position)
        
        print(f"股票: {single_analysis['symbol']}")
        print(f"当前价格: ¥{single_analysis['current_price']:.2f}")
        print(f"平均成本: ¥{single_analysis['avg_price']:.2f}")
        print(f"交易信号: {single_analysis['signals']['action'].upper()}")
        print(f"置信度: {single_analysis['signals']['confidence']:.2f}")
        print(f"信号原因: {', '.join(single_analysis['signals']['reasons'])}")
        
        if single_analysis['indicators']:
            print(f"技术指标详情:")
            for key, value in single_analysis['indicators'].items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
    
    print(f"\n" + "=" * 60)
    print("🎉 XtQuant持仓分析演示完成!")
    print("=" * 60)

def demo_api_endpoints():
    """演示API端点"""
    print("\n🌐 XtQuant技术分析API端点演示:")
    print("=" * 50)
    
    endpoints = [
        {
            "method": "GET",
            "url": "/api/technical/analysis?account_id=demo",
            "description": "获取所有持仓的技术分析"
        },
        {
            "method": "GET",
            "url": "/api/technical/analysis?account_id=demo&symbol=000001.SZ",
            "description": "获取特定股票的技术分析"
        },
        {
            "method": "POST",
            "url": "/api/technical/analysis",
            "description": "提交持仓数据进行技术分析",
            "body": {
                "account_id": "demo",
                "positions": create_sample_positions()
            }
        },
        {
            "method": "GET",
            "url": "/api/technical/signals?account_id=demo&min_confidence=0.7",
            "description": "获取高置信度交易信号"
        },
        {
            "method": "GET",
            "url": "/api/technical/indicators?symbol=000001.SZ&days=60",
            "description": "获取技术指标分析"
        }
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"{i}. {endpoint['method']} {endpoint['url']}")
        print(f"   {endpoint['description']}")
        if 'body' in endpoint:
            print(f"   Body: {json.dumps(endpoint['body'], ensure_ascii=False)}")
        print()

def demo_technical_indicators():
    """演示技术指标计算"""
    print("\n📊 技术指标计算演示:")
    print("=" * 40)
    
    # 获取配置
    config_data = Cs.returnConfigData()
    tushare_token = config_data.get("toshare_token", "")
    
    if not tushare_token:
        print("警告: 未找到Tushare token，无法演示技术指标计算")
        return
    
    position_manager = XtQuantPositionManager(tushare_token)
    
    async def test_indicators():
        # 测试获取历史数据
        symbol = "000001.SZ"
        print(f"获取 {symbol} 的历史数据...")
        
        df = await position_manager.get_historical_data(symbol, days=30)
        if not df.empty:
            print(f"✅ 成功获取 {len(df)} 条历史数据")
            
            # 计算技术指标
            indicators = position_manager.calculate_technical_indicators(df)
            if indicators:
                print(f"✅ 成功计算技术指标:")
                for key, value in indicators.items():
                    if isinstance(value, float):
                        print(f"  {key}: {value:.4f}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print("❌ 技术指标计算失败")
        else:
            print(f"❌ 无法获取 {symbol} 的历史数据")
    
    asyncio.run(test_indicators())

if __name__ == "__main__":
    print("🚀 启动XtQuant持仓分析演示...")
    
    # 运行演示
    asyncio.run(demo_xtquant_analysis())
    
    # 演示技术指标计算
    demo_technical_indicators()
    
    # 显示API端点
    demo_api_endpoints()
    
    print("\n📝 使用说明:")
    print("1. 启动Web服务器: python main.py")
    print("2. 访问技术分析API端点")
    print("3. 根据技术分析结果进行交易决策")
    print("4. 注意风险控制，技术分析仅供参考")
    
    print("\n⚠️ 风险提示:")
    print("- 技术分析仅供参考，不构成投资建议")
    print("- 请结合基本面分析和其他因素综合判断")
    print("- 投资有风险，入市需谨慎") 