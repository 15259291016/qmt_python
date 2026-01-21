"""
市场趋势数据获取诊断脚本
用于快速诊断为什么无法获取指数数据
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import config.ConfigServer as Cs

def test_tushare_token():
    """测试Tushare Token"""
    print("=" * 60)
    print("步骤1: 检查Tushare Token")
    print("=" * 60)
    
    token = Cs.getTushareToken()
    if not token:
        print("❌ Tushare Token未设置")
        print("   请检查 Config.yaml 或 .env 文件中的 toshare_token 配置")
        return False
    
    print(f"✅ Token已设置: {token[:10]}...{token[-5:]}")
    
    # 测试Token是否有效
    try:
        pro = ts.pro_api(token)
        # 尝试获取一个简单的数据来验证Token
        df = pro.trade_cal(exchange='SSE', start_date='20240101', end_date='20240110')
        if df is not None and not df.empty:
            print("✅ Token有效，可以调用Tushare API")
            return True
        else:
            print("⚠️ Token可能无效，API返回空数据")
            return False
    except Exception as e:
        print(f"❌ Token无效或API调用失败: {e}")
        return False

def test_index_data():
    """测试获取指数数据"""
    print("\n" + "=" * 60)
    print("步骤2: 测试获取指数数据")
    print("=" * 60)
    
    token = Cs.getTushareToken()
    if not token:
        print("❌ 跳过测试：Token未设置")
        return
    
    pro = ts.pro_api(token)
    index_codes = [
        ('000001.SH', '上证指数'),
        ('399001.SZ', '深证成指'),
        ('399006.SZ', '创业板指'),
        ('000905.SH', '中证500')
    ]
    
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=400)).strftime('%Y%m%d')
    
    success_count = 0
    for code, name in index_codes:
        try:
            print(f"\n测试 {name} ({code}):")
            # 指数数据使用 index_daily API
            df = pro.index_daily(ts_code=code, start_date=start_date, end_date=end_date)
            
            if df is None:
                print(f"  ❌ 返回None")
                continue
            
            if df.empty:
                print(f"  ❌ 返回空DataFrame")
                continue
            
            # 检查必需列
            required_cols = ['trade_date', 'close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"  ❌ 缺少必需列: {missing_cols}")
                print(f"     可用列: {df.columns.tolist()}")
                continue
            
            # 检查数据长度
            data_length = len(df)
            if data_length < 60:
                print(f"  ⚠️ 数据长度不足: {data_length} < 60")
            elif data_length < 120:
                print(f"  ⚠️ 数据长度不足（多周期涨跌幅需要120天）: {data_length} < 120")
            else:
                print(f"  ✅ 数据长度: {data_length} 条")
            
            print(f"  ✅ 日期范围: {df['trade_date'].min()} 至 {df['trade_date'].max()}")
            print(f"  ✅ 列名: {df.columns.tolist()}")
            
            # 检查是否有volume列
            if 'volume' in df.columns:
                print(f"  ✅ 有volume列")
            elif 'vol' in df.columns:
                print(f"  ⚠️ 有vol列（无volume列），代码会自动处理")
            else:
                print(f"  ⚠️ 无volume/vol列，成交量指标无法计算")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ❌ 获取失败: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n总结: {success_count}/{len(index_codes)} 个指数数据获取成功")
    if success_count == 0:
        print("\n❌ 所有指数数据获取失败，可能的原因：")
        print("   1. Tushare Token无效或过期")
        print("   2. 积分不足（指数数据可能需要积分）")
        print("   3. 网络连接问题")
        print("   4. API调用频率限制")
    elif success_count < len(index_codes):
        print(f"\n⚠️ 部分指数数据获取失败，市场趋势判断可能不准确")

def test_get_history_func():
    """测试get_history_func函数"""
    print("\n" + "=" * 60)
    print("步骤3: 测试get_history_func函数")
    print("=" * 60)
    
    from main import get_history_func
    import config.ConfigServer as Cs
    
    token = Cs.getTushareToken()
    if not token:
        print("❌ 跳过测试：Token未设置")
        return
    
    test_codes = ['000001.SH', '399001.SZ']
    for code in test_codes:
        print(f"\n测试 {code}:")
        try:
            df = get_history_func(code, token)
            if df is None:
                print(f"  ❌ 返回None")
            elif df.empty:
                print(f"  ❌ 返回空DataFrame")
            else:
                print(f"  ✅ 成功: {len(df)} 条数据")
                print(f"     列名: {df.columns.tolist()}")
                if 'close' in df.columns:
                    print(f"     最新收盘价: {df['close'].iloc[-1]}")
        except Exception as e:
            print(f"  ❌ 调用失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("市场趋势数据获取诊断工具")
    print("=" * 60)
    
    # 步骤1: 测试Token
    if not test_tushare_token():
        print("\n❌ Token测试失败，请先解决Token问题")
        sys.exit(1)
    
    # 步骤2: 测试指数数据
    test_index_data()
    
    # 步骤3: 测试get_history_func
    test_get_history_func()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)
    print("\n如果所有测试都失败，请检查：")
    print("1. Tushare Token是否有效")
    print("2. 是否有足够的积分获取指数数据")
    print("3. 网络连接是否正常")
    print("4. 查看详细错误信息")

