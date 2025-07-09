from typing import List

from pydantic import BaseModel


class LSTMConfig(BaseModel):
    input_size: int
    hidden_size: int
    num_layers: int
    output_size: int

class LSTMInput(BaseModel):
    sequence: List[float]