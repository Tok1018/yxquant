# 量化交易AI系统

一个基于AI的智能量化交易分析系统，集成了多种AI模型（GPT、DeepSeek、Gemini、Qwen、Grok等），提供技术分析、策略优化、风险管理和交易信号生成等功能。

## 🚀 主要特性

### AI集成功能
- **多模型支持**: 支持GPT-4、DeepSeek、Gemini、Qwen、Grok等多种AI模型
- **智能回退**: 自动在多个AI模型间切换，确保服务可用性
- **配置管理**: 灵活的AI模型配置和参数调整
- **使用统计**: 详细的API使用统计和成本跟踪

### 量化分析功能
- **技术指标**: MACD、CCI、KDJ、BOLL、RSI、均线等完整技术指标
- **头部底部识别**: 基于AI的智能头部底部概率分析
- **多策略支持**: 动量策略、均值回归策略、突破策略等
- **AI增强策略**: 结合传统技术分析和AI智能分析

### 风险管理
- **目标波动率管理**: 基于目标波动率的仓位控制
- **日内回撤熔断**: 实时监控和风险控制
- **仓位上限控制**: 单股和总仓位限制
- **AI风险预警**: 智能风险识别和预警

### 回测系统
- **多级回退数据源**: yfinance、akshare、tushare等
- **成本与滑点**: 真实交易成本模拟
- **秒级动量策略**: 支持高频交易策略
- **AI策略优化**: 基于AI的参数优化建议

### 数据管理
- **SQLite数据库**: 轻量级本地数据存储
- **自选股管理**: 灵活的投资组合管理
- **历史数据**: 完整的K线和技术指标历史
- **实时更新**: 自动数据更新和同步

## 📁 项目结构

```
yxquant/
├── config.py                 # 配置文件
├── database.py               # 数据库管理
├── ai_integration.py         # AI集成模块
├── ai_enhanced_strategies.py # AI增强策略
├── ai_config_manager.py      # AI配置管理
├── ai_api.py                 # AI Web API
├── requirements.txt          # 依赖包
├── README.md                 # 项目说明
├── data/                     # 数据目录
│   └── quant.db             # SQLite数据库
└── logs/                     # 日志目录
```

## 🛠️ 安装和配置

### 1. 环境要求
- Python 3.8+
- SQLite 3
- 至少4GB内存

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置AI模型
编辑 `ai_config.json` 文件，添加您的API密钥：

```json
{
  "models": {
    "gpt4": {
      "enabled": true,
      "api_key": "your-openai-api-key",
      "base_url": "https://api.openai.com/v1",
      "model_name": "gpt-4"
    },
    "deepseek": {
      "enabled": true,
      "api_key": "your-deepseek-api-key",
      "base_url": "https://api.deepseek.com/v1",
      "model_name": "deepseek-chat"
    },
    "gemini": {
      "enabled": true,
      "api_key": "your-gemini-api-key",
      "model_name": "gemini-pro"
    }
  }
}
```

### 4. 初始化数据库
```python
from database import db_manager
# 数据库会自动初始化
```

## 🚀 快速开始

### 1. 启动Web API服务
```bash
python ai_api.py
```
服务将在 http://localhost:8000 启动

### 2. 添加自选股
```python
from database import db_manager

# 添加股票信息
db_manager.add_stock("AAPL", "苹果公司", "科技", "NASDAQ")

# 添加到自选股
db_manager.add_to_watchlist("AAPL", "看好苹果长期发展")
```

### 3. 获取AI分析
```python
import asyncio
from ai_enhanced_strategies import create_ai_strategy_manager

async def analyze_stock():
    strategy_manager = create_ai_strategy_manager()
    
    # 获取交易信号
    signals = await strategy_manager.get_consensus_signal("AAPL", data)
    print(f"交易信号: {signals.signal_type.value}")
    print(f"置信度: {signals.confidence}")
    print(f"目标价: {signals.target_price}")
    print(f"止损价: {signals.stop_loss}")

asyncio.run(analyze_stock())
```

## 📊 API接口

### 股票分析
```bash
# 获取市场情绪分析
POST /ai/analyze/stock
{
  "symbol": "AAPL",
  "analysis_type": "sentiment",
  "data_period": 30
}

# 获取交易信号
POST /ai/strategies/signals
{
  "symbol": "AAPL",
  "use_consensus": true
}
```

### 策略管理
```bash
# 获取策略列表
GET /ai/strategies/list

# 启用/禁用策略
POST /ai/strategies/{strategy_name}/enable
POST /ai/strategies/{strategy_name}/disable

# 更新策略参数
POST /ai/strategies/{strategy_name}/parameters
{
  "lookback_period": 20,
  "threshold": 0.02
}
```

### 风险分析
```bash
# 风险分析
POST /ai/risk/analyze
{
  "portfolio_data": {
    "positions": [...],
    "total_value": 1000000
  }
}
```

## 🔧 配置说明

### AI模型配置
- **GPT-4**: 最强大的分析能力，适合复杂分析
- **DeepSeek**: 性价比高，响应速度快
- **Gemini**: Google的AI模型，分析准确
- **Qwen**: 阿里云模型，中文理解好
- **Grok**: X.AI模型，实时信息强

### 策略参数
- **动量策略**: 基于价格动量和成交量
- **均值回归**: 基于布林带和RSI指标
- **突破策略**: 基于支撑阻力位突破

### 风控参数
- **最大仓位**: 单股最大仓位比例
- **目标波动率**: 投资组合目标波动率
- **日内回撤限制**: 最大日内回撤比例

## 📈 使用示例

### 1. 批量分析自选股
```python
import asyncio
from database import db_manager
from ai_enhanced_strategies import create_ai_strategy_manager

async def batch_analysis():
    strategy_manager = create_ai_strategy_manager()
    watchlist = db_manager.get_watchlist()
    
    for _, stock in watchlist.iterrows():
        symbol = stock['symbol']
        data = db_manager.get_kline_data(symbol)
        
        if not data.empty:
            signal = await strategy_manager.get_consensus_signal(symbol, data)
            print(f"{symbol}: {signal.signal_type.value} (置信度: {signal.confidence:.2f})")

asyncio.run(batch_analysis())
```

### 2. 策略回测
```python
from backtest import BacktestEngine

# 创建回测引擎
backtest = BacktestEngine(
    initial_capital=1000000,
    start_date="2023-01-01",
    end_date="2024-01-01"
)

# 运行回测
results = backtest.run_strategy("AI_Momentum", ["AAPL", "MSFT", "GOOGL"])
print(f"总收益率: {results['total_return']:.2%}")
print(f"夏普比率: {results['sharpe_ratio']:.2f}")
```

## 🔍 监控和日志

### 日志文件
- 系统日志: `logs/system.log`
- AI使用日志: `logs/ai_usage.log`
- 交易日志: `logs/trading.log`

### 监控指标
- AI模型响应时间
- API调用成功率
- 策略信号准确率
- 风险指标监控

## 🚨 风险提示

1. **投资风险**: 本系统仅供学习和研究使用，不构成投资建议
2. **数据风险**: 历史数据不代表未来表现
3. **技术风险**: AI模型可能存在误判，请谨慎使用
4. **成本风险**: AI API调用可能产生费用

## 📝 开发计划

### 已完成 ✅
- [x] 项目架构设计
- [x] SQLite数据库设计
- [x] AI集成模块（多模型支持）
- [x] AI增强策略系统
- [x] AI配置管理系统
- [x] AI Web API接口
- [x] 风险管理基础框架

### 进行中 🚧
- [ ] 数据获取模块（多级回退）
- [ ] 技术指标计算模块
- [ ] 自选股管理界面
- [ ] 回测系统完善
- [ ] 可视化界面

### 未来计划 📋
- [ ] 实时数据流处理
- [ ] 机器学习模型集成
- [ ] 移动端应用
- [ ] 云端部署支持
- [ ] 更多技术指标
- [ ] 期权策略支持
- [ ] 加密货币支持

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork本项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License

## 📞 联系方式

如有问题或建议，请通过以下方式联系：
- 提交Issue
- 发送邮件
- 微信群讨论

---

**免责声明**: 本系统仅供学习和研究使用，不构成任何投资建议。使用本系统进行实际交易的风险由用户自行承担。
