#!/usr/bin/env python3
"""
环境切换演示脚本
展示如何在模拟和实盘环境之间切换
"""

import sys
import os
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.environment_manager import get_env_manager, switch_to_simulation, switch_to_production
from user_strategy.simple_select_stock import run_simple_strategy

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_environment_switch():
    """演示环境切换功能"""
    print("🚀 环境切换演示")
    print("=" * 60)
    print(f"演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    env_manager = get_env_manager()
    
    # 1. 显示当前环境
    print("📋 当前环境信息:")
    env_manager.print_environment_info()
    
    # 2. 列出所有可用环境
    environments = env_manager.list_available_environments()
    print(f"\n📋 可用环境列表:")
    for env_name, env_config in environments.items():
        print(f"  - {env_name}: {env_config.get('NAME', env_name)}")
        print(f"    QMT路径: {env_config.get('QMT_PATH', 'N/A')}")
        print(f"    账户: {env_config.get('ACCOUNT', 'N/A')}")
    
    # 3. 测试环境切换
    print(f"\n🔄 测试环境切换:")
    
    # 切换到模拟环境
    print("\n1. 切换到模拟环境:")
    if switch_to_simulation():
        env_manager.print_environment_info()
        
        # 在模拟环境中运行选股策略
        print("\n   🎯 在模拟环境中运行选股策略:")
        try:
            stocks = run_simple_strategy('SIMULATION')
            if stocks:
                print(f"   ✅ 模拟环境选股成功，推荐 {len(stocks)} 只股票")
                for i, stock in enumerate(stocks[:5], 1):  # 只显示前5只
                    print(f"      {i}. {stock}")
            else:
                print("   ❌ 模拟环境选股失败")
        except Exception as e:
            print(f"   ❌ 模拟环境选股异常: {e}")
    else:
        print("   ❌ 切换到模拟环境失败")
    
    # 切换到实盘环境
    print("\n2. 切换到实盘环境:")
    if switch_to_production():
        env_manager.print_environment_info()
        
        # 在实盘环境中运行选股策略
        print("\n   🎯 在实盘环境中运行选股策略:")
        try:
            stocks = run_simple_strategy('PRODUCTION')
            if stocks:
                print(f"   ✅ 实盘环境选股成功，推荐 {len(stocks)} 只股票")
                for i, stock in enumerate(stocks[:5], 1):  # 只显示前5只
                    print(f"      {i}. {stock}")
            else:
                print("   ❌ 实盘环境选股失败")
        except Exception as e:
            print(f"   ❌ 实盘环境选股异常: {e}")
    else:
        print("   ❌ 切换到实盘环境失败")
    
    # 4. 环境配置验证
    print(f"\n🔍 环境配置验证:")
    for env_name in ['SIMULATION', 'PRODUCTION']:
        if env_manager.switch_environment(env_name):
            is_valid = env_manager.validate_current_environment()
            status = "✅ 有效" if is_valid else "❌ 无效"
            print(f"  {env_name}: {status}")
    
    # 5. 切换回模拟环境（默认）
    print(f"\n🔄 切换回默认环境 (模拟):")
    switch_to_simulation()
    env_manager.print_environment_info()

def demo_main_integration():
    """演示与main.py的集成"""
    print(f"\n" + "=" * 60)
    print("🔗 与main.py集成演示")
    print("=" * 60)
    
    print("\n📋 运行方式:")
    print("1. 模拟环境:")
    print("   python main.py --env SIMULATION")
    print("   # 或")
    print("   python main.py  # 默认使用模拟环境")
    
    print("\n2. 实盘环境:")
    print("   python main.py --env PRODUCTION")
    
    print("\n📋 选股策略运行方式:")
    print("1. 模拟环境:")
    print("   python user_strategy/simple_select_stock.py --env SIMULATION")
    
    print("\n2. 实盘环境:")
    print("   python user_strategy/simple_select_stock.py --env PRODUCTION")

def demo_configuration():
    """演示配置信息"""
    print(f"\n" + "=" * 60)
    print("⚙️  配置信息演示")
    print("=" * 60)
    
    env_manager = get_env_manager()
    
    print("\n📋 当前配置:")
    config = env_manager.get_environment_info()
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    print("\n📋 数据库配置:")
    db_config = env_manager.get_database_config()
    for key, value in db_config.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(str(value))}")  # 隐藏密码
        else:
            print(f"  {key}: {value}")
    
    print(f"\n📋 Tushare Token: {env_manager.get_tushare_token()[:10]}...")

if __name__ == "__main__":
    try:
        # 1. 环境切换演示
        demo_environment_switch()
        
        # 2. 配置信息演示
        demo_configuration()
        
        # 3. 集成演示
        demo_main_integration()
        
        print(f"\n" + "=" * 60)
        print("🎉 环境切换演示完成!")
        print("💡 现在您可以在模拟和实盘环境之间自由切换了")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        sys.exit(1) 