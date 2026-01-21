#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试脚本 - 快速验证买卖点功能是否正常工作
"""

import os
import sys
from dotenv import load_dotenv

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from main import BuySellPointCrawler


def quick_test():
    """快速测试"""
    print("=" * 60)
    print("买卖点功能快速测试")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    tushare_token = os.getenv('TUSHARE_TOKEN')
    
    if not tushare_token:
        print("\n⚠️  警告: 未找到TUSHARE_TOKEN，将尝试使用AKShare数据源")
    else:
        print(f"\n✓ Tushare Token已加载")
    
    # 创建爬虫实例
    print("\n正在初始化爬虫...")
    crawler = BuySellPointCrawler(method='calculate', tushare_token=tushare_token)
    print("✓ 爬虫初始化成功")
    
    # 测试股票
    test_stock = '603444'  # 吉比特
    print(f"\n正在测试股票: {test_stock}")
    print("-" * 60)
    
    try:
        # 获取买卖点
        result = crawler.get_buy_sell_points(test_stock, days=250)
        
        if 'error' in result:
            print(f"❌ 错误: {result['error']}")
            return False
        
        # 显示结果
        print(f"\n✓ 计算成功！")
        print(f"\n结果摘要:")
        print(f"  股票代码: {result['stock_code']}")
        print(f"  买入点数量: {result['total_buy_points']}")
        print(f"  卖出点数量: {result['total_sell_points']}")
        
        if result.get('avg_buy_score', 0) > 0:
            print(f"  平均买入评分: {result['avg_buy_score']:.2f}")
        if result.get('avg_sell_score', 0) > 0:
            print(f"  平均卖出评分: {result['avg_sell_score']:.2f}")
        
        # 显示最近的买卖点
        if result.get('buy_points'):
            print(f"\n最近3个买入点:")
            for point in result['buy_points'][-3:]:
                print(f"  {point['date']}: 价格={point['price']:.2f}, "
                      f"评分={point.get('score', 0):.2f}, "
                      f"强度={point.get('strength', 'N/A')}")
        
        if result.get('sell_points'):
            print(f"\n最近3个卖出点:")
            for point in result['sell_points'][-3:]:
                print(f"  {point['date']}: 价格={point['price']:.2f}, "
                      f"评分={point.get('score', 0):.2f}, "
                      f"强度={point.get('strength', 'N/A')}")
        
        # 保存结果
        filename = f"测试结果_{test_stock}.csv"
        crawler.save_to_csv(result, filename)
        print(f"\n✓ 结果已保存到: {filename}")
        
        print(f"\n{'='*60}")
        print("✓ 测试通过！买卖点功能正常工作")
        print(f"{'='*60}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = quick_test()
    sys.exit(0 if success else 1)
