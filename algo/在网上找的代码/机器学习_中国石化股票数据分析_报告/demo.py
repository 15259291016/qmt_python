import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from sqlalchemy import create_engine
from statsmodels.stats.outliers_influence import variance_inflation_factor
import os
import matplotlib


matplotlib.use('TkAgg')

# 设置显示选项，避免输出被省略
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.width', None)

# 用来正常显示中文标签
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
sns.set_style('whitegrid', {'font.sans-serif': ['simhei', 'Arial']})

# 创建保存图片的目录
output_dir = 'images'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 加载数据
# file_path = '中国石化.xlsx'
# df = pd.read_excel(file_path)


# 加载数据
file_path = '韵达股份.csv'
df = pd.read_csv(file_path)
print("数据基本信息:")
df.info()

print("\n数据预览:")
print(df.head())


# 定义一个函数来转换数据
def convert_to_billion(value):
    """
    将带有“万”或“亿”的数据转换为亿元
    """
    if isinstance(value, str):
        if '万' in value:
            value = float(value.replace('万', '').replace(',', '')) / 10000
        elif '亿' in value:
            value = float(value.replace('亿', '').replace(',', ''))
        else:
            value = float(value.replace(',', ''))
    return value


# 选定要转换的列
columns_to_convert = df.columns[3:]

# 遍历每一列进行转换
# for col in columns_to_convert:
#     df[col] = df[col].apply(convert_to_billion)

# 数据排序，确保按时间顺序排列
df = df.sort_values(by='trade_date')
# 数据统计描述
print("\n数据统计描述:")
print(df.describe().applymap(lambda x: f"{x:.2f}"))
df.rename(
    columns={
        "trade_date": "日期",
        "pct_change": "涨跌幅",
        "close": "收盘价",
        "net_amount": "主力净流入额",
        "net_amount_rate": "主力净流入净占比",
        "buy_elg_amount": "超大单净流入额",
        "buy_elg_amount_rate": "超大单净流入占比",
        "buy_lg_amount": "大单净流入额",
        "buy_lg_amount_rate": "大单净流入占比",
        "buy_md_amount": "中单净流入额",
        "buy_md_amount_rate": "中单净流入占比",
        "buy_sm_amount": "小单净流入额",
        "buy_sm_amount_rate": "小单净流入占比"
    },
    inplace=True
)
df.drop(columns=['ts_code', 'name'], inplace=True)
# 数据可视化分析
plt.figure(figsize=(12, 6))
plt.plot(df['日期'], df['收盘价'], label='收盘价', color='blue')
plt.xlabel('日期')
plt.ylabel('收盘价（元）')
plt.title('收盘价走势')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(output_dir, '收盘价走势.png'))
plt.close()

plt.figure(figsize=(12, 6))
plt.plot(df['日期'], df['主力净流入额'], label='主力净流入额', color='green')
plt.xlabel('日期')
plt.ylabel('主力净流入额')
plt.title('主力净流入额走势')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(output_dir, '主力净流入额走势.png'))
plt.close()

# 数据分布分析
plt.figure(figsize=(12, 6))
sns.histplot(df['收盘价'], kde=True, color='blue')
plt.title('收盘价分布')
plt.xlabel('收盘价')
plt.ylabel('频率')
plt.savefig(os.path.join(output_dir, '收盘价分布.png'))
plt.close()

plt.figure(figsize=(12, 6))
sns.histplot(df['主力净流入额'], kde=True, color='green')
plt.title('主力净流入额分布')
plt.xlabel('主力净流入额')
plt.ylabel('频率')
plt.savefig(os.path.join(output_dir, '主力净流入额分布.png'))
plt.close()

# 相关性分析
plt.figure(figsize=(14, 10))
correlation_matrix = df.corr()
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f')
plt.title('相关性矩阵')
plt.savefig(os.path.join(output_dir, '相关性矩阵.png'))
plt.close()

# 选择相关特征列，假设存在‘收盘价’列
features = ['涨跌幅', '主力净流入额', '主力净流入净占比', '超大单净流入额', '超大单净流入占比',
            '大单净流入额', '大单净流入占比', '中单净流入额', '中单净流入占比', '小单净流入额',
            '小单净流入占比']
target = '收盘价'

# 分离特征和目标
# 分离特征和目标
X = df[features]
y = df[target]

# 添加常数项
X_const = sm.add_constant(X)

# 使用OLS模型
model = sm.OLS(y, X_const).fit()

# 打印模型方程
print("\nOLS模型方程:")
print(f"截距（const）：{model.params[0]:.4f}")
for feature, coef in zip(features, model.params[1:]):
    print(f"{feature}: {coef:.4f}")

# 进行F检验
print("\nF检验结果:")
print(model.f_test(" + ".join(features) + " = 0"))

print("\nOLS模型摘要:")
print(model.summary())

# 残差分析
residuals = model.resid
plt.figure(figsize=(12, 6))
plt.plot(df['日期'], residuals, label='残差', color='purple')
plt.axhline(y=0, color='r', linestyle='--')
plt.xlabel('日期')
plt.ylabel('残差')
plt.title('残差分析')
plt.legend()
plt.grid(True)
plt.savefig(os.path.join(output_dir, '残差分析.png'))
plt.close()

# 残差分布图
plt.figure(figsize=(12, 6))
sns.histplot(residuals, kde=True, color='purple')
plt.title('残差分布')
plt.xlabel('残差')
plt.ylabel('频率')
plt.savefig(os.path.join(output_dir, '残差分布.png'))
plt.close()

# 残差QQ图
plt.figure(figsize=(12, 6))
sm.qqplot(residuals, line='45', fit=True)
plt.title('残差QQ图')
plt.savefig(os.path.join(output_dir, '残差QQ图.png'))
plt.close()

# 特征重要性分析（线性回归系数）
coefficients_df = pd.DataFrame(model.params[1:], features, columns=['系数'])
coefficients_df = coefficients_df.sort_values(by='系数', ascending=False)

plt.figure(figsize=(12, 10))
ax = coefficients_df.plot(kind='bar',
                          color=['blue', 'green', 'orange', 'purple', 'red', 'cyan', 'magenta', 'yellow', 'pink',
                                 'brown'])
plt.title('特征重要性')
plt.xlabel('特征')
plt.ylabel('系数')
plt.grid(True)
plt.xticks(rotation=15)  # x轴标签倾斜15度
plt.savefig(os.path.join(output_dir, '特征重要性.png'))
plt.close()

# 多重共线性检测（VIF）
vif_data = pd.DataFrame()
vif_data["特征"] = X.columns
vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]

print("\n多重共线性检测（VIF）:")
print(vif_data)

# 回归诊断图
fig = plt.figure(figsize=(12, 8))
fig = sm.graphics.plot_regress_exog(model, '主力净流入额', fig=fig)
plt.savefig(os.path.join(output_dir, '回归诊断图_主力净流入额.png'))
plt.close()

fig = plt.figure(figsize=(12, 8))
fig = sm.graphics.plot_regress_exog(model, '涨跌幅', fig=fig)
plt.savefig(os.path.join(output_dir, '回归诊断图_涨跌幅.png'))
plt.close()

print(f"\n所有图表已保存到: {output_dir}")
