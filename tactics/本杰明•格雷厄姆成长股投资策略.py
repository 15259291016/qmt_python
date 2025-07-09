def graham_growth_stock_investment(eps, growth_rate, bond_yield, current_price):
    """
    格雷厄姆成长股投资策略计算器
    :param eps: float, 过去一年的每股收益
    :param growth_rate: float, 长期（5年）预估收益增长率（百分比形式，例如 10% 输入为 10）
    :param bond_yield: float, 当前AAA级公司债券的年收益率（百分比形式，例如 3% 输入为 3）
    :param current_price: float, 公司当前的市场价格
    :return: dict, 包含计算结果和投资建议
    """
    result = {}
    
    # 格雷厄姆修订版公式
    base_value = (8.5 + 2 * (growth_rate / 100)) * eps
    revised_value = (base_value * 4.4) / (bond_yield / 100)
    
    # 安全边际
    margin_of_safety_50 = revised_value * 0.5  # 50% 安全边际
    margin_of_safety_25 = revised_value * 0.25  # 25% 安全边际
    
    # 投资建议
    if current_price <= margin_of_safety_50:
        recommendation = "当前市场价格低于50%安全边际，具有较高的投资价值！"
    elif current_price <= margin_of_safety_25:
        recommendation = "当前市场价格低于25%安全边际，具有一定的投资价值。"
    else:
        recommendation = "当前市场价格高于安全边际，不建议投资。"
    
    # 结果整理
    result["公司"] = "（例：苹果公司）"
    result["每股收益 (EPS)"] = eps
    result["长期预估成长率 (g)"] = f"{growth_rate}%"
    result["AAA债券利率 (Y)"] = f"{bond_yield}%"
    result["当前价格 (Current Price)"] = current_price
    result["格雷厄姆内在价值 (Value)"] = f"{revised_value:.2f}"
    result["格雷厄姆安全边际 50%"] = f"{margin_of_safety_50:.2f}"
    result["格雷厄姆安全边际 25%"] = f"{margin_of_safety_25:.2f}"
    result["投资建议"] = recommendation
    
    return result

# 示例使用
if __name__ == "__main__":
    # 输入公司财务数据
    eps = 2.0  # 每股收益
    growth_rate = 10  # 长期预估收益增长率 (10%)
    bond_yield = 3  # 当前AAA级公司债券的年收益率 (3%)
    current_price = 80  # 公司当前的市场价格
    
    # 调用函数并获取结果
    result = graham_growth_stock_investment(eps, growth_rate, bond_yield, current_price)
    
    # 打印结果
    for key, value in result.items():
        print(f"{key}: {value}")