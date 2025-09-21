"""
AI量化交易系统演示脚本
展示AI集成的各种功能
"""
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入系统模块
from database import db_manager
from ai_integration import ai_manager, QuantAIAnalyzer
from ai_enhanced_strategies import create_ai_strategy_manager
from ai_config_manager import ai_config_manager

def create_sample_data():
    """创建示例数据"""
    logger.info("创建示例数据...")
    
    # 添加示例股票
    stocks = [
        ("AAPL", "苹果公司", "科技", "NASDAQ"),
        ("MSFT", "微软", "科技", "NASDAQ"),
        ("GOOGL", "谷歌", "科技", "NASDAQ"),
        ("TSLA", "特斯拉", "汽车", "NASDAQ"),
        ("NVDA", "英伟达", "半导体", "NASDAQ")
    ]
    
    for symbol, name, industry, market in stocks:
        db_manager.add_stock(symbol, name, industry, market)
        db_manager.add_to_watchlist(symbol, f"示例股票 - {name}")
    
    # 创建示例K线数据
    for symbol, _, _, _ in stocks:
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
        np.random.seed(hash(symbol) % 2**32)  # 确保每个股票的数据不同
        
        # 生成随机价格数据
        base_price = 100 + hash(symbol) % 200
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = [base_price]
        
        for ret in returns[1:]:
            prices.append(prices[-1] * (1 + ret))
        
        # 生成OHLCV数据
        data = pd.DataFrame({
            'date': dates,
            'open': [p * (1 + np.random.normal(0, 0.005)) for p in prices],
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        })
        
        # 确保OHLC逻辑正确
        data['high'] = data[['open', 'high', 'close']].max(axis=1)
        data['low'] = data[['open', 'low', 'close']].min(axis=1)
        
        # 保存数据
        db_manager.save_kline_data(symbol, data)
        logger.info(f"创建 {symbol} 的示例数据: {len(data)} 条记录")

async def demo_ai_analysis():
    """演示AI分析功能"""
    logger.info("开始AI分析演示...")
    
    # 创建AI分析器
    quant_ai = QuantAIAnalyzer(ai_manager)
    
    # 获取自选股列表
    watchlist = db_manager.get_watchlist()
    logger.info(f"自选股列表: {list(watchlist['symbol'])}")
    
    for _, stock in watchlist.iterrows():
        symbol = stock['symbol']
        logger.info(f"\n分析股票: {symbol} ({stock['name']})")
        
        # 获取K线数据
        data = db_manager.get_kline_data(symbol)
        if data.empty:
            logger.warning(f"没有 {symbol} 的数据")
            continue
        
        try:
            # 1. 市场情绪分析
            logger.info("1. 市场情绪分析...")
            sentiment = await quant_ai.analyze_market_sentiment(symbol)
            logger.info(f"   情绪分析结果: {sentiment}")
            
            # 2. 交易信号生成
            logger.info("2. 交易信号生成...")
            signals = await quant_ai.generate_trading_signals(symbol, data.tail(20))
            logger.info(f"   交易信号: {signals}")
            
            # 3. 风险分析
            logger.info("3. 风险分析...")
            portfolio_data = {
                "symbol": symbol,
                "current_price": data['close'].iloc[-1],
                "volatility": data['close'].pct_change().std() * np.sqrt(252),
                "data_points": len(data)
            }
            risk = await quant_ai.generate_risk_warning(portfolio_data)
            logger.info(f"   风险分析: {risk}")
            
        except Exception as e:
            logger.error(f"分析 {symbol} 时出错: {e}")

async def demo_ai_strategies():
    """演示AI增强策略"""
    logger.info("\n开始AI策略演示...")
    
    # 创建策略管理器
    strategy_manager = create_ai_strategy_manager()
    
    # 获取自选股
    watchlist = db_manager.get_watchlist()
    
    for _, stock in watchlist.iterrows():
        symbol = stock['symbol']
        logger.info(f"\n策略分析: {symbol}")
        
        # 获取数据
        data = db_manager.get_kline_data(symbol)
        if data.empty:
            continue
        
        try:
            # 1. 单个策略分析
            logger.info("1. 单个策略分析...")
            momentum_signal = await strategy_manager.analyze_symbol(symbol, data, ["momentum"])
            if momentum_signal:
                signal = momentum_signal["momentum"]
                logger.info(f"   动量策略: {signal.signal_type.value} (置信度: {signal.confidence:.2f})")
                logger.info(f"   推理: {signal.reasoning}")
            
            # 2. 共识信号
            logger.info("2. 共识信号分析...")
            consensus = await strategy_manager.get_consensus_signal(symbol, data)
            logger.info(f"   共识信号: {consensus.signal_type.value} (置信度: {consensus.confidence:.2f})")
            logger.info(f"   目标价: {consensus.target_price:.2f}")
            logger.info(f"   止损价: {consensus.stop_loss:.2f}")
            logger.info(f"   推理: {consensus.reasoning}")
            
        except Exception as e:
            logger.error(f"策略分析 {symbol} 时出错: {e}")

async def demo_strategy_optimization():
    """演示策略优化"""
    logger.info("\n开始策略优化演示...")
    
    quant_ai = QuantAIAnalyzer(ai_manager)
    
    # 模拟回测结果
    backtest_results = {
        "strategy_name": "AI_Momentum",
        "total_return": 0.15,
        "annual_return": 0.12,
        "max_drawdown": 0.08,
        "sharpe_ratio": 1.2,
        "win_rate": 0.65,
        "total_trades": 150,
        "avg_trade_return": 0.02,
        "volatility": 0.18
    }
    
    try:
        logger.info("策略优化分析...")
        optimization = await quant_ai.optimize_strategy_parameters("AI_Momentum", backtest_results)
        logger.info(f"优化建议: {optimization}")
        
    except Exception as e:
        logger.error(f"策略优化时出错: {e}")

def demo_database_operations():
    """演示数据库操作"""
    logger.info("\n开始数据库操作演示...")
    
    # 1. 查看自选股
    watchlist = db_manager.get_watchlist()
    logger.info(f"自选股数量: {len(watchlist)}")
    logger.info("自选股列表:")
    for _, stock in watchlist.iterrows():
        logger.info(f"  {stock['symbol']}: {stock['name']} ({stock['industry']})")
    
    # 2. 查看交易记录
    trades = db_manager.get_trades()
    logger.info(f"交易记录数量: {len(trades)}")
    
    # 3. 查看AI分析历史
    ai_analysis = db_manager.get_ai_analysis()
    logger.info(f"AI分析记录数量: {len(ai_analysis)}")
    
    # 4. 查看使用统计
    usage_stats = db_manager.get_ai_usage_stats()
    logger.info(f"AI使用统计记录数量: {len(usage_stats)}")

def demo_ai_config():
    """演示AI配置管理"""
    logger.info("\n开始AI配置演示...")
    
    # 1. 查看模型状态
    model_status = ai_config_manager.get_model_status()
    logger.info("AI模型状态:")
    for model, status in model_status.items():
        logger.info(f"  {model}: 启用={status['enabled']}, API密钥={status['has_api_key']}")
    
    # 2. 查看配置
    config = ai_config_manager.config
    logger.info(f"回退链: {config['fallback_chain']}")
    logger.info(f"功能配置: {config['features']}")

async def main():
    """主演示函数"""
    logger.info("=" * 60)
    logger.info("AI量化交易系统演示")
    logger.info("=" * 60)
    
    try:
        # 1. 创建示例数据
        create_sample_data()
        
        # 2. 演示数据库操作
        demo_database_operations()
        
        # 3. 演示AI配置
        demo_ai_config()
        
        # 4. 演示AI分析（需要配置API密钥）
        logger.info("\n注意: AI分析功能需要配置有效的API密钥")
        logger.info("请在 ai_config.json 中配置您的API密钥")
        
        # 检查是否有可用的AI模型
        health_status = await ai_manager.health_check_all()
        available_models = [model for model, status in health_status.items() if status]
        
        if available_models:
            logger.info(f"发现可用AI模型: {available_models}")
            
            # 5. AI分析演示
            await demo_ai_analysis()
            
            # 6. AI策略演示
            await demo_ai_strategies()
            
            # 7. 策略优化演示
            await demo_strategy_optimization()
        else:
            logger.warning("没有可用的AI模型，跳过AI分析演示")
            logger.info("请配置API密钥后重新运行演示")
        
        logger.info("\n" + "=" * 60)
        logger.info("演示完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"演示过程中出错: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
