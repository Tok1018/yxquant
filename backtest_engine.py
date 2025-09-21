"""
回测引擎模块
支持多种策略回测、成本计算、性能分析
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from abc import ABC, abstractmethod
import asyncio

from database import db_manager
from data_acquisition import data_manager, DataSource
from technical_indicators import indicators_calculator
from ai_enhanced_strategies import create_ai_strategy_manager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SignalType(Enum):
    """信号类型枚举"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"

class OrderType(Enum):
    """订单类型枚举"""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

@dataclass
class Trade:
    """交易记录"""
    symbol: str
    side: SignalType
    quantity: float
    price: float
    timestamp: datetime
    order_type: OrderType = OrderType.MARKET
    commission: float = 0.0
    slippage: float = 0.0
    trade_id: str = ""

@dataclass
class Position:
    """持仓信息"""
    symbol: str
    quantity: float
    avg_price: float
    market_value: float
    unrealized_pnl: float
    realized_pnl: float = 0.0

@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 1000000.0
    start_date: str = "2023-01-01"
    end_date: str = "2024-01-01"
    commission_rate: float = 0.001  # 佣金费率
    slippage_rate: float = 0.0005   # 滑点费率
    max_position_size: float = 0.1  # 单股最大仓位比例
    max_total_position: float = 0.95 # 总仓位上限
    rebalance_frequency: str = "daily"  # 调仓频率
    benchmark: str = "000001.SH"  # 基准指数（上证指数）
    risk_free_rate: float = 0.02  # 无风险利率

@dataclass
class BacktestResults:
    """回测结果"""
    total_return: float
    annual_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    win_rate: float
    profit_factor: float
    trades: List[Trade] = field(default_factory=list)
    positions: Dict[str, Position] = field(default_factory=dict)
    daily_returns: pd.Series = field(default_factory=pd.Series)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    benchmark_returns: pd.Series = field(default_factory=pd.Series)

class Strategy(ABC):
    """策略基类"""
    
    def __init__(self, name: str, config: Dict = None):
        self.name = name
        self.config = config or {}
        self.positions = {}
        self.trades = []
    
    @abstractmethod
    async def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, SignalType]:
        """生成交易信号"""
        pass
    
    @abstractmethod
    def calculate_position_size(self, symbol: str, signal: SignalType, 
                              current_price: float, portfolio_value: float) -> float:
        """计算仓位大小"""
        pass

class MomentumStrategy(Strategy):
    """动量策略"""
    
    def __init__(self, config: Dict = None):
        super().__init__("Momentum", config)
        self.lookback_period = self.config.get('lookback_period', 20)
        self.threshold = self.config.get('threshold', 0.02)
    
    async def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, SignalType]:
        """生成动量信号"""
        signals = {}
        
        for symbol, df in data.items():
            if df.empty or len(df) < self.lookback_period:
                signals[symbol] = SignalType.HOLD
                continue
            
            # 计算动量
            current_price = df['close'].iloc[-1]
            past_price = df['close'].iloc[-self.lookback_period]
            momentum = (current_price - past_price) / past_price
            
            # 生成信号
            if momentum > self.threshold:
                signals[symbol] = SignalType.BUY
            elif momentum < -self.threshold:
                signals[symbol] = SignalType.SELL
            else:
                signals[symbol] = SignalType.HOLD
        
        return signals
    
    def calculate_position_size(self, symbol: str, signal: SignalType, 
                              current_price: float, portfolio_value: float) -> float:
        """计算仓位大小"""
        if signal == SignalType.HOLD:
            return 0.0
        
        # 固定仓位比例
        position_ratio = self.config.get('position_ratio', 0.1)
        return portfolio_value * position_ratio / current_price

class MeanReversionStrategy(Strategy):
    """均值回归策略"""
    
    def __init__(self, config: Dict = None):
        super().__init__("MeanReversion", config)
        self.lookback_period = self.config.get('lookback_period', 20)
        self.bb_period = self.config.get('bb_period', 20)
        self.bb_std = self.config.get('bb_std', 2)
        self.rsi_period = self.config.get('rsi_period', 14)
        self.rsi_oversold = self.config.get('rsi_oversold', 30)
        self.rsi_overbought = self.config.get('rsi_overbought', 70)
    
    async def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, SignalType]:
        """生成均值回归信号"""
        signals = {}
        
        for symbol, df in data.items():
            if df.empty or len(df) < max(self.lookback_period, self.bb_period, self.rsi_period):
                signals[symbol] = SignalType.HOLD
                continue
            
            # 计算技术指标
            df_with_indicators = indicators_calculator.calculate_all_indicators(df)
            
            current_price = df_with_indicators['close'].iloc[-1]
            bb_upper = df_with_indicators['BB_Upper'].iloc[-1]
            bb_lower = df_with_indicators['BB_Lower'].iloc[-1]
            bb_middle = df_with_indicators['BB_Middle'].iloc[-1]
            rsi = df_with_indicators['RSI_14'].iloc[-1]
            
            # 生成信号
            if (current_price <= bb_lower and rsi <= self.rsi_oversold):
                signals[symbol] = SignalType.BUY
            elif (current_price >= bb_upper and rsi >= self.rsi_overbought):
                signals[symbol] = SignalType.SELL
            else:
                signals[symbol] = SignalType.HOLD
        
        return signals
    
    def calculate_position_size(self, symbol: str, signal: SignalType, 
                              current_price: float, portfolio_value: float) -> float:
        """计算仓位大小"""
        if signal == SignalType.HOLD:
            return 0.0
        
        # 基于波动率的仓位大小
        position_ratio = self.config.get('position_ratio', 0.1)
        return portfolio_value * position_ratio / current_price

class AIEnhancedStrategy(Strategy):
    """AI增强策略"""
    
    def __init__(self, config: Dict = None):
        super().__init__("AIEnhanced", config)
        self.ai_manager = None
        self._init_ai_manager()
    
    def _init_ai_manager(self):
        """初始化AI管理器"""
        try:
            self.ai_manager = create_ai_strategy_manager()
        except Exception as e:
            logger.error(f"AI管理器初始化失败: {e}")
    
    async def generate_signals(self, data: Dict[str, pd.DataFrame]) -> Dict[str, SignalType]:
        """生成AI增强信号"""
        signals = {}
        
        if not self.ai_manager:
            logger.warning("AI管理器未初始化，使用默认信号")
            return {symbol: SignalType.HOLD for symbol in data.keys()}
        
        for symbol, df in data.items():
            try:
                # 使用AI生成信号
                ai_signal = await self.ai_manager.get_consensus_signal(symbol, df)
                
                # 转换为策略信号
                if ai_signal.signal_type.value == "buy":
                    signals[symbol] = SignalType.BUY
                elif ai_signal.signal_type.value == "sell":
                    signals[symbol] = SignalType.SELL
                else:
                    signals[symbol] = SignalType.HOLD
                    
            except Exception as e:
                logger.error(f"AI信号生成失败 {symbol}: {e}")
                signals[symbol] = SignalType.HOLD
        
        return signals
    
    def calculate_position_size(self, symbol: str, signal: SignalType, 
                              current_price: float, portfolio_value: float) -> float:
        """计算仓位大小"""
        if signal == SignalType.HOLD:
            return 0.0
        
        # 基于AI置信度的仓位大小
        base_ratio = self.config.get('position_ratio', 0.1)
        # 这里可以根据AI置信度调整仓位大小
        return portfolio_value * base_ratio / current_price

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.initial_capital = config.initial_capital
        self.current_capital = config.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_returns = []
        self.equity_curve = []
        self.dates = []
        
    async def run_backtest(self, strategy: Strategy, symbols: List[str]) -> BacktestResults:
        """运行回测"""
        logger.info(f"开始回测: {strategy.name}")
        logger.info(f"回测期间: {self.config.start_date} 到 {self.config.end_date}")
        logger.info(f"初始资金: {self.initial_capital:,.2f}")
        logger.info(f"标的股票: {symbols}")
        
        # 获取数据
        data = await self._get_backtest_data(symbols)
        if not data:
            logger.error("无法获取回测数据")
            return self._create_empty_results()
        
        # 获取基准数据
        benchmark_data = await self._get_benchmark_data()
        
        # 生成交易日期
        trading_dates = self._generate_trading_dates(data)
        
        # 运行回测
        for date in trading_dates:
            await self._process_trading_day(date, strategy, data, symbols)
        
        # 计算结果
        results = self._calculate_results(benchmark_data)
        
        logger.info(f"回测完成: 总收益率 {results.total_return:.2%}")
        return results
    
    async def _get_backtest_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        """获取回测数据"""
        data = {}
        
        for symbol in symbols:
            try:
                # 根据股票代码选择数据源
                if symbol.endswith('.SZ') or symbol.endswith('.SH') or symbol.startswith('00') or symbol.startswith('60'):
                    source = DataSource.AKSHARE
                else:
                    source = DataSource.YFINANCE
                
                df = await data_manager.get_stock_data(
                    symbol=symbol,
                    start_date=self.config.start_date,
                    end_date=self.config.end_date,
                    source=source
                )
                
                if not df.empty:
                    # 计算技术指标
                    df_with_indicators = indicators_calculator.calculate_all_indicators(df)
                    data[symbol] = df_with_indicators
                else:
                    logger.warning(f"无法获取 {symbol} 的数据")
                    
            except Exception as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")
        
        return data
    
    async def _get_benchmark_data(self) -> pd.DataFrame:
        """获取基准数据"""
        try:
            # 根据基准股票代码选择数据源
            if self.config.benchmark.endswith('.SZ') or self.config.benchmark.endswith('.SH') or self.config.benchmark.startswith('00') or self.config.benchmark.startswith('60'):
                benchmark_source = DataSource.AKSHARE
            else:
                benchmark_source = DataSource.YFINANCE
            
            benchmark_df = await data_manager.get_stock_data(
                symbol=self.config.benchmark,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                source=benchmark_source
            )
            return benchmark_df
        except Exception as e:
            logger.error(f"获取基准数据失败: {e}")
            return pd.DataFrame()
    
    def _generate_trading_dates(self, data: Dict[str, pd.DataFrame]) -> List[datetime]:
        """生成交易日期"""
        all_dates = set()
        
        for df in data.values():
            if not df.empty and 'date' in df.columns:
                all_dates.update(pd.to_datetime(df['date']).dt.date)
        
        return sorted(list(all_dates))
    
    async def _process_trading_day(self, date: datetime, strategy: Strategy, 
                                 data: Dict[str, pd.DataFrame], symbols: List[str]):
        """处理单个交易日"""
        # 获取当日数据
        current_data = {}
        for symbol in symbols:
            if symbol in data:
                df = data[symbol]
                # 过滤当日数据
                day_data = df[df['date'].dt.date == date]
                if not day_data.empty:
                    current_data[symbol] = day_data
        
        if not current_data:
            return
        
        # 生成交易信号
        signals = await strategy.generate_signals(current_data)
        
        # 执行交易
        await self._execute_trades(date, signals, current_data, strategy)
        
        # 更新持仓和资金
        self._update_positions_and_capital(current_data)
        
        # 记录每日收益
        self._record_daily_return(date)
    
    async def _execute_trades(self, date: datetime, signals: Dict[str, SignalType], 
                            data: Dict[str, pd.DataFrame], strategy: Strategy):
        """执行交易"""
        for symbol, signal in signals.items():
            if symbol not in data:
                continue
            
            current_price = data[symbol]['close'].iloc[-1]
            portfolio_value = self._get_portfolio_value(data)
            
            # 计算目标仓位
            target_quantity = strategy.calculate_position_size(
                symbol, signal, current_price, portfolio_value
            )
            
            # 获取当前仓位
            current_quantity = self.positions.get(symbol, 0)
            quantity_change = target_quantity - current_quantity
            
            # 执行交易
            if abs(quantity_change) > 1e-6:  # 避免浮点数精度问题
                await self._place_order(symbol, quantity_change, current_price, date)
    
    async def _place_order(self, symbol: str, quantity: float, price: float, date: datetime):
        """下单"""
        if abs(quantity) < 1e-6:
            return
        
        # 计算佣金和滑点
        commission = abs(quantity) * price * self.config.commission_rate
        slippage = abs(quantity) * price * self.config.slippage_rate
        
        # 调整价格
        if quantity > 0:  # 买入
            adjusted_price = price * (1 + self.config.slippage_rate)
        else:  # 卖出
            adjusted_price = price * (1 - self.config.slippage_rate)
        
        # 创建交易记录
        trade = Trade(
            symbol=symbol,
            side=SignalType.BUY if quantity > 0 else SignalType.SELL,
            quantity=abs(quantity),
            price=adjusted_price,
            timestamp=date,
            commission=commission,
            slippage=slippage,
            trade_id=f"{symbol}_{date.strftime('%Y%m%d_%H%M%S')}"
        )
        
        self.trades.append(trade)
        
        # 更新持仓
        if symbol not in self.positions:
            self.positions[symbol] = 0
        
        self.positions[symbol] += quantity
        
        # 更新资金
        total_cost = abs(quantity) * adjusted_price + commission
        if quantity > 0:  # 买入
            self.current_capital -= total_cost
        else:  # 卖出
            self.current_capital += total_cost
    
    def _get_portfolio_value(self, data: Dict[str, pd.DataFrame]) -> float:
        """获取投资组合总价值"""
        total_value = self.current_capital
        
        for symbol, quantity in self.positions.items():
            if symbol in data and quantity > 0:
                current_price = data[symbol]['close'].iloc[-1]
                total_value += quantity * current_price
        
        return total_value
    
    def _update_positions_and_capital(self, data: Dict[str, pd.DataFrame]):
        """更新持仓和资金"""
        # 这里可以添加更复杂的持仓管理逻辑
        pass
    
    def _record_daily_return(self, date: datetime):
        """记录每日收益"""
        current_value = self._get_portfolio_value({})
        daily_return = (current_value - self.initial_capital) / self.initial_capital
        
        self.daily_returns.append(daily_return)
        self.equity_curve.append(current_value)
        self.dates.append(date)
    
    def _calculate_results(self, benchmark_data: pd.DataFrame) -> BacktestResults:
        """计算回测结果"""
        if not self.daily_returns:
            return self._create_empty_results()
        
        returns_series = pd.Series(self.daily_returns, index=self.dates)
        equity_series = pd.Series(self.equity_curve, index=self.dates)
        
        # 计算基本指标
        total_return = (equity_series.iloc[-1] - self.initial_capital) / self.initial_capital
        annual_return = (1 + total_return) ** (252 / len(returns_series)) - 1
        volatility = returns_series.std() * np.sqrt(252)
        sharpe_ratio = (annual_return - self.config.risk_free_rate) / volatility if volatility > 0 else 0
        
        # 计算最大回撤
        cumulative = (1 + returns_series).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        max_drawdown = drawdown.min()
        
        # 计算其他指标
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 计算胜率
        winning_trades = [t for t in self.trades if t.side == SignalType.BUY and 
                         any(t2.symbol == t.symbol and t2.side == SignalType.SELL and 
                             t2.timestamp > t.timestamp for t2 in self.trades)]
        win_rate = len(winning_trades) / len(self.trades) if self.trades else 0
        
        # 计算盈利因子
        gross_profit = sum(t.quantity * t.price for t in self.trades if t.side == SignalType.SELL)
        gross_loss = sum(t.quantity * t.price for t in self.trades if t.side == SignalType.BUY)
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # 基准收益
        benchmark_returns = pd.Series()
        if not benchmark_data.empty and 'close' in benchmark_data.columns:
            benchmark_prices = benchmark_data.set_index('date')['close']
            benchmark_returns = benchmark_prices.pct_change().dropna()
        
        return BacktestResults(
            total_return=total_return,
            annual_return=annual_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            calmar_ratio=calmar_ratio,
            win_rate=win_rate,
            profit_factor=profit_factor,
            trades=self.trades,
            positions=self.positions,
            daily_returns=returns_series,
            equity_curve=equity_series,
            benchmark_returns=benchmark_returns
        )
    
    def _create_empty_results(self) -> BacktestResults:
        """创建空结果"""
        return BacktestResults(
            total_return=0.0,
            annual_return=0.0,
            volatility=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            calmar_ratio=0.0,
            win_rate=0.0,
            profit_factor=0.0
        )

# 便捷函数
async def run_backtest(strategy_name: str, symbols: List[str], 
                      config: BacktestConfig = None) -> BacktestResults:
    """运行回测的便捷函数"""
    if config is None:
        config = BacktestConfig()
    
    # 创建策略
    if strategy_name == "momentum":
        strategy = MomentumStrategy()
    elif strategy_name == "mean_reversion":
        strategy = MeanReversionStrategy()
    elif strategy_name == "ai_enhanced":
        strategy = AIEnhancedStrategy()
    else:
        raise ValueError(f"不支持的策略: {strategy_name}")
    
    # 创建回测引擎
    engine = BacktestEngine(config)
    
    # 运行回测
    return await engine.run_backtest(strategy, symbols)

def create_backtest_config(**kwargs) -> BacktestConfig:
    """创建回测配置的便捷函数"""
    return BacktestConfig(**kwargs)
