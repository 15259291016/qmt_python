#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
持仓分析演示脚本

演示持仓分析模块的各项功能，包括：
1. 持仓数据分析
2. 风险指标计算
3. 可视化图表生成
4. 报告生成
"""

import asyncio
import json
from typing import List, Dict
import configs.ConfigServer as Cs

from modules.tornadoapp.position.position_analyzer import PositionAnalyzer
from modules.tornadoapp.position.position_visualizer import PositionVisualizer
from modules.tornadoapp.model.position_model import PositionAnalysis

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
        },
        {
            "symbol": "300059.SZ",  # 东方财富
            "volume": 600,
            "available_volume": 600,
            "avg_price": 28.90,
            "current_price": 26.30
        }
    ]

async def demo_position_analysis():
    """演示持仓分析功能"""
    print("=" * 60)
    print("持仓分析模块演示")
    print("=" * 60)
    
    # 获取配置
    config_data = Cs.returnConfigData()
    tushare_token = config_data.get("toshare_token", "")
    
    if not tushare_token:
        print("警告: 未找到Tushare token，将使用模拟价格数据")
        tushare_token = "demo_token"
    
    # 创建分析器和可视化工具
    analyzer = PositionAnalyzer(tushare_token)
    visualizer = PositionVisualizer()
    
    # 创建示例持仓数据
    positions_data = create_sample_positions()
    cash = 50000.0  # 现金
    
    print(f"\n📊 分析持仓数据...")
    print(f"持仓数量: {len(positions_data)}")
    print(f"现金: ¥{cash:,.2f}")
    
    # 分析持仓
    analysis = await asyncio.get_event_loop().run_in_executor(
        None, analyzer.analyze_positions, positions_data, cash
    )
    
    # 显示分析结果
    print("\n" + "=" * 40)
    print("📈 持仓分析结果")
    print("=" * 40)
    
    # 汇总信息
    summary = analysis.summary
    print(f"总持仓数量: {summary.total_positions}")
    print(f"总市值: ¥{summary.total_market_value:,.2f}")
    print(f"总成本: ¥{summary.total_cost_value:,.2f}")
    print(f"总未实现盈亏: ¥{summary.total_unrealized_pnl:,.2f}")
    print(f"总未实现盈亏率: {summary.total_unrealized_pnl_pct:.2f}%")
    print(f"现金: ¥{summary.cash:,.2f}")
    print(f"总资产: ¥{summary.total_asset:,.2f}")
    
    # 风险指标
    risk = analysis.risk
    print(f"\n⚠️ 风险指标:")
    print(f"集中度风险: {risk.concentration_risk:.4f}")
    print(f"行业集中度: {risk.sector_concentration:.4f}")
    print(f"波动率风险: {risk.volatility_risk:.4f}")
    print(f"Beta风险: {risk.beta_risk:.4f}")
    print(f"VaR(95%): {risk.var_95:.4f}")
    print(f"最大回撤: {risk.max_drawdown:.4f}")
    print(f"风险等级: {risk.risk_level.value.upper()}")
    
    # 绩效指标
    print(f"\n📊 绩效指标:")
    for key, value in analysis.performance_metrics.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}")
        else:
            print(f"{key}: {value}")
    
    # 主要持仓
    print(f"\n🏆 主要持仓 (前3名):")
    for i, pos in enumerate(analysis.top_positions[:3], 1):
        print(f"{i}. {pos.symbol}: 市值¥{pos.market_value:,.0f}, 盈亏{pos.unrealized_pnl_pct:.2f}%")
    
    # 调整建议
    print(f"\n💡 调整建议:")
    for i, rec in enumerate(analysis.recommendations, 1):
        print(f"{i}. {rec}")
    
    # 生成可视化图表
    print(f"\n🎨 生成可视化图表...")
    try:
        charts = visualizer.generate_comprehensive_report(analysis)
        print(f"✅ 成功生成 {len(charts)} 个图表:")
        for chart_name in charts.keys():
            print(f"  - {chart_name}")
    except Exception as e:
        print(f"❌ 生成图表失败: {e}")
    
    # 生成报告
    print(f"\n📋 生成分析报告...")
    try:
        # 汇总报告
        summary_report = {
            "report_type": "summary",
            "summary": {
                "total_positions": summary.total_positions,
                "total_market_value": round(summary.total_market_value, 2),
                "total_unrealized_pnl": round(summary.total_unrealized_pnl, 2),
                "total_unrealized_pnl_pct": round(summary.total_unrealized_pnl_pct, 2),
                "total_asset": round(summary.total_asset, 2)
            },
            "risk_level": risk.risk_level.value,
            "top_positions": [
                {
                    "symbol": pos.symbol,
                    "market_value": round(pos.market_value, 2),
                    "unrealized_pnl_pct": round(pos.unrealized_pnl_pct, 2)
                }
                for pos in analysis.top_positions[:3]
            ],
            "recommendations": analysis.recommendations[:3]
        }
        
        print("✅ 汇总报告:")
        print(json.dumps(summary_report, indent=2, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
    
    print(f"\n" + "=" * 60)
    print("🎉 持仓分析演示完成!")
    print("=" * 60)

def demo_api_endpoints():
    """演示API端点"""
    print("\n🌐 API端点演示:")
    print("=" * 40)
    
    endpoints = [
        {
            "method": "GET",
            "url": "/api/position/analysis?account_id=demo&include_recommendations=true",
            "description": "获取持仓分析"
        },
        {
            "method": "POST", 
            "url": "/api/position/analysis",
            "description": "提交持仓数据进行分析",
            "body": {
                "positions": create_sample_positions(),
                "cash": 50000.0
            }
        },
        {
            "method": "GET",
            "url": "/api/position/detail?account_id=demo",
            "description": "获取持仓明细"
        },
        {
            "method": "GET", 
            "url": "/api/position/detail?account_id=demo&symbol=000001.SZ",
            "description": "获取特定股票持仓"
        },
        {
            "method": "GET",
            "url": "/api/position/report?account_id=demo&type=summary",
            "description": "生成汇总报告"
        },
        {
            "method": "GET",
            "url": "/api/position/report?account_id=demo&type=detailed", 
            "description": "生成详细报告"
        },
        {
            "method": "GET",
            "url": "/api/position/report?account_id=demo&type=risk",
            "description": "生成风险报告"
        }
    ]
    
    for i, endpoint in enumerate(endpoints, 1):
        print(f"{i}. {endpoint['method']} {endpoint['url']}")
        print(f"   {endpoint['description']}")
        if 'body' in endpoint:
            print(f"   Body: {json.dumps(endpoint['body'], ensure_ascii=False)}")
        print()

if __name__ == "__main__":
    print("🚀 启动持仓分析演示...")
    
    # 运行演示
    asyncio.run(demo_position_analysis())
    
    # 显示API端点
    demo_api_endpoints()
    
    print("\n📝 使用说明:")
    print("1. 启动Web服务器: python main.py")
    print("2. 访问API端点进行持仓分析")
    print("3. 查看生成的图表和报告")
    print("4. 根据建议调整持仓策略") 