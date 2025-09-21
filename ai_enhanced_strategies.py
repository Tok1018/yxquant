"""
AI增强策略模块
结合传统技术分析和AI智能分析
"""
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass
from enum import Enum

from ai_integration import ai_manager, QuantAIAnalyzer
from config import AI_CONFIG

logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号类型"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"

@dataclass
class TradingSignal:
    """交易信号数据结构"""
    symbol: str
    signal_type: SignalType
    confidence: float  # 0-1
    price: float
    target_price: float
    stop_loss: float
    reasoning: str
    ai_analysis: Dict[str, Any]
    timestamp: datetime
    strategy_name: str

class AIEnhancedStrategy:
    """AI增强策略基类"""
    
    def __init__(self, name: str, ai_analyzer: QuantAIAnalyzer):
        self.name = name
        self.ai_analyzer = ai_analyzer
        self.enabled = True
        self.parameters = {}
    
    async def analyze(self, symbol: str, data: pd.DataFrame) -> TradingSignal:
        """分析并生成交易信号"""
        raise NotImplementedError
    
    def update_parameters(self, params: Dict[str, Any]):
        """更新策略参数"""
        self.parameters.update(params)

class AIMomentumStrategy(AIEnhancedStrategy):
    """AI增强动量策略"""
    
    def __init__(self, ai_analyzer: QuantAIAnalyzer):
        super().__init__("AI_Momentum", ai_analyzer)
        self.parameters = {
            "lookback_period": 20,
            "momentum_threshold": 0.02,
            "volume_threshold": 1.5,
            "ai_weight": 0.3  # AI分析权重
        }
    
    async def analyze(self, symbol: str, data: pd.DataFrame) -> TradingSignal:
        """AI增强动量分析"""
        if len(data) < self.parameters["lookback_period"]:
            return self._create_hold_signal(symbol, "数据不足")
        
        # 传统技术分析
        traditional_signal = self._traditional_momentum_analysis(data)
        
        # AI分析
        ai_signal = await self.ai_analyzer.generate_trading_signals(symbol, data)
        
        # 结合传统分析和AI分析
        combined_signal = self._combine_signals(traditional_signal, ai_signal)
        
        return TradingSignal(
            symbol=symbol,
            signal_type=combined_signal["signal_type"],
            confidence=combined_signal["confidence"],
            price=data['close'].iloc[-1],
            target_price=combined_signal.get("target_price", data['close'].iloc[-1] * 1.1),
            stop_loss=combined_signal.get("stop_loss", data['close'].iloc[-1] * 0.95),
            reasoning=combined_signal["reasoning"],
            ai_analysis=ai_signal,
            timestamp=datetime.now(),
            strategy_name=self.name
        )
    
    def _traditional_momentum_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """传统动量分析"""
        close = data['close']
        volume = data['volume']
        
        # 计算动量指标
        returns = close.pct_change()
        momentum = (close.iloc[-1] / close.iloc[-self.parameters["lookback_period"]] - 1)
        
        # 成交量分析
        avg_volume = volume.rolling(self.parameters["lookback_period"]).mean().iloc[-1]
        volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1
        
        # 移动平均线分析
        ma_short = close.rolling(5).mean().iloc[-1]
        ma_long = close.rolling(20).mean().iloc[-1]
        ma_signal = 1 if ma_short > ma_long else -1
        
        # 综合评分
        momentum_score = momentum * 0.4
        volume_score = (volume_ratio - 1) * 0.3
        ma_score = ma_signal * 0.3
        
        total_score = momentum_score + volume_score + ma_score
        
        if total_score > self.parameters["momentum_threshold"]:
            signal_type = SignalType.BUY
            confidence = min(abs(total_score) * 2, 1.0)
        elif total_score < -self.parameters["momentum_threshold"]:
            signal_type = SignalType.SELL
            confidence = min(abs(total_score) * 2, 1.0)
        else:
            signal_type = SignalType.HOLD
            confidence = 0.5
        
        return {
            "signal_type": signal_type,
            "confidence": confidence,
            "momentum": momentum,
            "volume_ratio": volume_ratio,
            "ma_signal": ma_signal,
            "total_score": total_score
        }
    
    def _combine_signals(self, traditional: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        """结合传统分析和AI分析"""
        ai_weight = self.parameters["ai_weight"]
        traditional_weight = 1 - ai_weight
        
        # 转换AI信号为数值
        ai_signal_map = {
            "strong_buy": 2, "buy": 1, "hold": 0, 
            "sell": -1, "strong_sell": -2
        }
        
        ai_signal_value = ai_signal_map.get(ai.get("signal", "hold"), 0)
        traditional_signal_value = 1 if traditional["signal_type"] == SignalType.BUY else (-1 if traditional["signal_type"] == SignalType.SELL else 0)
        
        # 加权平均
        combined_value = (traditional_signal_value * traditional_weight + 
                         ai_signal_value * ai_weight)
        
        # 确定最终信号
        if combined_value > 1.5:
            signal_type = SignalType.STRONG_BUY
        elif combined_value > 0.5:
            signal_type = SignalType.BUY
        elif combined_value < -1.5:
            signal_type = SignalType.STRONG_SELL
        elif combined_value < -0.5:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        
        # 计算置信度
        confidence = (traditional["confidence"] * traditional_weight + 
                     ai.get("strength", 5) / 10 * ai_weight)
        
        reasoning = f"传统分析: {traditional['total_score']:.3f}, AI分析: {ai.get('analysis', 'N/A')}"
        
        return {
            "signal_type": signal_type,
            "confidence": min(confidence, 1.0),
            "reasoning": reasoning,
            "target_price": ai.get("target_price", 0),
            "stop_loss": ai.get("stop_loss", 0)
        }
    
    def _create_hold_signal(self, symbol: str, reason: str) -> TradingSignal:
        """创建持有信号"""
        return TradingSignal(
            symbol=symbol,
            signal_type=SignalType.HOLD,
            confidence=0.5,
            price=0,
            target_price=0,
            stop_loss=0,
            reasoning=reason,
            ai_analysis={},
            timestamp=datetime.now(),
            strategy_name=self.name
        )

class AIMeanReversionStrategy(AIEnhancedStrategy):
    """AI增强均值回归策略"""
    
    def __init__(self, ai_analyzer: QuantAIAnalyzer):
        super().__init__("AI_MeanReversion", ai_analyzer)
        self.parameters = {
            "lookback_period": 20,
            "deviation_threshold": 2.0,
            "rsi_oversold": 30,
            "rsi_overbought": 70,
            "ai_weight": 0.4
        }
    
    async def analyze(self, symbol: str, data: pd.DataFrame) -> TradingSignal:
        """AI增强均值回归分析"""
        if len(data) < self.parameters["lookback_period"]:
            return self._create_hold_signal(symbol, "数据不足")
        
        # 传统均值回归分析
        traditional_signal = self._traditional_mean_reversion_analysis(data)
        
        # AI分析
        ai_signal = await self.ai_analyzer.generate_trading_signals(symbol, data)
        
        # 结合分析
        combined_signal = self._combine_signals(traditional_signal, ai_signal)
        
        return TradingSignal(
            symbol=symbol,
            signal_type=combined_signal["signal_type"],
            confidence=combined_signal["confidence"],
            price=data['close'].iloc[-1],
            target_price=combined_signal.get("target_price", data['close'].iloc[-1] * 1.05),
            stop_loss=combined_signal.get("stop_loss", data['close'].iloc[-1] * 0.98),
            reasoning=combined_signal["reasoning"],
            ai_analysis=ai_signal,
            timestamp=datetime.now(),
            strategy_name=self.name
        )
    
    def _traditional_mean_reversion_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """传统均值回归分析"""
        close = data['close']
        
        # 布林带分析
        sma = close.rolling(self.parameters["lookback_period"]).mean()
        std = close.rolling(self.parameters["lookback_period"]).std()
        upper_band = sma + (std * 2)
        lower_band = sma - (std * 2)
        
        current_price = close.iloc[-1]
        current_upper = upper_band.iloc[-1]
        current_lower = lower_band.iloc[-1]
        current_sma = sma.iloc[-1]
        
        # 计算偏离度
        deviation = (current_price - current_sma) / std.iloc[-1] if std.iloc[-1] > 0 else 0
        
        # RSI分析
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # 信号判断
        if deviation < -self.parameters["deviation_threshold"] and current_rsi < self.parameters["rsi_oversold"]:
            signal_type = SignalType.BUY
            confidence = min(abs(deviation) / 3, 1.0)
        elif deviation > self.parameters["deviation_threshold"] and current_rsi > self.parameters["rsi_overbought"]:
            signal_type = SignalType.SELL
            confidence = min(abs(deviation) / 3, 1.0)
        else:
            signal_type = SignalType.HOLD
            confidence = 0.5
        
        return {
            "signal_type": signal_type,
            "confidence": confidence,
            "deviation": deviation,
            "rsi": current_rsi,
            "bollinger_position": (current_price - current_lower) / (current_upper - current_lower) if current_upper != current_lower else 0.5
        }
    
    def _combine_signals(self, traditional: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        """结合传统分析和AI分析"""
        ai_weight = self.parameters["ai_weight"]
        traditional_weight = 1 - ai_weight
        
        # 转换信号
        ai_signal_map = {
            "strong_buy": 2, "buy": 1, "hold": 0, 
            "sell": -1, "strong_sell": -2
        }
        
        ai_signal_value = ai_signal_map.get(ai.get("signal", "hold"), 0)
        traditional_signal_value = 1 if traditional["signal_type"] == SignalType.BUY else (-1 if traditional["signal_type"] == SignalType.SELL else 0)
        
        # 加权平均
        combined_value = (traditional_signal_value * traditional_weight + 
                         ai_signal_value * ai_weight)
        
        # 确定最终信号
        if combined_value > 1.5:
            signal_type = SignalType.STRONG_BUY
        elif combined_value > 0.5:
            signal_type = SignalType.BUY
        elif combined_value < -1.5:
            signal_type = SignalType.STRONG_SELL
        elif combined_value < -0.5:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        
        # 计算置信度
        confidence = (traditional["confidence"] * traditional_weight + 
                     ai.get("strength", 5) / 10 * ai_weight)
        
        reasoning = f"偏离度: {traditional['deviation']:.2f}, RSI: {traditional['rsi']:.1f}, AI: {ai.get('analysis', 'N/A')}"
        
        return {
            "signal_type": signal_type,
            "confidence": min(confidence, 1.0),
            "reasoning": reasoning,
            "target_price": ai.get("target_price", 0),
            "stop_loss": ai.get("stop_loss", 0)
        }
    
    def _create_hold_signal(self, symbol: str, reason: str) -> TradingSignal:
        """创建持有信号"""
        return TradingSignal(
            symbol=symbol,
            signal_type=SignalType.HOLD,
            confidence=0.5,
            price=0,
            target_price=0,
            stop_loss=0,
            reasoning=reason,
            ai_analysis={},
            timestamp=datetime.now(),
            strategy_name=self.name
        )

class AIBreakoutStrategy(AIEnhancedStrategy):
    """AI增强突破策略"""
    
    def __init__(self, ai_analyzer: QuantAIAnalyzer):
        super().__init__("AI_Breakout", ai_analyzer)
        self.parameters = {
            "lookback_period": 20,
            "breakout_threshold": 0.05,
            "volume_confirmation": True,
            "ai_weight": 0.35
        }
    
    async def analyze(self, symbol: str, data: pd.DataFrame) -> TradingSignal:
        """AI增强突破分析"""
        if len(data) < self.parameters["lookback_period"]:
            return self._create_hold_signal(symbol, "数据不足")
        
        # 传统突破分析
        traditional_signal = self._traditional_breakout_analysis(data)
        
        # AI分析
        ai_signal = await self.ai_analyzer.generate_trading_signals(symbol, data)
        
        # 结合分析
        combined_signal = self._combine_signals(traditional_signal, ai_signal)
        
        return TradingSignal(
            symbol=symbol,
            signal_type=combined_signal["signal_type"],
            confidence=combined_signal["confidence"],
            price=data['close'].iloc[-1],
            target_price=combined_signal.get("target_price", data['close'].iloc[-1] * 1.15),
            stop_loss=combined_signal.get("stop_loss", data['close'].iloc[-1] * 0.95),
            reasoning=combined_signal["reasoning"],
            ai_analysis=ai_signal,
            timestamp=datetime.now(),
            strategy_name=self.name
        )
    
    def _traditional_breakout_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """传统突破分析"""
        close = data['close']
        high = data['high']
        low = data['low']
        volume = data['volume']
        
        # 计算阻力位和支撑位
        lookback = self.parameters["lookback_period"]
        resistance = high.rolling(lookback).max()
        support = low.rolling(lookback).min()
        
        current_price = close.iloc[-1]
        current_resistance = resistance.iloc[-1]
        current_support = support.iloc[-1]
        
        # 计算突破幅度
        resistance_breakout = (current_price - current_resistance) / current_resistance
        support_breakout = (current_support - current_price) / current_price
        
        # 成交量确认
        avg_volume = volume.rolling(lookback).mean().iloc[-1]
        volume_ratio = volume.iloc[-1] / avg_volume if avg_volume > 0 else 1
        volume_confirmed = volume_ratio > 1.2 if self.parameters["volume_confirmation"] else True
        
        # 信号判断
        if (resistance_breakout > self.parameters["breakout_threshold"] and 
            volume_confirmed):
            signal_type = SignalType.BUY
            confidence = min(resistance_breakout * 10, 1.0)
        elif (support_breakout > self.parameters["breakout_threshold"] and 
              volume_confirmed):
            signal_type = SignalType.SELL
            confidence = min(support_breakout * 10, 1.0)
        else:
            signal_type = SignalType.HOLD
            confidence = 0.5
        
        return {
            "signal_type": signal_type,
            "confidence": confidence,
            "resistance_breakout": resistance_breakout,
            "support_breakout": support_breakout,
            "volume_ratio": volume_ratio,
            "volume_confirmed": volume_confirmed
        }
    
    def _combine_signals(self, traditional: Dict[str, Any], ai: Dict[str, Any]) -> Dict[str, Any]:
        """结合传统分析和AI分析"""
        ai_weight = self.parameters["ai_weight"]
        traditional_weight = 1 - ai_weight
        
        # 转换信号
        ai_signal_map = {
            "strong_buy": 2, "buy": 1, "hold": 0, 
            "sell": -1, "strong_sell": -2
        }
        
        ai_signal_value = ai_signal_map.get(ai.get("signal", "hold"), 0)
        traditional_signal_value = 1 if traditional["signal_type"] == SignalType.BUY else (-1 if traditional["signal_type"] == SignalType.SELL else 0)
        
        # 加权平均
        combined_value = (traditional_signal_value * traditional_weight + 
                         ai_signal_value * ai_weight)
        
        # 确定最终信号
        if combined_value > 1.5:
            signal_type = SignalType.STRONG_BUY
        elif combined_value > 0.5:
            signal_type = SignalType.BUY
        elif combined_value < -1.5:
            signal_type = SignalType.STRONG_SELL
        elif combined_value < -0.5:
            signal_type = SignalType.SELL
        else:
            signal_type = SignalType.HOLD
        
        # 计算置信度
        confidence = (traditional["confidence"] * traditional_weight + 
                     ai.get("strength", 5) / 10 * ai_weight)
        
        reasoning = f"突破幅度: {max(traditional['resistance_breakout'], traditional['support_breakout']):.3f}, 成交量: {traditional['volume_ratio']:.2f}, AI: {ai.get('analysis', 'N/A')}"
        
        return {
            "signal_type": signal_type,
            "confidence": min(confidence, 1.0),
            "reasoning": reasoning,
            "target_price": ai.get("target_price", 0),
            "stop_loss": ai.get("stop_loss", 0)
        }
    
    def _create_hold_signal(self, symbol: str, reason: str) -> TradingSignal:
        """创建持有信号"""
        return TradingSignal(
            symbol=symbol,
            signal_type=SignalType.HOLD,
            confidence=0.5,
            price=0,
            target_price=0,
            stop_loss=0,
            reasoning=reason,
            ai_analysis={},
            timestamp=datetime.now(),
            strategy_name=self.name
        )

class AIStrategyManager:
    """AI策略管理器"""
    
    def __init__(self, ai_analyzer: QuantAIAnalyzer):
        self.ai_analyzer = ai_analyzer
        self.strategies: Dict[str, AIEnhancedStrategy] = {}
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """初始化策略"""
        self.strategies = {
            "momentum": AIMomentumStrategy(self.ai_analyzer),
            "mean_reversion": AIMeanReversionStrategy(self.ai_analyzer),
            "breakout": AIBreakoutStrategy(self.ai_analyzer)
        }
        logger.info(f"初始化了 {len(self.strategies)} 个AI增强策略")
    
    async def analyze_symbol(self, symbol: str, data: pd.DataFrame, 
                           strategy_names: List[str] = None) -> Dict[str, TradingSignal]:
        """分析单个股票"""
        if strategy_names is None:
            strategy_names = list(self.strategies.keys())
        
        results = {}
        for strategy_name in strategy_names:
            if strategy_name not in self.strategies:
                continue
            
            try:
                strategy = self.strategies[strategy_name]
                if strategy.enabled:
                    signal = await strategy.analyze(symbol, data)
                    results[strategy_name] = signal
            except Exception as e:
                logger.error(f"策略 {strategy_name} 分析失败: {e}")
                continue
        
        return results
    
    async def get_consensus_signal(self, symbol: str, data: pd.DataFrame) -> TradingSignal:
        """获取共识信号"""
        signals = await self.analyze_symbol(symbol, data)
        
        if not signals:
            return TradingSignal(
                symbol=symbol,
                signal_type=SignalType.HOLD,
                confidence=0.0,
                price=data['close'].iloc[-1] if not data.empty else 0,
                target_price=0,
                stop_loss=0,
                reasoning="无可用策略",
                ai_analysis={},
                timestamp=datetime.now(),
                strategy_name="consensus"
            )
        
        # 计算加权平均信号
        signal_weights = {
            SignalType.STRONG_BUY: 2,
            SignalType.BUY: 1,
            SignalType.HOLD: 0,
            SignalType.SELL: -1,
            SignalType.STRONG_SELL: -2
        }
        
        total_weight = 0
        weighted_sum = 0
        total_confidence = 0
        reasoning_parts = []
        
        for strategy_name, signal in signals.items():
            weight = signal_weights[signal.signal_type] * signal.confidence
            weighted_sum += weight
            total_weight += signal.confidence
            total_confidence += signal.confidence
            reasoning_parts.append(f"{strategy_name}: {signal.signal_type.value}")
        
        if total_weight == 0:
            consensus_type = SignalType.HOLD
            consensus_confidence = 0.0
        else:
            avg_signal = weighted_sum / total_weight
            
            if avg_signal > 1.5:
                consensus_type = SignalType.STRONG_BUY
            elif avg_signal > 0.5:
                consensus_type = SignalType.BUY
            elif avg_signal < -1.5:
                consensus_type = SignalType.STRONG_SELL
            elif avg_signal < -0.5:
                consensus_type = SignalType.SELL
            else:
                consensus_type = SignalType.HOLD
            
            consensus_confidence = min(total_confidence / len(signals), 1.0)
        
        # 计算目标价和止损价
        target_prices = [s.target_price for s in signals.values() if s.target_price > 0]
        stop_losses = [s.stop_loss for s in signals.values() if s.stop_loss > 0]
        
        avg_target = np.mean(target_prices) if target_prices else data['close'].iloc[-1] * 1.1
        avg_stop_loss = np.mean(stop_losses) if stop_losses else data['close'].iloc[-1] * 0.95
        
        return TradingSignal(
            symbol=symbol,
            signal_type=consensus_type,
            confidence=consensus_confidence,
            price=data['close'].iloc[-1] if not data.empty else 0,
            target_price=avg_target,
            stop_loss=avg_stop_loss,
            reasoning="; ".join(reasoning_parts),
            ai_analysis={"individual_signals": {k: v.ai_analysis for k, v in signals.items()}},
            timestamp=datetime.now(),
            strategy_name="consensus"
        )
    
    def enable_strategy(self, strategy_name: str):
        """启用策略"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].enabled = True
            logger.info(f"启用策略: {strategy_name}")
    
    def disable_strategy(self, strategy_name: str):
        """禁用策略"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].enabled = False
            logger.info(f"禁用策略: {strategy_name}")
    
    def update_strategy_parameters(self, strategy_name: str, parameters: Dict[str, Any]):
        """更新策略参数"""
        if strategy_name in self.strategies:
            self.strategies[strategy_name].update_parameters(parameters)
            logger.info(f"更新策略参数: {strategy_name}")

# 创建AI策略管理器实例
def create_ai_strategy_manager():
    """创建AI策略管理器"""
    from ai_integration import quant_ai
    return AIStrategyManager(quant_ai)

if __name__ == "__main__":
    # 示例使用
    async def main():
        strategy_manager = create_ai_strategy_manager()
        
        # 模拟数据
        data = pd.DataFrame({
            'close': [100, 102, 101, 103, 105, 107, 106, 108, 110, 112],
            'volume': [1000, 1200, 900, 1100, 1300, 1500, 1200, 1400, 1600, 1800]
        })
        
        # 分析单个策略
        signals = await strategy_manager.analyze_symbol("AAPL", data, ["momentum"])
        print("动量策略信号:", signals)
        
        # 获取共识信号
        consensus = await strategy_manager.get_consensus_signal("AAPL", data)
        print("共识信号:", consensus)
    
    # asyncio.run(main())
