"""
量化交易系统配置文件
"""
import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent

# 数据库配置
DATABASE_PATH = PROJECT_ROOT / "data" / "quant.db"
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = PROJECT_ROOT / "logs"

# 数据源配置
DATA_SOURCES = {
    "primary": "akshare",  # 主要数据源
    "fallback": ["akshare", "tushare"],  # 备用数据源
    "cache_days": 30,  # 缓存天数
}

# 技术指标参数
TECHNICAL_INDICATORS = {
    "MA_PERIODS": [5, 10, 20, 30, 60, 120, 250],  # 均线周期
    "MACD": {"fast": 12, "slow": 26, "signal": 9},
    "KDJ": {"k_period": 9, "d_period": 3, "j_period": 3},
    "CCI": {"period": 14},
    "BOLL": {"period": 20, "std": 2},
    "RSI": {"period": 14},
}

# 风控参数
RISK_MANAGEMENT = {
    "max_position_size": 0.1,  # 单个股票最大仓位
    "max_total_exposure": 0.95,  # 总仓位上限
    "target_volatility": 0.15,  # 目标波动率
    "daily_drawdown_limit": 0.05,  # 日内回撤限制
    "stop_loss": 0.08,  # 止损比例
    "take_profit": 0.20,  # 止盈比例
}

# 回测参数
BACKTEST_CONFIG = {
    "initial_capital": 1000000,  # 初始资金
    "commission_rate": 0.0003,  # 手续费率
    "slippage_rate": 0.001,  # 滑点率
    "start_date": "2020-01-01",
    "end_date": "2024-01-01",
}

# 策略配置
STRATEGY_CONFIG = {
    "momentum_strategy": {
        "enabled": True,
        "lookback_period": 20,
        "threshold": 0.02,
    },
    "mean_reversion_strategy": {
        "enabled": True,
        "lookback_period": 10,
        "threshold": 2.0,
    },
    "breakout_strategy": {
        "enabled": True,
        "lookback_period": 20,
        "threshold": 0.05,
    }
}

# AI模型配置
AI_CONFIG = {
    "enabled": True,
    "primary_model": "gpt4",
    "fallback_models": ["deepseek", "gemini"],
    "api_keys": {
        "openai": "your-openai-api-key",
        "deepseek": "your-deepseek-api-key", 
        "gemini": "your-gemini-api-key",
        "qwen": "your-qwen-api-key",
        "grok": "your-grok-api-key"
    },
    "model_settings": {
        "temperature": 0.7,
        "max_tokens": 2000,
        "timeout": 30,
        "retry_count": 3
    },
    "features": {
        "market_sentiment_analysis": True,
        "trading_signal_generation": True,
        "strategy_optimization": True,
        "risk_warning": True,
        "news_analysis": True,
        "technical_analysis_enhancement": True
    }
}

# 创建必要的目录
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
