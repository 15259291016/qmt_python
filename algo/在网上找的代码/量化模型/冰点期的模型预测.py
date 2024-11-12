import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from xgboost import XGBClassifier
from sklearn.metrics import mean_squared_error, accuracy_score
import matplotlib.pyplot as plt
import shap

# 设置字体为微软雅黑
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('市场情绪统计表.csv')

# 将日期列转换为 datetime 类型
df['日期'] = pd.to_datetime(df['日期'])

# 设置日期列为索引
df.set_index('日期', inplace=True)

# 添加是否为冰点期的标签
df['冰点期'] = (df['市场阶段'] == '冰点期').astype(int)

# 创建滞后特征
df['冰点期_lag_1'] = df['冰点期'].shift(1)
df['冰点期_lag_2'] = df['冰点期'].shift(2)
# 此处省略预测特征处理代码。
features=[]
target = '冰点期'
 # 创建特征矩阵和目标向量
X = df[features].dropna()
y = df[target].loc[X.index]

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 使用 XGBoost 模型
model = XGBClassifier(random_state=42)

# 定义超参数搜索空间
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [3, 5, 7],
    'learning_rate': [0.01, 0.1, 0.2],
    'subsample': [0.8, 1.0],
    'colsample_bytree': [0.8, 1.0]
}

# 使用网格搜索进行超参数调优
grid_search = GridSearchCV(estimator=model, param_grid=param_grid, cv=5, scoring='accuracy', n_jobs=-1)
grid_search.fit(X_train, y_train)

# 最佳模型
best_model = grid_search.best_estimator_

# 预测
y_pred = best_model.predict(X_test)

# 计算准确率
accuracy = accuracy_score(y_test, y_pred)
print(f'Accuracy: {accuracy}')

# 分析特征重要性
importances = best_model.feature_importances_
feature_importances = pd.DataFrame({'Feature': X.columns, 'Importance': importances})
print(feature_importances.sort_values(by='Importance', ascending=False))

# 使用 SHAP 解释模型
explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_test)

# 检查 shap_values 的类型和形状
print(f'SHAP values type: {type(shap_values)}')
print(f'SHAP values shape: {shap_values.shape}')

# 如果是多类别问题，选择类别 1 的 SHAP 值数组
if isinstance(shap_values, list):
    shap_values = shap_values[1]  # 选择类别 1 的 SHAP 值数组
elif shap_values.ndim == 3 and shap_values.shape[2] == 2:
    shap_values = shap_values[:, :, 1]  # 二分类问题，选择类别 1 的 SHAP 值数组

# 绘制 SHAP 值的摘要图
shap.summary_plot(shap_values, X_test, feature_names=features)

# 预测未来的冰点期状态
future_dates = pd.date_range(start='2024-11-02', end='2024-11-10')
future_data = pd.DataFrame({'日期': future_dates})
future_data = future_data.merge(df, on='日期', how='left')

# 只保留数值类型的特征
future_data = future_data[features]

# 使用历史数据的均值填充缺失值
future_data = future_data.fillna(df[features].mean())

future_predictions = best_model.predict(future_data)
future_data['预测冰点期'] = future_predictions
print(future_data[['预测冰点期']])
