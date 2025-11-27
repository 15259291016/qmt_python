from xtquant import xttrader, xtdata, xttype
import time
import pandas as pd
from datetime import datetime

def _parse_schema(doc: str) -> dict:
    schema = {}
    if not doc:
        return schema
    for line in doc.splitlines():
        parts = line.strip().split('\t')
        if len(parts) >= 3:
            name, typ, desc = parts[0], parts[1], parts[2]
            if name and typ and desc:
                schema[name] = (typ, desc)
    return schema

# 订阅行情
def on_tick(data):
    """
    字段名	数据类型	解释
time	int	时间戳
bidNumber	int	主买单总单数
offNumber	int	主卖单总单数
ddx	float	大单动向
ddy	float	涨跌动因
ddz	float	大单差分
netOrder	int	净挂单量
netWithdraw	int	净撤单量
withdrawBid	int	总撤买量
withdrawOff	int	总撤卖量
bidNumberDx	int	主买单总单数增量
offNumberDx	int	主卖单总单数增量
transactionNumber	int	成交笔数增量
bidMostAmount	float	主买特大单成交额
bidBigAmount	float	主买大单成交额
bidMediumAmount	float	主买中单成交额
bidSmallAmount	float	主买小单成交额
bidTotalAmount	float	主买累计成交额
offMostAmount	float	主卖特大单成交额
offBigAmount	float	主卖大单成交额
offMediumAmount	float	主卖中单成交额
offSmallAmount	float	主卖小单成交额
offTotalAmount	float	主卖累计成交额
unactiveBidMostAmount	float	被动买特大单成交额
unactiveBidBigAmount	float	被动买大单成交额
unactiveBidMediumAmount	float	被动买中单成交额
unactiveBidSmallAmount	float	被动买小单成交额
unactiveBidTotalAmount	float	被动买累计成交额
unactiveOffMostAmount	float	被动卖特大单成交额
unactiveOffBigAmount	float	被动卖大单成交额
unactiveOffMediumAmount	float	被动卖中单成交额
unactiveOffSmallAmount	float	被动卖小单成交额
unactiveOffTotalAmount	float	被动卖累计成交额
netInflowMostAmount	float	净流入超大单成交额
netInflowBigAmount	float	净流入大单成交额
netInflowMediumAmount	float	净流入中单成交额
netInflowSmallAmount	float	净流入小单成交额
bidMostVolume	int	主买特大单成交量
bidBigVolume	int	主买大单成交量
bidMediumVolume	int	主买中单成交量
bidSmallVolume	int	主买小单成交量
bidTotalVolume	int	主买累计成交量
offMostVolume	int	主卖特大单成交量
offBigVolume	int	主卖大单成交量
offMediumVolume	int	主卖中单成交量
offSmallVolume	int	主卖小单成交量
offTotalVolume	int	主卖累计成交量
unactiveBidMostVolume	int	被动买特大单成交量
unactiveBidBigVolume	int	被动买大单成交量
unactiveBidMediumVolume	int	被动买中单成交量
unactiveBidSmallVolume	int	被动买小单成交量
unactiveBidTotalVolume	int	被动买累计成交量
unactiveOffMostVolume	int	被动卖特大单成交量
unactiveOffBigVolume	int	被动卖大单成交量
unactiveOffMediumVolume	int	被动卖中单成交量
unactiveOffSmallVolume	int	被动卖小单成交量
unactiveOffTotalVolume	int	被动卖累计成交量
netInflowMostVolume	int	净流入超大单成交量
netInflowBigVolume	int	净流入大单成交量
netInflowMediumVolume	int	净流入中单成交量
netInflowSmallVolume	int	净流入小单成交量
bidMostAmountDx	float	主买特大单成交额增量
bidBigAmountDx	float	主买大单成交额增量
bidMediumAmountDx	float	主买中单成交额增量
bidSmallAmountDx	float	主买小单成交额增量
bidTotalAmountDx	float	主买累计成交额增量
offMostAmountDx	float	主卖特大单成交额增量
offBigAmountDx	float	主卖大单成交额增量
offMediumAmountDx	float	主卖中单成交额增量
offSmallAmountDx	float	主卖小单成交额增量
offTotalAmountDx	float	主卖累计成交额增量
unactiveBidMostAmountDx	float	被动买特大单成交额增量
unactiveBidBigAmountDx	float	被动买大单成交额增量
unactiveBidMediumAmountDx	float	被动买中单成交额增量
unactiveBidSmallAmountDx	float	被动买小单成交额增量
unactiveBidTotalAmountDx	float	被动买累计成交额增量
unactiveOffMostAmountDx	float	被动卖特大单成交额增量
unactiveOffBigAmountDx	float	被动卖大单成交额增量
unactiveOffMediumAmountDx	float	被动卖中单成交额增量
unactiveOffSmallAmountDx	float	被动卖小单成交额增量
unactiveOffTotalAmountDx	float	被动卖累计成交额增量
netInflowMostAmountDx	float	净流入超大单成交额增量
netInflowBigAmountDx	float	净流入大单成交额增量
netInflowMediumAmountDx	float	净流入中单成交额增量
netInflowSmallAmountDx	float	净流入小单成交额增量
bidMostVolumeDx	int	主买特大单成交量增量
bidBigVolumeDx	int	主买大单成交量增量
bidMediumVolumeDx	int	主买中单成交量增量
bidSmallVolumeDx	int	主买小单成交量增量
bidTotalVolumeDx	int	主买累计成交量增量
offMostVolumeDx	int	主卖特大单成交量增量
offBigVolumeDx	int	主卖大单成交量增量
offMediumVolumeDx	int	主卖中单成交量增量
offSmallVolumeDx	int	主卖小单成交量增量
offTotalVolumeDx	int	主卖累计成交量增量
unactiveBidMostVolumeDx	int	被动买特大单成交量增量
unactiveBidBigVolumeDx	int	被动买大单成交量增量
unactiveBidMediumVolumeDx	int	被动买中单成交量增量
unactiveBidSmallVolumeDx	int	被动买小单成交量增量
unactiveBidTotalVolumeDx	int	被动买累计成交量增量
unactiveOffMostVolumeDx	int	被动卖特大单成交量增量
unactiveOffBigVolumeDx	int	被动卖大单成交量增量
unactiveOffMediumVolumeDx	int	被动卖中单成交量增量
unactiveOffSmallVolumeDx	int	被动卖小单成交量增量
unactiveOffTotalVolumeDx	int	被动卖累计成交量增量
netInflowMostVolumeDx	int	净流入超大单成交量增量
netInflowBigVolumeDx	int	净流入大单成交量增量
netInflowMediumVolumeDx	int	净流入中单成交量增量
netInflowSmallVolumeDx	int	净流入小单成交量增量
    """
    # 处理字典列表格式的数据
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        print_dict_list_data(data)
    # 处理字典格式的数据（回调数据）
    elif isinstance(data, dict):
        # 检查是否是 {股票代码: 数据} 格式
        if len(data) == 1:
            first_value = list(data.values())[0]
            if isinstance(first_value, list):
                # 处理 {股票代码: [字典列表]} 格式
                stock_code = list(data.keys())[0]
                data_list = first_value
                print(f"\n【股票代码：{stock_code}】")
                print_dict_list_data(data_list)
            elif isinstance(first_value, pd.DataFrame):
                # 处理 {股票代码: DataFrame} 格式
                stock_code = list(data.keys())[0]
                df = first_value
                if not df.empty:
                    data_list = df.to_dict('records')
                    print(f"\n【股票代码：{stock_code}】")
                    print_dict_list_data(data_list)
                else:
                    print(f"\n【股票代码：{stock_code}】数据为空")
            else:
                # 普通字典格式（回调数据）
                print_dict_data(data)
        else:
            # 普通字典格式（回调数据）
            print_dict_data(data)
    else:
        print("未知数据格式：", type(data))
        print(data)


def print_dict_data(data: dict):
    """
    打印字典格式的数据（回调数据）
    
    Args:
        data: 字典格式的数据
    """
    schema = _parse_schema(on_tick.__doc__)
    if not schema:
        print("数据格式解析失败，原始数据：", data)
        return
    
    # 格式化打印所有字段
    print("\n" + "="*60)
    print("行情数据详情")
    print("="*60)
    for key, (typ, desc) in schema.items():
        val = data.get(key, "")
        display_val = format_value(val, typ, key)
        print(f"{desc}：{display_val}")
    print("="*60 + "\n")


def print_dict_list_data(data_list: list):
    """
    打印字典列表格式的数据
    
    Args:
        data_list: 字典列表，每个字典包含一条记录
    """
    schema = _parse_schema(on_tick.__doc__)
    if not schema:
        print("数据格式解析失败")
        return
    
    for idx, data in enumerate(data_list):
        print("\n" + "="*60)
        print(f"第 {idx + 1} 条记录")
        print("="*60)
        
        for key, (typ, desc) in schema.items():
            val = data.get(key, "")
            display_val = format_value(val, typ, key)
            print(f"{desc}：{display_val}")
        
        print("="*60 + "\n")


def analyze_abnormal_value(val: int, key: str) -> str:
    """
    分析异常值可能的原因
    
    Args:
        val: 异常值
        key: 字段名
        
    Returns:
        异常值原因说明
    """
    abs_val = abs(val)
    
    # 优先检查增量字段（Dx），因为增量字段最容易出现异常
    if key.endswith('Dx'):  # 增量字段
        # 检查是否是内存地址格式
        hex_str = hex(abs_val)
        # 64位系统内存地址通常是16位16进制（0x开头+16位）
        if len(hex_str) >= 18:  # 0x + 16位 = 18字符
            return "增量字段数据异常，疑似内存地址或未初始化数据（数据源问题）"
        # 检查是否是浮点数精度问题
        if abs_val > 1e15:
            return "增量字段数据异常，可能是数据源计算错误、累计值误读为增量，或浮点数精度问题"
        return "增量字段数据异常，建议检查数据源"
    
    # 检查是否是内存地址格式（非增量字段）
    hex_str = hex(abs_val)
    if len(hex_str) >= 18:  # 64位内存地址
        return "疑似内存地址或未初始化数据（数据源问题）"
    
    # 检查数值范围是否合理
    # 正常成交量应该在合理范围内
    if 'Volume' in key:
        if abs_val > 1e15:  # 超过千万亿
            return "成交量数值异常，可能是数据类型转换错误或数据源问题"
        elif abs_val > 1e12:  # 超过万亿
            return "成交量数值超出合理范围，建议检查数据源"
    
    if 'Amount' in key:
        if abs_val > 1e15:  # 超过千万亿
            return "成交额数值异常，可能是数据类型转换错误或数据源问题"
        elif abs_val > 1e12:  # 超过万亿
            return "成交额数值超出合理范围，建议检查数据源"
    
    return "数据异常，建议检查数据源或联系技术支持"


def format_value(val, typ: str, key: str = "") -> str:
    """
    根据数据类型格式化显示值
    
    Args:
        val: 原始值
        typ: 数据类型（int, float等）
        key: 字段名（用于特殊处理，如时间戳转换）
        
    Returns:
        格式化后的字符串
    """
    if val == "" or val is None:
        return "无数据"
    
    # 特殊处理：时间戳转换为时间格式
    if key == "time" and isinstance(val, (int, float)) and val > 0:
        try:
            # 判断是秒级还是毫秒级时间戳
            is_millisecond = val > 1e12
            if is_millisecond:  # 毫秒级时间戳（13位数字）
                timestamp = val / 1000
                milliseconds = int(val % 1000)
            else:  # 秒级时间戳（10位数字）
                timestamp = val
                milliseconds = 0
            
            dt = datetime.fromtimestamp(timestamp)
            # 格式化时间：包含日期、时分秒，如果是毫秒级时间戳则显示毫秒
            if is_millisecond and milliseconds > 0:
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                return f"{time_str}.{milliseconds:03d} (时间戳: {int(val):,})"
            else:
                time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                return f"{time_str} (时间戳: {int(val):,})"
        except (ValueError, OSError, OverflowError) as e:
            # 转换失败，返回原始值
            return f"{int(val):,} (转换失败: {str(e)})"
    
    # 检查异常值（可能是内存地址或错误数据）
    if isinstance(val, (int, float)):
        # 对于异常大的整数，可能是错误数据
        if isinstance(val, int) and abs(val) > 1e15:
            # 分析异常值可能的原因
            reason = analyze_abnormal_value(val, key)
            return f"{val:,} (异常值 - {reason})"
        # 对于异常小的浮点数，可能是精度问题
        if isinstance(val, float) and abs(val) < 1e-300 and val != 0:
            return "0.00 (接近0)"
    
    try:
        if typ == 'int':
            if isinstance(val, (int, float)):
                return f"{int(val):,}"
            else:
                return str(val)
        elif typ == 'float':
            if isinstance(val, (int, float)):
                # 处理异常小的浮点数
                if abs(val) < 1e-300 and val != 0:
                    return "0.00"
                return f"{float(val):,.2f}"
            else:
                return str(val)
        else:
            return str(val)
    except (ValueError, TypeError, OverflowError):
        return str(val)
        
stock_list = ["600622.SH"]


# 启动交易
path = r"D:\国金QMT交易端模拟\userdata_mini"
session_id = int(time.time())
xt_trader = xttrader.XtQuantTrader(path, session_id)
xt_trader.start()
xt_trader.connect()
print("交易连接成功")
xtdata.download_history_data(stock_list[0],period="transactioncount1d",start_time = "", end_time = "")
subId = xtdata.subscribe_quote(stock_list[0], period="transactioncount1d", callback=on_tick)
print("订阅行情成功，订阅ID为：", subId)
data1 = xtdata.get_market_data_ex([],stock_list,period="transactioncount1d",start_time = "", end_time = "")
print("\n【get_market_data_ex 返回数据】")
print(data1)
# 取消订阅
# xtdata.unsubscribe_quote(subId)
print("取消订阅成功")
xt_trader.run_forever() 
print("交易连接成功")
