import torch
import torch.nn as nn

from schemas.lstm_schema import LSTMConfig


class LSTMModel(nn.Module):
    def __init__(self, config: LSTMConfig):
        super().__init__()
        self.lstm = nn.LSTM(
            input_size=config.input_size,
            hidden_size=config.hidden_size,
            num_layers=config.num_layers,
            batch_first=True
        )
        self.fc = nn.Linear(config.hidden_size, config.output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])
        return out