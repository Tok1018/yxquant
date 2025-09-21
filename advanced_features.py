"""
高级功能模块
提供机器学习模型集成、期权策略、加密货币支持等高级功能
"""
import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import pickle
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# 机器学习相关导入
try:
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.neural_network import MLPClassifier
    from sklearn.preprocessing import StandardScaler, MinMaxScaler
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.pipeline import Pipeline
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelType(Enum):
    """模型类型枚举"""
    RANDOM_FOREST = "random_forest"
    GRADIENT_BOOSTING = "gradient_boosting"
    LOGISTIC_REGRESSION = "logistic_regression"
    SVM = "svm"
    NEURAL_NETWORK = "neural_network"
    LSTM = "lstm"
    TRANSFORMER = "transformer"

class AssetType(Enum):
    """资产类型枚举"""
    STOCK = "stock"
    OPTION = "option"
    CRYPTO = "crypto"
    FOREX = "forex"
    COMMODITY = "commodity"

@dataclass
class ModelConfig:
    """模型配置"""
    model_type: ModelType
    features: List[str]
    target: str
    lookback_period: int = 20
    prediction_horizon: int = 1
    test_size: float = 0.2
    random_state: int = 42
    parameters: Dict[str, Any] = None

@dataclass
class ModelPerformance:
    """模型性能指标"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    cross_val_score: float
    training_time: float
    prediction_time: float

@dataclass
class OptionContract:
    """期权合约"""
    symbol: str
    strike_price: float
    expiration_date: datetime
    option_type: str  # 'call' or 'put'
    underlying_price: float
    bid_price: float
    ask_price: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

@dataclass
class CryptoAsset:
    """加密货币资产"""
    symbol: str
    name: str
    price: float
    market_cap: float
    volume_24h: float
    change_24h: float
    change_percent_24h: float
    circulating_supply: float
    total_supply: float
    max_supply: Optional[float]
    last_updated: datetime

class MachineLearningEngine:
    """机器学习引擎"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.feature_importance = {}
        self.model_performance = {}
        
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn未安装，机器学习功能不可用")
    
    def create_model(self, config: ModelConfig) -> str:
        """创建模型"""
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn未安装")
        
        model_id = f"{config.model_type.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 根据模型类型创建模型
        if config.model_type == ModelType.RANDOM_FOREST:
            model = RandomForestClassifier(
                n_estimators=config.parameters.get('n_estimators', 100),
                max_depth=config.parameters.get('max_depth', 10),
                random_state=config.random_state
            )
        elif config.model_type == ModelType.GRADIENT_BOOSTING:
            model = GradientBoostingClassifier(
                n_estimators=config.parameters.get('n_estimators', 100),
                learning_rate=config.parameters.get('learning_rate', 0.1),
                max_depth=config.parameters.get('max_depth', 3),
                random_state=config.random_state
            )
        elif config.model_type == ModelType.LOGISTIC_REGRESSION:
            model = LogisticRegression(
                random_state=config.random_state,
                max_iter=config.parameters.get('max_iter', 1000)
            )
        elif config.model_type == ModelType.SVM:
            model = SVC(
                kernel=config.parameters.get('kernel', 'rbf'),
                C=config.parameters.get('C', 1.0),
                random_state=config.random_state
            )
        elif config.model_type == ModelType.NEURAL_NETWORK:
            model = MLPClassifier(
                hidden_layer_sizes=config.parameters.get('hidden_layer_sizes', (100, 50)),
                activation=config.parameters.get('activation', 'relu'),
                max_iter=config.parameters.get('max_iter', 1000),
                random_state=config.random_state
            )
        else:
            raise ValueError(f"不支持的模型类型: {config.model_type}")
        
        self.models[model_id] = {
            'model': model,
            'config': config,
            'scaler': StandardScaler(),
            'trained': False
        }
        
        logger.info(f"创建模型: {model_id}")
        return model_id
    
    def prepare_features(self, data: pd.DataFrame, config: ModelConfig) -> Tuple[np.ndarray, np.ndarray]:
        """准备特征数据"""
        # 选择特征列
        feature_columns = [col for col in config.features if col in data.columns]
        if not feature_columns:
            raise ValueError("没有找到有效的特征列")
        
        # 创建特征矩阵
        X = data[feature_columns].values
        
        # 创建目标变量（未来收益率）
        if config.target in data.columns:
            y = data[config.target].values
        else:
            # 计算未来收益率
            future_returns = data['close'].pct_change(config.prediction_horizon).shift(-config.prediction_horizon)
            y = (future_returns > 0).astype(int)  # 二分类：上涨为1，下跌为0
        
        # 移除NaN值
        valid_indices = ~(np.isnan(X).any(axis=1) | np.isnan(y))
        X = X[valid_indices]
        y = y[valid_indices]
        
        return X, y
    
    def train_model(self, model_id: str, data: pd.DataFrame) -> ModelPerformance:
        """训练模型"""
        if model_id not in self.models:
            raise ValueError(f"模型不存在: {model_id}")
        
        model_info = self.models[model_id]
        config = model_info['config']
        
        # 准备数据
        X, y = self.prepare_features(data, config)
        
        if len(X) == 0:
            raise ValueError("没有有效的训练数据")
        
        # 分割训练和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=config.test_size, random_state=config.random_state
        )
        
        # 特征缩放
        scaler = model_info['scaler']
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # 训练模型
        start_time = datetime.now()
        model_info['model'].fit(X_train_scaled, y_train)
        training_time = (datetime.now() - start_time).total_seconds()
        
        # 预测
        start_time = datetime.now()
        y_pred = model_info['model'].predict(X_test_scaled)
        prediction_time = (datetime.now() - start_time).total_seconds()
        
        # 计算性能指标
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted')
        recall = recall_score(y_test, y_pred, average='weighted')
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        # 交叉验证
        cv_scores = cross_val_score(model_info['model'], X_train_scaled, y_train, cv=5)
        cv_score = cv_scores.mean()
        
        performance = ModelPerformance(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1,
            cross_val_score=cv_score,
            training_time=training_time,
            prediction_time=prediction_time
        )
        
        # 保存性能指标
        self.model_performance[model_id] = performance
        
        # 获取特征重要性
        if hasattr(model_info['model'], 'feature_importances_'):
            self.feature_importance[model_id] = dict(zip(
                config.features, model_info['model'].feature_importances_
            ))
        
        model_info['trained'] = True
        
        logger.info(f"模型训练完成: {model_id}, 准确率: {accuracy:.4f}")
        return performance
    
    def predict(self, model_id: str, data: pd.DataFrame) -> np.ndarray:
        """使用模型预测"""
        if model_id not in self.models:
            raise ValueError(f"模型不存在: {model_id}")
        
        model_info = self.models[model_id]
        if not model_info['trained']:
            raise ValueError(f"模型未训练: {model_id}")
        
        config = model_info['config']
        X, _ = self.prepare_features(data, config)
        
        if len(X) == 0:
            raise ValueError("没有有效的预测数据")
        
        # 特征缩放
        X_scaled = model_info['scaler'].transform(X)
        
        # 预测
        predictions = model_info['model'].predict(X_scaled)
        probabilities = model_info['model'].predict_proba(X_scaled)
        
        return predictions, probabilities
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_id not in self.models:
            raise ValueError(f"模型不存在: {model_id}")
        
        model_info = self.models[model_id]
        performance = self.model_performance.get(model_id)
        feature_importance = self.feature_importance.get(model_id, {})
        
        return {
            'model_id': model_id,
            'model_type': model_info['config'].model_type.value,
            'trained': model_info['trained'],
            'performance': asdict(performance) if performance else None,
            'feature_importance': feature_importance,
            'config': asdict(model_info['config'])
        }

class OptionPricingEngine:
    """期权定价引擎"""
    
    def __init__(self):
        self.risk_free_rate = 0.02  # 无风险利率
    
    def black_scholes_price(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> float:
        """Black-Scholes期权定价"""
        from scipy.stats import norm
        import math
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        if option_type.lower() == 'call':
            price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
        else:  # put
            price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        
        return price
    
    def calculate_greeks(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Dict[str, float]:
        """计算希腊字母"""
        from scipy.stats import norm
        import math
        
        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)
        
        # Delta
        if option_type.lower() == 'call':
            delta = norm.cdf(d1)
        else:  # put
            delta = norm.cdf(d1) - 1
        
        # Gamma
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
        
        # Theta
        if option_type.lower() == 'call':
            theta = -S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) - r * K * math.exp(-r * T) * norm.cdf(d2)
        else:  # put
            theta = -S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) + r * K * math.exp(-r * T) * norm.cdf(-d2)
        
        # Vega
        vega = S * norm.pdf(d1) * math.sqrt(T)
        
        # Rho
        if option_type.lower() == 'call':
            rho = K * T * math.exp(-r * T) * norm.cdf(d2)
        else:  # put
            rho = -K * T * math.exp(-r * T) * norm.cdf(-d2)
        
        return {
            'delta': delta,
            'gamma': gamma,
            'theta': theta,
            'vega': vega,
            'rho': rho
        }
    
    def implied_volatility(self, market_price: float, S: float, K: float, T: float, r: float, option_type: str) -> float:
        """计算隐含波动率"""
        from scipy.optimize import brentq
        
        def objective(sigma):
            theoretical_price = self.black_scholes_price(S, K, T, r, sigma, option_type)
            return theoretical_price - market_price
        
        try:
            iv = brentq(objective, 0.01, 5.0)
            return iv
        except ValueError:
            return 0.0
    
    def create_option_contract(self, symbol: str, strike: float, expiration: datetime, 
                              option_type: str, underlying_price: float, 
                              bid_price: float = 0, ask_price: float = 0) -> OptionContract:
        """创建期权合约"""
        T = (expiration - datetime.now()).days / 365.0
        
        # 使用中间价计算隐含波动率
        mid_price = (bid_price + ask_price) / 2 if bid_price > 0 and ask_price > 0 else 0
        iv = self.implied_volatility(mid_price, underlying_price, strike, T, self.risk_free_rate, option_type)
        
        # 计算希腊字母
        greeks = self.calculate_greeks(underlying_price, strike, T, self.risk_free_rate, iv, option_type)
        
        return OptionContract(
            symbol=symbol,
            strike_price=strike,
            expiration_date=expiration,
            option_type=option_type,
            underlying_price=underlying_price,
            bid_price=bid_price,
            ask_price=ask_price,
            volume=0,
            open_interest=0,
            implied_volatility=iv,
            delta=greeks['delta'],
            gamma=greeks['gamma'],
            theta=greeks['theta'],
            vega=greeks['vega'],
            rho=greeks['rho']
        )

class CryptoDataProvider:
    """加密货币数据提供者"""
    
    def __init__(self):
        self.base_url = "https://api.coingecko.com/api/v3"
        self.cache = {}
        self.cache_duration = 300  # 5分钟缓存
    
    async def get_crypto_data(self, symbols: List[str]) -> List[CryptoAsset]:
        """获取加密货币数据"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                # 构建API请求
                symbols_str = ','.join(symbols)
                url = f"{self.base_url}/simple/price"
                params = {
                    'ids': symbols_str,
                    'vs_currencies': 'usd',
                    'include_market_cap': 'true',
                    'include_24hr_vol': 'true',
                    'include_24hr_change': 'true'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_crypto_data(data)
                    else:
                        logger.error(f"获取加密货币数据失败: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"获取加密货币数据失败: {e}")
            return []
    
    def _parse_crypto_data(self, data: Dict) -> List[CryptoAsset]:
        """解析加密货币数据"""
        crypto_assets = []
        
        for symbol, info in data.items():
            try:
                asset = CryptoAsset(
                    symbol=symbol.upper(),
                    name=symbol,
                    price=info.get('usd', 0),
                    market_cap=info.get('usd_market_cap', 0),
                    volume_24h=info.get('usd_24h_vol', 0),
                    change_24h=info.get('usd_24h_change', 0),
                    change_percent_24h=info.get('usd_24h_change', 0),
                    circulating_supply=0,  # 需要额外API调用
                    total_supply=0,
                    max_supply=None,
                    last_updated=datetime.now()
                )
                crypto_assets.append(asset)
            except Exception as e:
                logger.error(f"解析 {symbol} 数据失败: {e}")
                continue
        
        return crypto_assets
    
    async def get_crypto_historical_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """获取加密货币历史数据"""
        try:
            import aiohttp
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/coins/{symbol}/market_chart"
                params = {
                    'vs_currency': 'usd',
                    'days': days,
                    'interval': 'daily'
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_historical_data(data)
                    else:
                        logger.error(f"获取 {symbol} 历史数据失败: {response.status}")
                        return pd.DataFrame()
        except Exception as e:
            logger.error(f"获取 {symbol} 历史数据失败: {e}")
            return pd.DataFrame()
    
    def _parse_historical_data(self, data: Dict) -> pd.DataFrame:
        """解析历史数据"""
        try:
            prices = data.get('prices', [])
            volumes = data.get('total_volumes', [])
            
            df_data = []
            for i, price_data in enumerate(prices):
                timestamp = datetime.fromtimestamp(price_data[0] / 1000)
                price = price_data[1]
                volume = volumes[i][1] if i < len(volumes) else 0
                
                df_data.append({
                    'timestamp': timestamp,
                    'close': price,
                    'volume': volume
                })
            
            df = pd.DataFrame(df_data)
            df.set_index('timestamp', inplace=True)
            return df
        except Exception as e:
            logger.error(f"解析历史数据失败: {e}")
            return pd.DataFrame()

class AdvancedStrategyEngine:
    """高级策略引擎"""
    
    def __init__(self):
        self.ml_engine = MachineLearningEngine()
        self.option_engine = OptionPricingEngine()
        self.crypto_provider = CryptoDataProvider()
        self.strategies = {}
    
    def create_ml_strategy(self, name: str, config: ModelConfig) -> str:
        """创建机器学习策略"""
        model_id = self.ml_engine.create_model(config)
        self.strategies[name] = {
            'type': 'ml',
            'model_id': model_id,
            'config': config
        }
        logger.info(f"创建机器学习策略: {name}")
        return model_id
    
    def create_option_strategy(self, name: str, strategy_config: Dict) -> str:
        """创建期权策略"""
        strategy_id = f"option_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.strategies[name] = {
            'type': 'option',
            'strategy_id': strategy_id,
            'config': strategy_config
        }
        logger.info(f"创建期权策略: {name}")
        return strategy_id
    
    def create_crypto_strategy(self, name: str, strategy_config: Dict) -> str:
        """创建加密货币策略"""
        strategy_id = f"crypto_{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.strategies[name] = {
            'type': 'crypto',
            'strategy_id': strategy_id,
            'config': strategy_config
        }
        logger.info(f"创建加密货币策略: {name}")
        return strategy_id
    
    async def run_strategy(self, name: str, data: pd.DataFrame) -> Dict[str, Any]:
        """运行策略"""
        if name not in self.strategies:
            raise ValueError(f"策略不存在: {name}")
        
        strategy = self.strategies[name]
        strategy_type = strategy['type']
        
        if strategy_type == 'ml':
            return await self._run_ml_strategy(strategy, data)
        elif strategy_type == 'option':
            return await self._run_option_strategy(strategy, data)
        elif strategy_type == 'crypto':
            return await self._run_crypto_strategy(strategy, data)
        else:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
    
    async def _run_ml_strategy(self, strategy: Dict, data: pd.DataFrame) -> Dict[str, Any]:
        """运行机器学习策略"""
        model_id = strategy['model_id']
        
        # 训练模型
        performance = self.ml_engine.train_model(model_id, data)
        
        # 预测
        predictions, probabilities = self.ml_engine.predict(model_id, data)
        
        # 生成交易信号
        signals = []
        for i, (pred, prob) in enumerate(zip(predictions, probabilities)):
            if pred == 1 and prob[1] > 0.6:  # 上涨概率大于60%
                signals.append({
                    'index': i,
                    'signal': 'buy',
                    'confidence': prob[1],
                    'timestamp': data.index[i] if hasattr(data.index, '__getitem__') else datetime.now()
                })
            elif pred == 0 and prob[0] > 0.6:  # 下跌概率大于60%
                signals.append({
                    'index': i,
                    'signal': 'sell',
                    'confidence': prob[0],
                    'timestamp': data.index[i] if hasattr(data.index, '__getitem__') else datetime.now()
                })
        
        return {
            'strategy_type': 'ml',
            'performance': asdict(performance),
            'signals': signals,
            'model_info': self.ml_engine.get_model_info(model_id)
        }
    
    async def _run_option_strategy(self, strategy: Dict, data: pd.DataFrame) -> Dict[str, Any]:
        """运行期权策略"""
        config = strategy['config']
        
        # 这里实现期权策略逻辑
        # 例如：跨式策略、蝶式策略等
        
        signals = []
        for i, row in data.iterrows():
            # 示例：基于波动率的期权策略
            if 'volatility' in row and row['volatility'] > 0.3:
                signals.append({
                    'index': i,
                    'signal': 'buy_straddle',
                    'confidence': 0.7,
                    'timestamp': i if hasattr(i, 'strftime') else datetime.now()
                })
        
        return {
            'strategy_type': 'option',
            'signals': signals,
            'config': config
        }
    
    async def _run_crypto_strategy(self, strategy: Dict, data: pd.DataFrame) -> Dict[str, Any]:
        """运行加密货币策略"""
        config = strategy['config']
        
        # 这里实现加密货币策略逻辑
        # 例如：动量策略、均值回归策略等
        
        signals = []
        for i, row in data.iterrows():
            # 示例：基于价格动量的策略
            if 'change_24h' in row and row['change_24h'] > 0.1:
                signals.append({
                    'index': i,
                    'signal': 'buy',
                    'confidence': 0.8,
                    'timestamp': i if hasattr(i, 'strftime') else datetime.now()
                })
        
        return {
            'strategy_type': 'crypto',
            'signals': signals,
            'config': config
        }

# 创建全局高级功能引擎实例
advanced_engine = AdvancedStrategyEngine()

# 便捷函数
def create_ml_model(model_type: ModelType, features: List[str], target: str, **kwargs) -> str:
    """创建机器学习模型的便捷函数"""
    config = ModelConfig(
        model_type=model_type,
        features=features,
        target=target,
        **kwargs
    )
    return advanced_engine.ml_engine.create_model(config)

def train_ml_model(model_id: str, data: pd.DataFrame) -> ModelPerformance:
    """训练机器学习模型的便捷函数"""
    return advanced_engine.ml_engine.train_model(model_id, data)

def predict_with_ml_model(model_id: str, data: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
    """使用机器学习模型预测的便捷函数"""
    return advanced_engine.ml_engine.predict(model_id, data)

def create_option_contract(symbol: str, strike: float, expiration: datetime, 
                          option_type: str, underlying_price: float, 
                          bid_price: float = 0, ask_price: float = 0) -> OptionContract:
    """创建期权合约的便捷函数"""
    return advanced_engine.option_engine.create_option_contract(
        symbol, strike, expiration, option_type, underlying_price, bid_price, ask_price
    )

async def get_crypto_data(symbols: List[str]) -> List[CryptoAsset]:
    """获取加密货币数据的便捷函数"""
    return await advanced_engine.crypto_provider.get_crypto_data(symbols)

async def get_crypto_historical_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """获取加密货币历史数据的便捷函数"""
    return await advanced_engine.crypto_provider.get_crypto_historical_data(symbol, days)

# 使用示例
async def example_advanced_features():
    """高级功能使用示例"""
    # 创建机器学习模型
    model_id = create_ml_model(
        model_type=ModelType.RANDOM_FOREST,
        features=['rsi', 'macd', 'bb_position'],
        target='future_return',
        n_estimators=100,
        max_depth=10
    )
    
    # 创建期权合约
    option = create_option_contract(
        symbol='AAPL',
        strike=150.0,
        expiration=datetime.now() + timedelta(days=30),
        option_type='call',
        underlying_price=155.0,
        bid_price=5.0,
        ask_price=5.5
    )
    
    # 获取加密货币数据
    crypto_data = await get_crypto_data(['bitcoin', 'ethereum'])
    
    print(f"机器学习模型ID: {model_id}")
    print(f"期权合约: {option.symbol} {option.strike} {option.option_type}")
    print(f"加密货币数据: {len(crypto_data)} 个资产")

if __name__ == "__main__":
    asyncio.run(example_advanced_features())
