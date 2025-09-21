"""
回测引擎模块测试
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backtest_engine import (
    BacktestEngine, BacktestConfig, BacktestResults,
    MomentumStrategy, MeanReversionStrategy, AIEnhancedStrategy,
    SignalType, OrderType, Trade, Position
)

class TestBacktestConfig(unittest.TestCase):
    """回测配置测试类"""
    
    def test_default_config(self):
        """测试默认配置"""
        config = BacktestConfig()
        
        self.assertEqual(config.initial_capital, 1000000.0)
        self.assertEqual(config.start_date, "2023-01-01")
        self.assertEqual(config.end_date, "2024-01-01")
        self.assertEqual(config.commission_rate, 0.001)
        self.assertEqual(config.slippage_rate, 0.0005)
        self.assertEqual(config.max_position_size, 0.1)
        self.assertEqual(config.max_total_position, 0.95)
        self.assertEqual(config.benchmark, "SPY")
        self.assertEqual(config.risk_free_rate, 0.02)
    
    def test_custom_config(self):
        """测试自定义配置"""
        config = BacktestConfig(
            initial_capital=500000.0,
            start_date="2022-01-01",
            end_date="2023-01-01",
            commission_rate=0.002,
            benchmark="QQQ"
        )
        
        self.assertEqual(config.initial_capital, 500000.0)
        self.assertEqual(config.start_date, "2022-01-01")
        self.assertEqual(config.end_date, "2023-01-01")
        self.assertEqual(config.commission_rate, 0.002)
        self.assertEqual(config.benchmark, "QQQ")

class TestMomentumStrategy(unittest.TestCase):
    """动量策略测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.strategy = MomentumStrategy({
            'lookback_period': 10,
            'threshold': 0.05,
            'position_ratio': 0.2
        })
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=20, freq='D')
        prices = [100 + i * 2 for i in range(20)]  # 上升趋势
        
        self.test_data = {
            'AAPL': pd.DataFrame({
                'date': dates,
                'close': prices,
                'open': [p - 1 for p in prices],
                'high': [p + 2 for p in prices],
                'low': [p - 2 for p in prices],
                'volume': [1000000] * 20
            })
        }
    
    def test_strategy_initialization(self):
        """测试策略初始化"""
        self.assertEqual(self.strategy.name, "Momentum")
        self.assertEqual(self.strategy.lookback_period, 10)
        self.assertEqual(self.strategy.threshold, 0.05)
    
    def test_generate_signals(self):
        """测试生成信号"""
        import asyncio
        
        async def run_test():
            signals = await self.strategy.generate_signals(self.test_data)
            
            # 验证信号生成
            self.assertIn('AAPL', signals)
            self.assertIsInstance(signals['AAPL'], SignalType)
            
            # 由于是上升趋势，应该生成买入信号
            self.assertEqual(signals['AAPL'], SignalType.BUY)
        
        asyncio.run(run_test())
    
    def test_calculate_position_size(self):
        """测试计算仓位大小"""
        position_size = self.strategy.calculate_position_size(
            'AAPL', SignalType.BUY, 120.0, 100000.0
        )
        
        # 验证仓位计算
        expected_size = 100000.0 * 0.2 / 120.0
        self.assertAlmostEqual(position_size, expected_size, places=2)
    
    def test_calculate_position_size_hold(self):
        """测试持有信号的仓位大小"""
        position_size = self.strategy.calculate_position_size(
            'AAPL', SignalType.HOLD, 120.0, 100000.0
        )
        
        # 持有信号应该返回0
        self.assertEqual(position_size, 0.0)

class TestMeanReversionStrategy(unittest.TestCase):
    """均值回归策略测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.strategy = MeanReversionStrategy({
            'lookback_period': 10,
            'bb_period': 20,
            'bb_std': 2,
            'rsi_period': 14,
            'rsi_oversold': 30,
            'rsi_overbought': 70,
            'position_ratio': 0.15
        })
        
        # 创建测试数据（包含技术指标）
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        prices = [100] * 30  # 横盘整理
        
        self.test_data = {
            'AAPL': pd.DataFrame({
                'date': dates,
                'close': prices,
                'open': [p - 0.5 for p in prices],
                'high': [p + 1 for p in prices],
                'low': [p - 1 for p in prices],
                'volume': [1000000] * 30,
                'BB_Upper': [102] * 30,
                'BB_Lower': [98] * 30,
                'BB_Middle': [100] * 30,
                'RSI_14': [50] * 30
            })
        }
    
    def test_strategy_initialization(self):
        """测试策略初始化"""
        self.assertEqual(self.strategy.name, "MeanReversion")
        self.assertEqual(self.strategy.lookback_period, 10)
        self.assertEqual(self.strategy.bb_period, 20)
        self.assertEqual(self.strategy.rsi_period, 14)
    
    def test_generate_signals(self):
        """测试生成信号"""
        import asyncio
        
        async def run_test():
            signals = await self.strategy.generate_signals(self.test_data)
            
            # 验证信号生成
            self.assertIn('AAPL', signals)
            self.assertIsInstance(signals['AAPL'], SignalType)
        
        asyncio.run(run_test())

class TestBacktestEngine(unittest.TestCase):
    """回测引擎测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = BacktestConfig(
            initial_capital=100000.0,
            start_date="2023-01-01",
            end_date="2023-01-31"
        )
        self.engine = BacktestEngine(self.config)
        self.strategy = MomentumStrategy()
    
    def test_engine_initialization(self):
        """测试引擎初始化"""
        self.assertEqual(self.engine.initial_capital, 100000.0)
        self.assertEqual(self.engine.current_capital, 100000.0)
        self.assertEqual(len(self.engine.positions), 0)
        self.assertEqual(len(self.engine.trades), 0)
    
    def test_place_order(self):
        """测试下单"""
        import asyncio
        
        async def run_test():
            # 测试买入订单
            await self.engine._place_order('AAPL', 100, 120.0, datetime.now())
            
            # 验证交易记录
            self.assertEqual(len(self.engine.trades), 1)
            trade = self.engine.trades[0]
            self.assertEqual(trade.symbol, 'AAPL')
            self.assertEqual(trade.quantity, 100)
            self.assertEqual(trade.price, 120.0)
            self.assertEqual(trade.side, SignalType.BUY)
            
            # 验证资金变化
            expected_cost = 100 * 120.0 * (1 + self.config.commission_rate + self.config.slippage_rate)
            expected_capital = 100000.0 - expected_cost
            self.assertAlmostEqual(self.engine.current_capital, expected_capital, places=2)
        
        asyncio.run(run_test())
    
    def test_place_order_sell(self):
        """测试卖出订单"""
        import asyncio
        
        async def run_test():
            # 先买入
            await self.engine._place_order('AAPL', 100, 120.0, datetime.now())
            initial_capital = self.engine.current_capital
            
            # 再卖出
            await self.engine._place_order('AAPL', -50, 130.0, datetime.now())
            
            # 验证交易记录
            self.assertEqual(len(self.engine.trades), 2)
            
            # 验证资金变化（应该增加）
            self.assertGreater(self.engine.current_capital, initial_capital)
        
        asyncio.run(run_test())
    
    def test_get_portfolio_value(self):
        """测试获取投资组合价值"""
        # 添加持仓
        self.engine.positions['AAPL'] = 100
        self.engine.current_capital = 50000.0
        
        # 创建测试数据
        test_data = {
            'AAPL': pd.DataFrame({
                'close': [120.0]
            })
        }
        
        portfolio_value = self.engine._get_portfolio_value(test_data)
        
        # 验证投资组合价值
        expected_value = 50000.0 + 100 * 120.0
        self.assertEqual(portfolio_value, expected_value)
    
    def test_calculate_results(self):
        """测试计算结果"""
        # 模拟一些交易和收益数据
        self.engine.trades = [
            Trade('AAPL', SignalType.BUY, 100, 120.0, datetime.now()),
            Trade('AAPL', SignalType.SELL, 100, 130.0, datetime.now())
        ]
        
        self.engine.daily_returns = [0.01, 0.02, -0.01, 0.03]
        self.engine.equity_curve = [100000, 101000, 103020, 101989, 105049]
        self.engine.dates = pd.date_range('2023-01-01', periods=5)
        
        # 创建空的基准数据
        benchmark_data = pd.DataFrame()
        
        results = self.engine._calculate_results(benchmark_data)
        
        # 验证结果
        self.assertIsInstance(results, BacktestResults)
        self.assertGreater(results.total_return, 0)  # 应该有正收益
        self.assertGreater(results.sharpe_ratio, 0)  # 夏普比率应该为正

class TestBacktestResults(unittest.TestCase):
    """回测结果测试类"""
    
    def test_results_initialization(self):
        """测试结果初始化"""
        results = BacktestResults(
            total_return=0.15,
            annual_return=0.12,
            volatility=0.20,
            sharpe_ratio=0.6,
            max_drawdown=-0.08,
            calmar_ratio=1.5,
            win_rate=0.6,
            profit_factor=1.2
        )
        
        self.assertEqual(results.total_return, 0.15)
        self.assertEqual(results.annual_return, 0.12)
        self.assertEqual(results.volatility, 0.20)
        self.assertEqual(results.sharpe_ratio, 0.6)
        self.assertEqual(results.max_drawdown, -0.08)
        self.assertEqual(results.calmar_ratio, 1.5)
        self.assertEqual(results.win_rate, 0.6)
        self.assertEqual(results.profit_factor, 1.2)

if __name__ == '__main__':
    unittest.main()
