"""
数据获取模块测试
"""
import unittest
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_acquisition import DataAcquisitionManager, DataSource, DataConfig

class TestDataAcquisitionManager(unittest.TestCase):
    """数据获取管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = DataConfig(
            primary_source=DataSource.YFINANCE,
            fallback_sources=[DataSource.AKSHARE, DataSource.TUSHARE],
            cache_duration=60,
            max_retries=2,
            timeout=10
        )
        self.data_manager = DataAcquisitionManager(self.config)
    
    def test_config_initialization(self):
        """测试配置初始化"""
        self.assertEqual(self.data_manager.config.primary_source, DataSource.YFINANCE)
        self.assertEqual(len(self.data_manager.config.fallback_sources), 2)
        self.assertEqual(self.data_manager.config.cache_duration, 60)
    
    def test_cache_validation(self):
        """测试缓存验证"""
        # 测试空缓存
        self.assertFalse(self.data_manager._is_cache_valid("test_key"))
        
        # 添加缓存
        test_data = pd.DataFrame({'test': [1, 2, 3]})
        self.data_manager._update_cache("test_key", test_data)
        
        # 测试有效缓存
        self.assertTrue(self.data_manager._is_cache_valid("test_key"))
        
        # 测试过期缓存
        self.data_manager.last_update["test_key"] = datetime.now() - timedelta(seconds=120)
        self.assertFalse(self.data_manager._is_cache_valid("test_key"))
    
    @patch('yfinance.Ticker')
    def test_fetch_from_yfinance(self, mock_ticker):
        """测试从yfinance获取数据"""
        # 模拟yfinance返回数据
        mock_data = pd.DataFrame({
            'Open': [100, 101, 102],
            'High': [105, 106, 107],
            'Low': [95, 96, 97],
            'Close': [102, 103, 104],
            'Volume': [1000000, 1100000, 1200000]
        })
        mock_data.index = pd.date_range('2023-01-01', periods=3)
        
        mock_ticker_instance = Mock()
        mock_ticker_instance.history.return_value = mock_data
        mock_ticker.return_value = mock_ticker_instance
        
        # 运行测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                self.data_manager._fetch_from_yfinance(
                    "AAPL", "2023-01-01", "2023-01-03", "1d"
                )
            )
            
            # 验证结果
            self.assertFalse(result.empty)
            self.assertEqual(len(result), 3)
            self.assertIn('symbol', result.columns)
            self.assertIn('date', result.columns)
            self.assertIn('open', result.columns)
            self.assertIn('close', result.columns)
            
        finally:
            loop.close()
    
    def test_get_market_data(self):
        """测试批量获取市场数据"""
        # 模拟数据获取
        with patch.object(self.data_manager, 'get_stock_data') as mock_get_stock:
            mock_data = pd.DataFrame({
                'date': pd.date_range('2023-01-01', periods=3),
                'open': [100, 101, 102],
                'high': [105, 106, 107],
                'low': [95, 96, 97],
                'close': [102, 103, 104],
                'volume': [1000000, 1100000, 1200000]
            })
            mock_get_stock.return_value = mock_data
            
            # 运行测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.data_manager.get_market_data(
                        ["AAPL", "MSFT"], "2023-01-01", "2023-01-03"
                    )
                )
                
                # 验证结果
                self.assertIn("AAPL", result)
                self.assertIn("MSFT", result)
                self.assertEqual(len(result["AAPL"]), 3)
                self.assertEqual(len(result["MSFT"]), 3)
                
            finally:
                loop.close()
    
    def test_get_realtime_data(self):
        """测试获取实时数据"""
        # 模拟yfinance实时数据
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.info = {
                'currentPrice': 150.0,
                'regularMarketChange': 2.5,
                'regularMarketChangePercent': 0.0167,
                'volume': 5000000,
                'marketCap': 2500000000000
            }
            mock_ticker.return_value = mock_ticker_instance
            
            # 运行测试
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.data_manager.get_realtime_data(["AAPL"])
                )
                
                # 验证结果
                self.assertIn("AAPL", result)
                self.assertEqual(result["AAPL"]["price"], 150.0)
                self.assertEqual(result["AAPL"]["change"], 2.5)
                
            finally:
                loop.close()
    
    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效股票代码
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker_instance = Mock()
            mock_ticker_instance.history.side_effect = Exception("Invalid symbol")
            mock_ticker.return_value = mock_ticker_instance
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    self.data_manager._fetch_from_yfinance(
                        "INVALID", "2023-01-01", "2023-01-03", "1d"
                    )
                )
                
                # 验证返回空DataFrame
                self.assertTrue(result.empty)
                
            finally:
                loop.close()

if __name__ == '__main__':
    unittest.main()
