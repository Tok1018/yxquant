"""
AI集成模块测试
"""
import unittest
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ai_integration import (
    AIManager, AIModelType, AIModelConfig, 
    AIAnalysisResult, SignalType as AISignalType
)

class TestAIModelConfig(unittest.TestCase):
    """AI模型配置测试类"""
    
    def test_config_initialization(self):
        """测试配置初始化"""
        config = AIModelConfig(
            model_type=AIModelType.GPT_4,
            api_key="test_key",
            base_url="https://api.openai.com/v1",
            model_name="gpt-4",
            temperature=0.7,
            max_tokens=2000,
            timeout=30,
            retry_count=3,
            priority=1
        )
        
        self.assertEqual(config.model_type, AIModelType.GPT_4)
        self.assertEqual(config.api_key, "test_key")
        self.assertEqual(config.base_url, "https://api.openai.com/v1")
        self.assertEqual(config.model_name, "gpt-4")
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.max_tokens, 2000)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.retry_count, 3)
        self.assertEqual(config.priority, 1)

class TestAIManager(unittest.TestCase):
    """AI管理器测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.ai_manager = AIManager()
        
        # 创建测试数据
        dates = pd.date_range('2023-01-01', periods=20, freq='D')
        prices = [100 + i * 2 for i in range(20)]
        
        self.test_data = pd.DataFrame({
            'date': dates,
            'open': [p - 1 for p in prices],
            'high': [p + 2 for p in prices],
            'low': [p - 2 for p in prices],
            'close': prices,
            'volume': [1000000] * 20
        })
    
    def test_manager_initialization(self):
        """测试管理器初始化"""
        self.assertIsInstance(self.ai_manager.models, dict)
        self.assertIsInstance(self.ai_manager.usage_stats, dict)
        self.assertIsNone(self.ai_manager.active_provider)
    
    def test_add_model(self):
        """测试添加模型"""
        config = AIModelConfig(
            model_type=AIModelType.GPT_4,
            api_key="test_key",
            model_name="gpt-4"
        )
        
        self.ai_manager.add_model("gpt4", config)
        
        # 验证模型已添加
        self.assertIn("gpt4", self.ai_manager.models)
        self.assertEqual(self.ai_manager.models["gpt4"], config)
    
    def test_set_active_provider(self):
        """测试设置活跃提供商"""
        # 先添加模型
        config = AIModelConfig(
            model_type=AIModelType.GPT_4,
            api_key="test_key",
            model_name="gpt-4"
        )
        self.ai_manager.add_model("gpt4", config)
        
        # 设置活跃提供商
        self.ai_manager.set_active_provider("gpt4")
        
        # 验证设置成功
        self.assertEqual(self.ai_manager.active_provider, "gpt4")
    
    def test_set_active_provider_invalid(self):
        """测试设置无效的活跃提供商"""
        with self.assertRaises(ValueError):
            self.ai_manager.set_active_provider("invalid_model")
    
    @patch('openai.OpenAI')
    def test_analyze_market_sentiment(self, mock_openai):
        """测试市场情绪分析"""
        # 模拟OpenAI响应
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"sentiment": "positive", "confidence": 0.8, "reasoning": "市场表现良好"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 添加模型配置
        config = AIModelConfig(
            model_type=AIModelType.GPT_4,
            api_key="test_key",
            model_name="gpt-4"
        )
        self.ai_manager.add_model("gpt4", config)
        self.ai_manager.set_active_provider("gpt4")
        
        # 运行测试
        async def run_test():
            result = await self.ai_manager.analyze_market_sentiment(
                "AAPL", self.test_data, 30
            )
            
            # 验证结果
            self.assertIsInstance(result, AIAnalysisResult)
            self.assertEqual(result.analysis_type, "market_sentiment")
            self.assertIn("sentiment", result.data)
            self.assertIn("confidence", result.data)
        
        asyncio.run(run_test())
    
    @patch('openai.OpenAI')
    def test_generate_trading_signal(self, mock_openai):
        """测试生成交易信号"""
        # 模拟OpenAI响应
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"signal": "buy", "confidence": 0.75, "target_price": 110.0, "stop_loss": 95.0, "reasoning": "技术指标显示看涨"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 添加模型配置
        config = AIModelConfig(
            model_type=AIModelType.GPT_4,
            api_key="test_key",
            model_name="gpt-4"
        )
        self.ai_manager.add_model("gpt4", config)
        self.ai_manager.set_active_provider("gpt4")
        
        # 运行测试
        async def run_test():
            result = await self.ai_manager.generate_trading_signal(
                "AAPL", self.test_data
            )
            
            # 验证结果
            self.assertIsInstance(result, AIAnalysisResult)
            self.assertEqual(result.analysis_type, "trading_signal")
            self.assertIn("signal", result.data)
            self.assertIn("confidence", result.data)
            self.assertIn("target_price", result.data)
        
        asyncio.run(run_test())
    
    @patch('openai.OpenAI')
    def test_optimize_strategy_parameters(self, mock_openai):
        """测试优化策略参数"""
        # 模拟OpenAI响应
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"optimized_parameters": {"lookback_period": 25, "threshold": 0.03}, "expected_improvement": 0.15, "reasoning": "基于历史数据优化"}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # 添加模型配置
        config = AIModelConfig(
            model_type=AIModelType.GPT_4,
            api_key="test_key",
            model_name="gpt-4"
        )
        self.ai_manager.add_model("gpt4", config)
        self.ai_manager.set_active_provider("gpt4")
        
        # 运行测试
        async def run_test():
            result = await self.ai_manager.optimize_strategy_parameters(
                "momentum", {"lookback_period": 20, "threshold": 0.02}, self.test_data
            )
            
            # 验证结果
            self.assertIsInstance(result, AIAnalysisResult)
            self.assertEqual(result.analysis_type, "strategy_optimization")
            self.assertIn("optimized_parameters", result.data)
            self.assertIn("expected_improvement", result.data)
        
        asyncio.run(run_test())
    
    def test_health_check(self):
        """测试健康检查"""
        # 添加模型配置
        config = AIModelConfig(
            model_type=AIModelType.GPT_4,
            api_key="test_key",
            model_name="gpt-4"
        )
        self.ai_manager.add_model("gpt4", config)
        
        # 运行健康检查
        async def run_test():
            health_status = await self.ai_manager.health_check("gpt4")
            
            # 验证结果（由于没有真实的API密钥，应该返回False）
            self.assertIsInstance(health_status, bool)
        
        asyncio.run(run_test())
    
    def test_health_check_all(self):
        """测试所有模型健康检查"""
        # 添加多个模型配置
        config1 = AIModelConfig(
            model_type=AIModelType.GPT_4,
            api_key="test_key1",
            model_name="gpt-4"
        )
        config2 = AIModelConfig(
            model_type=AIModelType.DEEPSEEK,
            api_key="test_key2",
            model_name="deepseek-chat"
        )
        
        self.ai_manager.add_model("gpt4", config1)
        self.ai_manager.add_model("deepseek", config2)
        
        # 运行健康检查
        async def run_test():
            health_status = await self.ai_manager.health_check_all()
            
            # 验证结果
            self.assertIsInstance(health_status, dict)
            self.assertIn("gpt4", health_status)
            self.assertIn("deepseek", health_status)
            self.assertIsInstance(health_status["gpt4"], bool)
            self.assertIsInstance(health_status["deepseek"], bool)
        
        asyncio.run(run_test())
    
    def test_get_usage_stats(self):
        """测试获取使用统计"""
        # 添加一些使用统计
        self.ai_manager.usage_stats["gpt4"] = {
            "total_requests": 100,
            "total_tokens": 50000,
            "total_cost": 25.0,
            "last_used": datetime.now()
        }
        
        stats = self.ai_manager.get_usage_stats()
        
        # 验证结果
        self.assertIsInstance(stats, dict)
        self.assertIn("gpt4", stats)
        self.assertEqual(stats["gpt4"]["total_requests"], 100)
        self.assertEqual(stats["gpt4"]["total_tokens"], 50000)
        self.assertEqual(stats["gpt4"]["total_cost"], 25.0)
    
    def test_get_usage_stats_by_provider(self):
        """测试获取特定提供商的使用统计"""
        # 添加使用统计
        self.ai_manager.usage_stats["gpt4"] = {
            "total_requests": 100,
            "total_tokens": 50000,
            "total_cost": 25.0,
            "last_used": datetime.now()
        }
        
        stats = self.ai_manager.get_usage_stats("gpt4")
        
        # 验证结果
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["total_requests"], 100)
        self.assertEqual(stats["total_tokens"], 50000)
        self.assertEqual(stats["total_cost"], 25.0)
    
    def test_get_usage_stats_invalid_provider(self):
        """测试获取无效提供商的使用统计"""
        stats = self.ai_manager.get_usage_stats("invalid_provider")
        
        # 验证结果
        self.assertIsNone(stats)

if __name__ == '__main__':
    unittest.main()
