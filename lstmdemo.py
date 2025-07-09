import torch

from schemas.lstm_schema import LSTMConfig
from src.models.lstm_model import LSTMModel

# 定义模型配置
config = LSTMConfig(input_size=1, hidden_size=16, num_layers=1, output_size=1)
model = LSTMModel(config)

# 构造一个简单的输入序列
x = torch.randn(10, 5, 1)  # batch=10, seq_len=5, input_size=1
y = model(x)
print("预测输出：", y)