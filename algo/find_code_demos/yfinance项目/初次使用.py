import yfinance as yf
# https://cloud.tencent.com/developer/article/2318758
# 指定股票代码
name = 'AAPL'

# 下载历史价格数据
apple = yf.download(name, start='2022-01-01', end='2022-12-31')

import pandas as pd
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style('whitegrid')
plt.style.use("fivethirtyeight")
# %matplotlib inline

from datetime import datetime

# pip install pandas_datareader
from pandas_datareader.data import DataReader
import yfinance as yf
from pandas_datareader import data as pdr

yf.pdr_override()

import warnings
warnings.filterwarnings("ignore")

# 获取4个公司股价信息

tech_list = ['AAPL', 'GOOG', 'MSFT', 'AMZN']