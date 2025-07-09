import pandas as pd

def graham_active_investment_strategy(data):
    """
    本杰明・格雷厄姆积极投资策略
    :param data: DataFrame, 包含股票的财务数据和市场数据
    :return: DataFrame, 包含符合条件的股票和投资建议
    """
    # 筛选条件
    condition1 = data['PE'] > 0
    condition2 = data['PB'] > 0
    condition3 = data['PB'] < 2.5
    condition4 = data['Current Ratio'] >= 1.2
    condition5 = data['Total Debt'] <= 1.5 * data['Net Current Assets']
    condition6 = data['Net Income'] > 0
    condition7 = data['Dividend'] > 0
    condition8 = data['Net Income Growth'] > 0

    # 合并条件
    filtered_data = data[
        (condition1) &
        (condition2) &
        (condition3) &
        (condition4) &
        (condition5) &
        (condition6) &
        (condition7) &
        (condition8)
    ]

    # 按市盈率排序，选取前400只股票
    filtered_data = filtered_data.sort_values(by='PE', ascending=True).head(400)

    # 按市净率排序，选取前400只股票
    filtered_data = filtered_data.sort_values(by='PB', ascending=True).head(400)

    # 按净利润增长率排序，选取前400只股票
    filtered_data = filtered_data.sort_values(by='Net Income Growth', ascending=False).head(400)

    # 最终选取前30只股票
    final_selection = filtered_data.head(30)

    # 添加投资建议
    final_selection['Investment Suggestion'] = 'Buy'

    return final_selection

# 示例数据
data = pd.DataFrame({
    'Stock': ['Stock1', 'Stock2', 'Stock3', 'Stock4', 'Stock5'],
    'PE': [10, 15, 20, 25, 30],
    'PB': [1.2, 1.5, 1.8, 2.0, 2.2],
    'Current Ratio': [1.5, 1.3, 1.2, 1.1, 1.0],
    'Total Debt': [100, 150, 200, 250, 300],
    'Net Current Assets': [200, 250, 300, 350, 400],
    'Net Income': [10, 20, 30, 40, 50],
    'Dividend': [1, 2, 3, 4, 5],
    'Net Income Growth': [5, 10, 15, 20, 25]
})

# 调用函数
result = graham_active_investment_strategy(data)

# 打印结果
print(result)