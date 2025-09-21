"""
技术指标模块测试
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from technical_indicators import TechnicalIndicators, IndicatorType, IndicatorConfig

class TestTechnicalIndicators(unittest.TestCase):
    """技术指标测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.indicators = TechnicalIndicators()
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        np.random.seed(42)
        
        # 生成模拟价格数据
        base_price = 100
        returns = np.random.normal(0, 0.02, 100)
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        self.test_data = pd.DataFrame({
            'date': dates,
            'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 100)
        })
        
        # 确保high >= low
        self.test_data['high'] = np.maximum(self.test_data['high'], self.test_data['low'])
        self.test_data['high'] = np.maximum(self.test_data['high'], self.test_data['close'])
        self.test_data['low'] = np.minimum(self.test_data['low'], self.test_data['close'])
    
    def test_indicators_config_initialization(self):
        """测试指标配置初始化"""
        configs = self.indicators.indicators_config
        
        # 检查关键指标是否存在
        self.assertIn('SMA', configs)
        self.assertIn('EMA', configs)
        self.assertIn('RSI', configs)
        self.assertIn('MACD', configs)
        self.assertIn('BBANDS', configs)
        
        # 检查配置类型
        self.assertEqual(configs['SMA'].indicator_type, IndicatorType.TREND)
        self.assertEqual(configs['RSI'].indicator_type, IndicatorType.MOMENTUM)
        self.assertEqual(configs['BBANDS'].indicator_type, IndicatorType.VOLATILITY)
    
    def test_calculate_all_indicators(self):
        """测试计算所有指标"""
        result = self.indicators.calculate_all_indicators(self.test_data)
        
        # 验证结果不为空
        self.assertFalse(result.empty)
        
        # 验证原始数据保留
        self.assertIn('open', result.columns)
        self.assertIn('high', result.columns)
        self.assertIn('low', result.columns)
        self.assertIn('close', result.columns)
        self.assertIn('volume', result.columns)
        
        # 验证添加了技术指标
        self.assertIn('SMA_20', result.columns)
        self.assertIn('EMA_12', result.columns)
        self.assertIn('RSI_14', result.columns)
        self.assertIn('MACD', result.columns)
        self.assertIn('BB_Upper', result.columns)
    
    def test_calculate_single_indicator_sma(self):
        """测试计算单个SMA指标"""
        sma = self.indicators.calculate_single_indicator(
            self.test_data, 'SMA', period=20
        )
        
        # 验证结果
        self.assertFalse(sma.empty)
        self.assertEqual(len(sma), len(self.test_data))
        
        # 验证SMA值在合理范围内
        self.assertTrue(sma.iloc[-1] > 0)
        self.assertTrue(sma.iloc[-1] < 200)  # 假设价格在合理范围内
    
    def test_calculate_single_indicator_rsi(self):
        """测试计算单个RSI指标"""
        rsi = self.indicators.calculate_single_indicator(
            self.test_data, 'RSI', period=14
        )
        
        # 验证结果
        self.assertFalse(rsi.empty)
        self.assertEqual(len(rsi), len(self.test_data))
        
        # 验证RSI值在0-100范围内
        valid_rsi = rsi.dropna()
        if not valid_rsi.empty:
            self.assertTrue(valid_rsi.min() >= 0)
            self.assertTrue(valid_rsi.max() <= 100)
    
    def test_calculate_single_indicator_macd(self):
        """测试计算单个MACD指标"""
        macd = self.indicators.calculate_single_indicator(
            self.test_data, 'MACD', fast=12, slow=26, signal=9
        )
        
        # 验证结果
        self.assertFalse(macd.empty)
        self.assertEqual(len(macd), len(self.test_data))
    
    def test_calculate_single_indicator_bbands(self):
        """测试计算布林带指标"""
        bbands = self.indicators.calculate_single_indicator(
            self.test_data, 'BBANDS', period=20, std=2
        )
        
        # 验证结果
        self.assertFalse(bbands.empty)
        self.assertIn('upper', bbands.columns)
        self.assertIn('middle', bbands.columns)
        self.assertIn('lower', bbands.columns)
        
        # 验证布林带关系
        if not bbands.empty:
            self.assertTrue((bbands['upper'] >= bbands['middle']).all())
            self.assertTrue((bbands['middle'] >= bbands['lower']).all())
    
    def test_get_support_resistance_levels(self):
        """测试获取支撑阻力位"""
        levels = self.indicators.get_support_resistance_levels(self.test_data, window=20)
        
        # 验证结果结构
        self.assertIn('resistance', levels)
        self.assertIn('support', levels)
        
        # 验证数据类型
        self.assertIsInstance(levels['resistance'], list)
        self.assertIsInstance(levels['support'], list)
        
        # 验证数值合理性
        for level in levels['resistance']:
            self.assertIsInstance(level, (int, float))
            self.assertTrue(level > 0)
        
        for level in levels['support']:
            self.assertIsInstance(level, (int, float))
            self.assertTrue(level > 0)
    
    def test_detect_patterns(self):
        """测试检测技术形态"""
        patterns = self.indicators.detect_patterns(self.test_data)
        
        # 验证结果结构
        self.assertIsInstance(patterns, dict)
        
        # 验证关键形态
        expected_patterns = ['doji', 'hammer', 'hanging_man', 'engulfing', 'harami']
        for pattern in expected_patterns:
            self.assertIn(pattern, patterns)
            self.assertIsInstance(patterns[pattern], list)
    
    def test_empty_data_handling(self):
        """测试空数据处理"""
        empty_data = pd.DataFrame()
        result = self.indicators.calculate_all_indicators(empty_data)
        
        # 验证返回空DataFrame
        self.assertTrue(result.empty)
    
    def test_insufficient_data_handling(self):
        """测试数据不足处理"""
        # 创建只有5行数据的DataFrame
        short_data = self.test_data.head(5)
        result = self.indicators.calculate_all_indicators(short_data)
        
        # 验证结果不为空（应该返回原始数据）
        self.assertFalse(result.empty)
        self.assertEqual(len(result), 5)
    
    def test_calculate_kdj(self):
        """测试KDJ指标计算"""
        result = self.indicators._calculate_kdj(self.test_data)
        
        # 验证结果
        self.assertFalse(result.empty)
        self.assertIn('KDJ_K', result.columns)
        self.assertIn('KDJ_D', result.columns)
        self.assertIn('KDJ_J', result.columns)
        
        # 验证KDJ值在合理范围内
        k_values = result['KDJ_K'].dropna()
        d_values = result['KDJ_D'].dropna()
        j_values = result['KDJ_J'].dropna()
        
        if not k_values.empty:
            self.assertTrue(k_values.min() >= 0)
            self.assertTrue(k_values.max() <= 100)
        
        if not d_values.empty:
            self.assertTrue(d_values.min() >= 0)
            self.assertTrue(d_values.max() <= 100)
        
        if not j_values.empty:
            # J值可以超出0-100范围
            self.assertTrue(j_values.min() >= -50)  # 允许一定的负值
            self.assertTrue(j_values.max() <= 150)  # 允许一定的超出

if __name__ == '__main__':
    unittest.main()
