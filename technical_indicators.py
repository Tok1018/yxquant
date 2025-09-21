"""
技术指标计算模块
支持MACD、CCI、KDJ、BOLL、RSI、均线等完整技术指标
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
# 使用自定义实现，不依赖TA-Lib
# import talib

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IndicatorType(Enum):
    """技术指标类型枚举"""
    TREND = "trend"          # 趋势指标
    MOMENTUM = "momentum"     # 动量指标
    VOLATILITY = "volatility" # 波动率指标
    VOLUME = "volume"         # 成交量指标
    OSCILLATOR = "oscillator" # 震荡指标

@dataclass
class IndicatorConfig:
    """指标配置"""
    name: str
    indicator_type: IndicatorType
    parameters: Dict[str, Union[int, float]]
    description: str = ""

class TechnicalIndicators:
    """技术指标计算类"""
    
    def __init__(self):
        self.indicators_config = self._init_indicators_config()
    
    def _init_indicators_config(self) -> Dict[str, IndicatorConfig]:
        """初始化指标配置"""
        return {
            # 趋势指标
            "SMA": IndicatorConfig("SMA", IndicatorType.TREND, {"period": 20}, "简单移动平均"),
            "EMA": IndicatorConfig("EMA", IndicatorType.TREND, {"period": 20}, "指数移动平均"),
            "WMA": IndicatorConfig("WMA", IndicatorType.TREND, {"period": 20}, "加权移动平均"),
            "MACD": IndicatorConfig("MACD", IndicatorType.TREND, {"fast": 12, "slow": 26, "signal": 9}, "MACD指标"),
            "ADX": IndicatorConfig("ADX", IndicatorType.TREND, {"period": 14}, "平均趋向指数"),
            "AROON": IndicatorConfig("AROON", IndicatorType.TREND, {"period": 14}, "阿隆指标"),
            
            # 动量指标
            "RSI": IndicatorConfig("RSI", IndicatorType.MOMENTUM, {"period": 14}, "相对强弱指数"),
            "CCI": IndicatorConfig("CCI", IndicatorType.MOMENTUM, {"period": 20}, "商品通道指数"),
            "ROC": IndicatorConfig("ROC", IndicatorType.MOMENTUM, {"period": 10}, "变化率"),
            "MOM": IndicatorConfig("MOM", IndicatorType.MOMENTUM, {"period": 10}, "动量"),
            "WILLR": IndicatorConfig("WILLR", IndicatorType.MOMENTUM, {"period": 14}, "威廉指标"),
            "STOCH": IndicatorConfig("STOCH", IndicatorType.MOMENTUM, {"k_period": 14, "d_period": 3}, "随机指标"),
            
            # 波动率指标
            "BBANDS": IndicatorConfig("BBANDS", IndicatorType.VOLATILITY, {"period": 20, "std": 2}, "布林带"),
            "ATR": IndicatorConfig("ATR", IndicatorType.VOLATILITY, {"period": 14}, "平均真实波幅"),
            "NATR": IndicatorConfig("NATR", IndicatorType.VOLATILITY, {"period": 14}, "标准化ATR"),
            "TRANGE": IndicatorConfig("TRANGE", IndicatorType.VOLATILITY, {}, "真实波幅"),
            
            # 成交量指标
            "OBV": IndicatorConfig("OBV", IndicatorType.VOLUME, {}, "能量潮"),
            "AD": IndicatorConfig("AD", IndicatorType.VOLUME, {}, "累积/派发线"),
            "ADOSC": IndicatorConfig("ADOSC", IndicatorType.VOLUME, {"fast": 3, "slow": 10}, "累积/派发震荡器"),
            "MFI": IndicatorConfig("MFI", IndicatorType.VOLUME, {"period": 14}, "资金流量指数"),
            
            # 震荡指标
            "KDJ": IndicatorConfig("KDJ", IndicatorType.OSCILLATOR, {"k_period": 9, "d_period": 3, "j_period": 3}, "KDJ指标"),
            "CCI": IndicatorConfig("CCI", IndicatorType.OSCILLATOR, {"period": 20}, "商品通道指数"),
            "UO": IndicatorConfig("UO", IndicatorType.OSCILLATOR, {"fast": 7, "medium": 14, "slow": 28}, "终极震荡器"),
        }
    
    def calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标"""
        if data.empty:
            return data
        
        result = data.copy()
        
        # 确保数据包含必要的列
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in required_columns:
            if col not in data.columns:
                logger.error(f"数据缺少必要列: {col}")
                return data
        
        # 计算各类指标
        result = self._calculate_trend_indicators(result)
        result = self._calculate_momentum_indicators(result)
        result = self._calculate_volatility_indicators(result)
        result = self._calculate_volume_indicators(result)
        result = self._calculate_oscillator_indicators(result)
        
        return result
    
    def _calculate_trend_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算趋势指标"""
        result = data.copy()
        
        try:
            # 简单移动平均
            result['SMA_20'] = data['close'].rolling(window=20).mean()
            result['SMA_50'] = data['close'].rolling(window=50).mean()
            result['SMA_200'] = data['close'].rolling(window=200).mean()
            
            # 指数移动平均
            result['EMA_12'] = data['close'].ewm(span=12).mean()
            result['EMA_26'] = data['close'].ewm(span=26).mean()
            result['EMA_50'] = data['close'].ewm(span=50).mean()
            
            # MACD
            ema_12 = data['close'].ewm(span=12).mean()
            ema_26 = data['close'].ewm(span=26).mean()
            macd = ema_12 - ema_26
            macd_signal = macd.ewm(span=9).mean()
            macd_hist = macd - macd_signal
            
            result['MACD'] = macd
            result['MACD_Signal'] = macd_signal
            result['MACD_Hist'] = macd_hist
            
            # ADX (简化实现)
            result['ADX'] = _calculate_adx(data, 14)
            result['ADXR'] = result['ADX'].rolling(window=14).mean()
            
            # AROON (简化实现)
            aroon_down, aroon_up = _calculate_aroon(data, 14)
            result['AROON_Down'] = aroon_down
            result['AROON_Up'] = aroon_up
            result['AROON_Osc'] = aroon_up - aroon_down
            
        except Exception as e:
            logger.error(f"计算趋势指标失败: {e}")
        
        return result
    
    def _calculate_momentum_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算动量指标"""
        result = data.copy()
        
        try:
            # RSI
            result['RSI_14'] = _calculate_rsi(data['close'], 14)
            result['RSI_21'] = _calculate_rsi(data['close'], 21)
            
            # CCI
            result['CCI_20'] = _calculate_cci(data, 20)
            
            # ROC
            result['ROC_10'] = data['close'].pct_change(periods=10) * 100
            result['ROC_20'] = data['close'].pct_change(periods=20) * 100
            
            # MOM
            result['MOM_10'] = data['close'] - data['close'].shift(10)
            
            # WILLR
            result['WILLR_14'] = _calculate_williams_r(data, 14)
            
            # STOCH
            stoch_k, stoch_d = _calculate_stochastic(data, 14, 3)
            result['STOCH_K'] = stoch_k
            result['STOCH_D'] = stoch_d
            
            # STOCHF (快速随机指标)
            stochf_k, stochf_d = _calculate_stochastic_fast(data, 14, 3)
            result['STOCHF_K'] = stochf_k
            result['STOCHF_D'] = stochf_d
            
        except Exception as e:
            logger.error(f"计算动量指标失败: {e}")
        
        return result
    
    def _calculate_volatility_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算波动率指标"""
        result = data.copy()
        
        try:
            # 布林带
            bb_upper, bb_middle, bb_lower = _calculate_bollinger_bands(data['close'], 20, 2)
            result['BB_Upper'] = bb_upper
            result['BB_Middle'] = bb_middle
            result['BB_Lower'] = bb_lower
            result['BB_Width'] = (bb_upper - bb_lower) / bb_middle
            result['BB_Position'] = (data['close'] - bb_lower) / (bb_upper - bb_lower)
            
            # ATR
            result['ATR_14'] = _calculate_atr(data, 14)
            result['NATR_14'] = result['ATR_14'] / data['close'] * 100
            result['TRANGE'] = _calculate_true_range(data)
            
        except Exception as e:
            logger.error(f"计算波动率指标失败: {e}")
        
        return result
    
    def _calculate_volume_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算成交量指标"""
        result = data.copy()
        
        try:
            # OBV (简化实现)
            result['OBV'] = _calculate_obv(data)
            
            # AD (简化实现)
            result['AD'] = _calculate_ad(data)
            
            # ADOSC (简化实现)
            result['ADOSC'] = _calculate_adosc(data)
            
            # MFI (简化实现)
            result['MFI_14'] = _calculate_mfi(data, 14)
            
        except Exception as e:
            logger.error(f"计算成交量指标失败: {e}")
        
        return result
    
    def _calculate_oscillator_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算震荡指标"""
        result = data.copy()
        
        try:
            # KDJ指标（自定义实现）
            result = self._calculate_kdj(result)
            
            # CCI（已在动量指标中计算）
            
            # 终极震荡器（简化实现）
            result['UO'] = _calculate_ultimate_oscillator(data)
            
        except Exception as e:
            logger.error(f"计算震荡指标失败: {e}")
        
        return result
    
    def _calculate_kdj(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算KDJ指标"""
        try:
            # 计算RSV
            low_min = data['low'].rolling(window=9).min()
            high_max = data['high'].rolling(window=9).max()
            rsv = (data['close'] - low_min) / (high_max - low_min) * 100
            
            # 计算K值
            k = rsv.ewm(alpha=1/3).mean()
            
            # 计算D值
            d = k.ewm(alpha=1/3).mean()
            
            # 计算J值
            j = 3 * k - 2 * d
            
            result = data.copy()
            result['KDJ_K'] = k
            result['KDJ_D'] = d
            result['KDJ_J'] = j
            
            return result
            
        except Exception as e:
            logger.error(f"计算KDJ指标失败: {e}")
            return data
    
    def calculate_single_indicator(self, data: pd.DataFrame, indicator_name: str, **kwargs) -> pd.Series:
        """计算单个技术指标"""
        if indicator_name not in self.indicators_config:
            logger.error(f"不支持的指标: {indicator_name}")
            return pd.Series()
        
        config = self.indicators_config[indicator_name]
        
        try:
            if indicator_name == "SMA":
                period = kwargs.get('period', config.parameters['period'])
                return data['close'].rolling(window=period).mean()
            
            elif indicator_name == "EMA":
                period = kwargs.get('period', config.parameters['period'])
                return data['close'].ewm(span=period).mean()
            
            elif indicator_name == "RSI":
                period = kwargs.get('period', config.parameters['period'])
                return _calculate_rsi(data['close'], period)
            
            elif indicator_name == "MACD":
                fast = kwargs.get('fast', config.parameters['fast'])
                slow = kwargs.get('slow', config.parameters['slow'])
                signal = kwargs.get('signal', config.parameters['signal'])
                ema_fast = data['close'].ewm(span=fast).mean()
                ema_slow = data['close'].ewm(span=slow).mean()
                macd = ema_fast - ema_slow
                return macd
            
            elif indicator_name == "BBANDS":
                period = kwargs.get('period', config.parameters['period'])
                std = kwargs.get('std', config.parameters['std'])
                upper, middle, lower = _calculate_bollinger_bands(data['close'], period, std)
                return pd.DataFrame({'upper': upper, 'middle': middle, 'lower': lower})
            
            elif indicator_name == "CCI":
                period = kwargs.get('period', config.parameters['period'])
                return _calculate_cci(data, period)
            
            else:
                logger.warning(f"指标{indicator_name}需要特殊处理")
                return pd.Series()
                
        except Exception as e:
            logger.error(f"计算指标{indicator_name}失败: {e}")
            return pd.Series()
    
    def get_support_resistance_levels(self, data: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
        """计算支撑阻力位"""
        try:
            highs = data['high'].rolling(window=window).max()
            lows = data['low'].rolling(window=window).min()
            
            # 找出局部高点和低点
            resistance_levels = []
            support_levels = []
            
            for i in range(window, len(data)):
                if data['high'].iloc[i] == highs.iloc[i]:
                    resistance_levels.append(data['high'].iloc[i])
                if data['low'].iloc[i] == lows.iloc[i]:
                    support_levels.append(data['low'].iloc[i])
            
            return {
                'resistance': sorted(set(resistance_levels), reverse=True)[:5],
                'support': sorted(set(support_levels), reverse=True)[:5]
            }
            
        except Exception as e:
            logger.error(f"计算支撑阻力位失败: {e}")
            return {'resistance': [], 'support': []}
    
    def detect_patterns(self, data: pd.DataFrame) -> Dict[str, List[int]]:
        """检测技术形态（简化实现）"""
        patterns = {}
        
        try:
            # 简化的形态检测
            patterns['doji'] = _detect_doji(data)
            patterns['hammer'] = _detect_hammer(data)
            patterns['hanging_man'] = _detect_hanging_man(data)
            patterns['engulfing'] = _detect_engulfing(data)
            patterns['harami'] = _detect_harami(data)
            patterns['morning_star'] = _detect_morning_star(data)
            patterns['evening_star'] = _detect_evening_star(data)
            
            return patterns
            
        except Exception as e:
            logger.error(f"检测技术形态失败: {e}")
            return {}

# 创建全局技术指标计算器实例
indicators_calculator = TechnicalIndicators()

# 便捷函数
def calculate_indicators(data: pd.DataFrame) -> pd.DataFrame:
    """计算所有技术指标的便捷函数"""
    return indicators_calculator.calculate_all_indicators(data)

def calculate_single_indicator(data: pd.DataFrame, indicator_name: str, **kwargs) -> pd.Series:
    """计算单个技术指标的便捷函数"""
    return indicators_calculator.calculate_single_indicator(data, indicator_name, **kwargs)

def get_support_resistance(data: pd.DataFrame, window: int = 20) -> Dict[str, List[float]]:
    """获取支撑阻力位的便捷函数"""
    return indicators_calculator.get_support_resistance_levels(data, window)

def detect_patterns(data: pd.DataFrame) -> Dict[str, List[int]]:
    """检测技术形态的便捷函数"""
    return indicators_calculator.detect_patterns(data)

# 自定义技术指标计算函数
def _calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """计算RSI指标"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def _calculate_cci(data: pd.DataFrame, period: int = 20) -> pd.Series:
    """计算CCI指标"""
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    sma = typical_price.rolling(window=period).mean()
    mad = typical_price.rolling(window=period).apply(lambda x: np.mean(np.abs(x - x.mean())))
    cci = (typical_price - sma) / (0.015 * mad)
    return cci

def _calculate_williams_r(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算威廉指标"""
    highest_high = data['high'].rolling(window=period).max()
    lowest_low = data['low'].rolling(window=period).min()
    williams_r = -100 * (highest_high - data['close']) / (highest_high - lowest_low)
    return williams_r

def _calculate_stochastic(data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """计算随机指标"""
    lowest_low = data['low'].rolling(window=k_period).min()
    highest_high = data['high'].rolling(window=k_period).max()
    k_percent = 100 * (data['close'] - lowest_low) / (highest_high - lowest_low)
    d_percent = k_percent.rolling(window=d_period).mean()
    return k_percent, d_percent

def _calculate_stochastic_fast(data: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """计算快速随机指标"""
    return _calculate_stochastic(data, k_period, d_period)

def _calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """计算布林带"""
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    return upper, middle, lower

def _calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算ATR指标"""
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    atr = true_range.rolling(window=period).mean()
    return atr

def _calculate_true_range(data: pd.DataFrame) -> pd.Series:
    """计算真实波幅"""
    high_low = data['high'] - data['low']
    high_close = np.abs(data['high'] - data['close'].shift())
    low_close = np.abs(data['low'] - data['close'].shift())
    true_range = np.maximum(high_low, np.maximum(high_close, low_close))
    return true_range

def _calculate_adx(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算ADX指标（简化实现）"""
    high_diff = data['high'].diff()
    low_diff = data['low'].diff()
    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
    
    atr = _calculate_atr(data, period)
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
    
    dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()
    return adx

def _calculate_aroon(data: pd.DataFrame, period: int = 14) -> Tuple[pd.Series, pd.Series]:
    """计算AROON指标"""
    aroon_up = data['high'].rolling(window=period).apply(lambda x: (period - x.argmax()) / period * 100)
    aroon_down = data['low'].rolling(window=period).apply(lambda x: (period - x.argmin()) / period * 100)
    return aroon_down, aroon_up

def _calculate_obv(data: pd.DataFrame) -> pd.Series:
    """计算OBV指标"""
    obv = np.zeros(len(data))
    obv[0] = data['volume'].iloc[0]
    
    for i in range(1, len(data)):
        if data['close'].iloc[i] > data['close'].iloc[i-1]:
            obv[i] = obv[i-1] + data['volume'].iloc[i]
        elif data['close'].iloc[i] < data['close'].iloc[i-1]:
            obv[i] = obv[i-1] - data['volume'].iloc[i]
        else:
            obv[i] = obv[i-1]
    
    return pd.Series(obv, index=data.index)

def _calculate_ad(data: pd.DataFrame) -> pd.Series:
    """计算AD指标"""
    clv = ((data['close'] - data['low']) - (data['high'] - data['close'])) / (data['high'] - data['low'])
    clv = clv.fillna(0)  # 处理除零情况
    ad = (clv * data['volume']).cumsum()
    return ad

def _calculate_adosc(data: pd.DataFrame, fast: int = 3, slow: int = 10) -> pd.Series:
    """计算ADOSC指标"""
    ad = _calculate_ad(data)
    adosc = ad.rolling(window=fast).mean() - ad.rolling(window=slow).mean()
    return adosc

def _calculate_mfi(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """计算MFI指标"""
    typical_price = (data['high'] + data['low'] + data['close']) / 3
    money_flow = typical_price * data['volume']
    
    positive_flow = money_flow.where(typical_price > typical_price.shift(1), 0).rolling(window=period).sum()
    negative_flow = money_flow.where(typical_price < typical_price.shift(1), 0).rolling(window=period).sum()
    
    mfi = 100 - (100 / (1 + positive_flow / negative_flow))
    return mfi

def _calculate_ultimate_oscillator(data: pd.DataFrame) -> pd.Series:
    """计算终极震荡器"""
    tr = _calculate_true_range(data)
    bp = data['close'] - data['low'].rolling(window=7).min()
    rp = data['high'].rolling(window=7).max() - data['close']
    
    avg7 = bp.rolling(window=7).sum() / tr.rolling(window=7).sum()
    avg14 = bp.rolling(window=14).sum() / tr.rolling(window=14).sum()
    avg28 = bp.rolling(window=28).sum() / tr.rolling(window=28).sum()
    
    uo = 100 * (4 * avg7 + 2 * avg14 + avg28) / 7
    return uo

# 形态检测函数
def _detect_doji(data: pd.DataFrame) -> List[int]:
    """检测十字星形态"""
    body_size = np.abs(data['close'] - data['open'])
    total_range = data['high'] - data['low']
    doji_condition = (body_size / total_range) < 0.1
    return [i for i, val in enumerate(doji_condition) if val]

def _detect_hammer(data: pd.DataFrame) -> List[int]:
    """检测锤子形态"""
    body_size = np.abs(data['close'] - data['open'])
    lower_shadow = np.minimum(data['open'], data['close']) - data['low']
    upper_shadow = data['high'] - np.maximum(data['open'], data['close'])
    total_range = data['high'] - data['low']
    
    hammer_condition = (
        (lower_shadow > 2 * body_size) & 
        (upper_shadow < body_size) & 
        (data['close'] > data['open'])
    )
    return [i for i, val in enumerate(hammer_condition) if val]

def _detect_hanging_man(data: pd.DataFrame) -> List[int]:
    """检测上吊线形态"""
    body_size = np.abs(data['close'] - data['open'])
    lower_shadow = np.minimum(data['open'], data['close']) - data['low']
    upper_shadow = data['high'] - np.maximum(data['open'], data['close'])
    total_range = data['high'] - data['low']
    
    hanging_man_condition = (
        (lower_shadow > 2 * body_size) & 
        (upper_shadow < body_size) & 
        (data['close'] < data['open'])
    )
    return [i for i, val in enumerate(hanging_man_condition) if val]

def _detect_engulfing(data: pd.DataFrame) -> List[int]:
    """检测吞没形态"""
    prev_body = np.abs(data['close'].shift(1) - data['open'].shift(1))
    curr_body = np.abs(data['close'] - data['open'])
    
    bullish_engulfing = (
        (data['close'].shift(1) < data['open'].shift(1)) &  # 前一根是阴线
        (data['close'] > data['open']) &  # 当前是阳线
        (data['open'] < data['close'].shift(1)) &  # 当前开盘价低于前一根收盘价
        (data['close'] > data['open'].shift(1)) &  # 当前收盘价高于前一根开盘价
        (curr_body > prev_body)  # 当前实体大于前一根
    )
    
    bearish_engulfing = (
        (data['close'].shift(1) > data['open'].shift(1)) &  # 前一根是阳线
        (data['close'] < data['open']) &  # 当前是阴线
        (data['open'] > data['close'].shift(1)) &  # 当前开盘价高于前一根收盘价
        (data['close'] < data['open'].shift(1)) &  # 当前收盘价低于前一根开盘价
        (curr_body > prev_body)  # 当前实体大于前一根
    )
    
    engulfing_condition = bullish_engulfing | bearish_engulfing
    return [i for i, val in enumerate(engulfing_condition) if val]

def _detect_harami(data: pd.DataFrame) -> List[int]:
    """检测孕线形态"""
    prev_body = np.abs(data['close'].shift(1) - data['open'].shift(1))
    curr_body = np.abs(data['close'] - data['open'])
    
    harami_condition = (
        (prev_body > curr_body) &  # 前一根实体大于当前实体
        (data['open'] > data['close'].shift(1)) &  # 当前开盘价在前一根实体范围内
        (data['close'] < data['open'].shift(1)) &  # 当前收盘价在前一根实体范围内
        (data['open'] < data['open'].shift(1)) &  # 当前开盘价在前一根开盘价下方
        (data['close'] > data['close'].shift(1))  # 当前收盘价在前一根收盘价上方
    )
    return [i for i, val in enumerate(harami_condition) if val]

def _detect_morning_star(data: pd.DataFrame) -> List[int]:
    """检测晨星形态（简化实现）"""
    # 简化的晨星检测
    star_condition = (
        (data['close'].shift(2) < data['open'].shift(2)) &  # 第一根是阴线
        (np.abs(data['close'].shift(1) - data['open'].shift(1)) < 
         np.abs(data['close'].shift(2) - data['open'].shift(2)) * 0.3) &  # 第二根是小实体
        (data['close'] > data['open']) &  # 第三根是阳线
        (data['close'] > (data['open'].shift(2) + data['close'].shift(2)) / 2)  # 第三根收盘价超过第一根中点
    )
    return [i for i, val in enumerate(star_condition) if val]

def _detect_evening_star(data: pd.DataFrame) -> List[int]:
    """检测暮星形态（简化实现）"""
    # 简化的暮星检测
    star_condition = (
        (data['close'].shift(2) > data['open'].shift(2)) &  # 第一根是阳线
        (np.abs(data['close'].shift(1) - data['open'].shift(1)) < 
         np.abs(data['close'].shift(2) - data['open'].shift(2)) * 0.3) &  # 第二根是小实体
        (data['close'] < data['open']) &  # 第三根是阴线
        (data['close'] < (data['open'].shift(2) + data['close'].shift(2)) / 2)  # 第三根收盘价低于第一根中点
    )
    return [i for i, val in enumerate(star_condition) if val]
