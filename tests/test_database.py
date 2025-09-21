"""
数据库模块测试
"""
import unittest
import tempfile
import os
import pandas as pd
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database import DatabaseManager

class TestDatabaseManager(unittest.TestCase):
    """数据库管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时数据库文件
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 创建数据库管理器实例
        self.db_manager = DatabaseManager(self.temp_db.name)
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时数据库文件
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)
    
    def test_add_stock(self):
        """测试添加股票"""
        # 添加股票
        self.db_manager.add_stock("AAPL", "苹果公司", "科技", "NASDAQ")
        
        # 验证股票是否添加成功
        stocks = self.db_manager.get_all_stocks()
        self.assertEqual(len(stocks), 1)
        self.assertEqual(stocks.iloc[0]['symbol'], "AAPL")
        self.assertEqual(stocks.iloc[0]['name'], "苹果公司")
    
    def test_add_to_watchlist(self):
        """测试添加到自选股"""
        # 先添加股票
        self.db_manager.add_stock("AAPL", "苹果公司", "科技", "NASDAQ")
        
        # 添加到自选股
        self.db_manager.add_to_watchlist("AAPL", "看好苹果长期发展")
        
        # 验证自选股
        watchlist = self.db_manager.get_watchlist()
        self.assertEqual(len(watchlist), 1)
        self.assertEqual(watchlist.iloc[0]['symbol'], "AAPL")
    
    def test_add_kline_data(self):
        """测试添加K线数据"""
        # 添加股票
        self.db_manager.add_stock("AAPL", "苹果公司", "科技", "NASDAQ")
        
        # 添加K线数据
        test_date = datetime.now().date()
        self.db_manager.add_kline_data(
            symbol="AAPL",
            date=test_date,
            open_price=100.0,
            high_price=105.0,
            low_price=95.0,
            close_price=102.0,
            volume=1000000
        )
        
        # 验证K线数据
        kline_data = self.db_manager.get_kline_data("AAPL")
        self.assertEqual(len(kline_data), 1)
        self.assertEqual(kline_data.iloc[0]['close'], 102.0)
    
    def test_get_kline_data_with_date_range(self):
        """测试按日期范围获取K线数据"""
        # 添加股票
        self.db_manager.add_stock("AAPL", "苹果公司", "科技", "NASDAQ")
        
        # 添加多天K线数据
        base_date = datetime.now().date()
        for i in range(5):
            date = base_date - timedelta(days=i)
            self.db_manager.add_kline_data(
                symbol="AAPL",
                date=date,
                open_price=100.0 + i,
                high_price=105.0 + i,
                low_price=95.0 + i,
                close_price=102.0 + i,
                volume=1000000
            )
        
        # 获取最近3天的数据
        start_date = (base_date - timedelta(days=2)).strftime("%Y-%m-%d")
        end_date = base_date.strftime("%Y-%m-%d")
        
        kline_data = self.db_manager.get_kline_data("AAPL", start_date, end_date)
        self.assertEqual(len(kline_data), 3)
    
    def test_remove_from_watchlist(self):
        """测试从自选股移除"""
        # 先添加股票和自选股
        self.db_manager.add_stock("AAPL", "苹果公司", "科技", "NASDAQ")
        self.db_manager.add_to_watchlist("AAPL", "测试")
        
        # 验证添加成功
        watchlist = self.db_manager.get_watchlist()
        self.assertEqual(len(watchlist), 1)
        
        # 移除自选股
        self.db_manager.remove_from_watchlist("AAPL")
        
        # 验证移除成功
        watchlist = self.db_manager.get_watchlist()
        self.assertEqual(len(watchlist), 0)
    
    def test_add_ai_analysis(self):
        """测试添加AI分析结果"""
        # 添加股票
        self.db_manager.add_stock("AAPL", "苹果公司", "科技", "NASDAQ")
        
        # 添加AI分析结果
        analysis_data = {
            "signal_type": "buy",
            "confidence": 0.85,
            "target_price": 110.0,
            "stop_loss": 95.0,
            "reasoning": "技术指标显示看涨信号"
        }
        
        self.db_manager.add_ai_analysis("AAPL", analysis_data)
        
        # 验证AI分析结果
        analysis = self.db_manager.get_ai_analysis("AAPL")
        self.assertEqual(len(analysis), 1)
        self.assertEqual(analysis.iloc[0]['signal_type'], "buy")
        self.assertEqual(analysis.iloc[0]['confidence'], 0.85)
    
    def test_add_trade_record(self):
        """测试添加交易记录"""
        # 添加股票
        self.db_manager.add_stock("AAPL", "苹果公司", "科技", "NASDAQ")
        
        # 添加交易记录
        self.db_manager.add_trade_record(
            symbol="AAPL",
            side="buy",
            quantity=100,
            price=100.0,
            commission=1.0,
            timestamp=datetime.now()
        )
        
        # 验证交易记录
        trades = self.db_manager.get_trade_records("AAPL")
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades.iloc[0]['side'], "buy")
        self.assertEqual(trades.iloc[0]['quantity'], 100)

if __name__ == '__main__':
    unittest.main()
