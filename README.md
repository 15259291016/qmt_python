# 项目环境说明

## Python环境

建议使用 Python 3.11.9

```bash
conda create -n py311 python=3.11.9
conda activate py311
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 环境配置

首次使用项目时，需要配置环境变量：

```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑.env文件，配置你的服务信息
# 请根据.env.example中的示例，填入你的实际配置
```

**注意**: `.env` 文件包含敏感信息，不会被提交到Git仓库。请确保在 `.env` 文件中配置正确的服务参数。

## 运行项目

```bash
cd algo
python main.py
```