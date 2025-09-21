# API 参考文档

## 概述

量化交易AI系统提供了丰富的API接口，支持股票分析、策略管理、回测、AI分析等功能。

## 基础信息

- **基础URL**: `http://localhost:8000`
- **API版本**: v1.0.0
- **内容类型**: `application/json`
- **字符编码**: UTF-8

## 认证

目前API不需要认证，但建议在生产环境中添加适当的认证机制。

## 通用响应格式

所有API响应都遵循以下格式：

```json
{
  "status": "success|error",
  "message": "操作结果描述",
  "data": {}, // 具体数据（可选）
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 错误处理

API使用标准HTTP状态码：

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

## API 端点

### 1. 自选股管理

#### 1.1 获取自选股列表

```http
GET /watchlist
```

**响应示例:**
```json
{
  "status": "success",
  "data": [
    {
      "symbol": "AAPL",
      "name": "苹果公司",
      "industry": "科技",
      "market": "NASDAQ",
      "added_at": "2024-01-01T00:00:00Z",
      "notes": "看好长期发展"
    }
  ]
}
```

#### 1.2 添加自选股

```http
POST /api/watchlist/add
```

**请求体:**
```json
{
  "symbol": "AAPL",
  "notes": "看好长期发展"
}
```

**响应示例:**
```json
{
  "status": "success",
  "message": "已添加 AAPL 到自选股"
}
```

#### 1.3 移除自选股

```http
DELETE /api/watchlist/{symbol}
```

**响应示例:**
```json
{
  "status": "success",
  "message": "已移除 AAPL 从自选股"
}
```

### 2. 策略管理

#### 2.1 获取策略列表

```http
GET /api/strategies
```

**响应示例:**
```json
{
  "status": "success",
  "strategies": [
    {
      "name": "momentum",
      "display_name": "动量策略",
      "description": "基于价格动量的趋势跟踪策略",
      "parameters": {
        "lookback_period": 20,
        "threshold": 0.02,
        "position_ratio": 0.1
      },
      "enabled": true
    }
  ]
}
```

#### 2.2 启用策略

```http
POST /api/strategies/{strategy_name}/enable
```

**响应示例:**
```json
{
  "status": "success",
  "message": "策略 momentum 已启用"
}
```

#### 2.3 禁用策略

```http
POST /api/strategies/{strategy_name}/disable
```

**响应示例:**
```json
{
  "status": "success",
  "message": "策略 momentum 已禁用"
}
```

### 3. 回测功能

#### 3.1 运行回测

```http
POST /api/backtest/run
```

**请求体:**
```json
{
  "strategy_name": "momentum",
  "symbols": ["AAPL", "MSFT"],
  "start_date": "2023-01-01",
  "end_date": "2024-01-01",
  "initial_capital": 1000000.0
}
```

**响应示例:**
```json
{
  "status": "success",
  "results": {
    "total_return": 0.15,
    "annual_return": 0.12,
    "volatility": 0.20,
    "sharpe_ratio": 0.6,
    "max_drawdown": -0.08,
    "calmar_ratio": 1.5,
    "win_rate": 0.6,
    "profit_factor": 1.2,
    "trades_count": 25,
    "equity_curve": {
      "2023-01-01": 1000000,
      "2023-01-02": 1005000
    },
    "daily_returns": {
      "2023-01-01": 0.005,
      "2023-01-02": 0.003
    }
  }
}
```

### 4. AI分析功能

#### 4.1 股票分析

```http
POST /api/analysis/stock
```

**请求体:**
```json
{
  "symbol": "AAPL",
  "analysis_type": "technical|sentiment|ai_signal",
  "data_period": 30
}
```

**响应示例:**
```json
{
  "status": "success",
  "analysis": {
    "symbol": "AAPL",
    "current_price": 150.0,
    "signals": {
      "rsi": "超买",
      "macd": "看涨",
      "bb": "区间震荡"
    },
    "indicators": {
      "rsi": 75.5,
      "macd": 2.3,
      "bb_position": 0.6
    }
  }
}
```

#### 4.2 市场情绪分析

```http
POST /ai/analyze/stock
```

**请求体:**
```json
{
  "symbol": "AAPL",
  "analysis_type": "sentiment",
  "data_period": 30
}
```

**响应示例:**
```json
{
  "status": "success",
  "analysis": {
    "symbol": "AAPL",
    "sentiment_score": 0.6,
    "sentiment_label": "中性偏乐观",
    "confidence": 0.75,
    "reasoning": "技术指标显示积极信号，但市场情绪保持谨慎"
  }
}
```

#### 4.3 获取交易信号

```http
POST /ai/strategies/signals
```

**请求体:**
```json
{
  "symbol": "AAPL",
  "use_consensus": true
}
```

**响应示例:**
```json
{
  "status": "success",
  "signal": {
    "symbol": "AAPL",
    "signal_type": "buy",
    "confidence": 0.85,
    "target_price": 160.0,
    "stop_loss": 140.0,
    "reasoning": "多个技术指标显示看涨信号，AI分析建议买入"
  }
}
```

### 5. 数据管理

#### 5.1 更新股票数据

```http
POST /api/data/update/{symbol}
```

**响应示例:**
```json
{
  "status": "success",
  "message": "已更新 AAPL 的数据"
}
```

#### 5.2 获取实时数据

```http
GET /api/data/realtime/{symbol}
```

**响应示例:**
```json
{
  "status": "success",
  "data": {
    "symbol": "AAPL",
    "price": 150.0,
    "change": 2.5,
    "change_percent": 0.0167,
    "volume": 5000000,
    "market_cap": 2500000000000,
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### 6. 系统监控

#### 6.1 获取系统状态

```http
GET /api/monitor/status
```

**响应示例:**
```json
{
  "status": "success",
  "data": {
    "ai_models": {
      "gpt4": true,
      "deepseek": true,
      "gemini": false
    },
    "database": "正常",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

#### 6.2 获取系统统计

```http
GET /api/monitor/stats
```

**响应示例:**
```json
{
  "status": "success",
  "data": {
    "watchlist_count": 10,
    "stocks_count": 100,
    "active_ai_models": 2,
    "total_requests": 1500,
    "uptime": "7天12小时30分钟"
  }
}
```

## 数据模型

### 股票信息 (Stock)

```json
{
  "symbol": "string",      // 股票代码
  "name": "string",        // 股票名称
  "industry": "string",    // 行业
  "market": "string",      // 市场
  "is_active": boolean,    // 是否活跃
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### 自选股 (WatchlistItem)

```json
{
  "id": "integer",
  "symbol": "string",
  "added_at": "datetime",
  "notes": "string"
}
```

### K线数据 (KlineData)

```json
{
  "symbol": "string",
  "date": "date",
  "open": "float",
  "high": "float",
  "low": "float",
  "close": "float",
  "volume": "integer"
}
```

### 交易记录 (Trade)

```json
{
  "symbol": "string",
  "side": "buy|sell",
  "quantity": "float",
  "price": "float",
  "timestamp": "datetime",
  "commission": "float",
  "slippage": "float"
}
```

### AI分析结果 (AIAnalysis)

```json
{
  "symbol": "string",
  "analysis_type": "string",
  "data": "object",
  "confidence": "float",
  "timestamp": "datetime"
}
```

## 错误代码

| 错误代码 | 描述 | 解决方案 |
|---------|------|----------|
| 1001 | 股票代码不存在 | 检查股票代码是否正确 |
| 1002 | 数据获取失败 | 检查数据源连接 |
| 1003 | AI模型不可用 | 检查AI配置和API密钥 |
| 1004 | 策略参数错误 | 检查策略参数格式 |
| 1005 | 回测数据不足 | 确保有足够的历史数据 |
| 2001 | 数据库连接失败 | 检查数据库配置 |
| 2002 | 文件操作失败 | 检查文件权限 |
| 3001 | 网络请求超时 | 检查网络连接 |
| 3002 | API调用限制 | 等待后重试 |

## 使用示例

### Python 示例

```python
import requests
import json

# 基础URL
base_url = "http://localhost:8000"

# 添加自选股
def add_to_watchlist(symbol, notes):
    url = f"{base_url}/api/watchlist/add"
    data = {"symbol": symbol, "notes": notes}
    response = requests.post(url, json=data)
    return response.json()

# 运行回测
def run_backtest(strategy, symbols, start_date, end_date):
    url = f"{base_url}/api/backtest/run"
    data = {
        "strategy_name": strategy,
        "symbols": symbols,
        "start_date": start_date,
        "end_date": end_date,
        "initial_capital": 1000000.0
    }
    response = requests.post(url, json=data)
    return response.json()

# 获取AI分析
def analyze_stock(symbol, analysis_type):
    url = f"{base_url}/api/analysis/stock"
    data = {
        "symbol": symbol,
        "analysis_type": analysis_type,
        "data_period": 30
    }
    response = requests.post(url, json=data)
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 添加自选股
    result = add_to_watchlist("AAPL", "看好苹果长期发展")
    print("添加自选股:", result)
    
    # 运行回测
    backtest_result = run_backtest(
        "momentum", 
        ["AAPL", "MSFT"], 
        "2023-01-01", 
        "2024-01-01"
    )
    print("回测结果:", backtest_result)
    
    # 获取技术分析
    analysis = analyze_stock("AAPL", "technical")
    print("技术分析:", analysis)
```

### JavaScript 示例

```javascript
// 基础URL
const baseUrl = 'http://localhost:8000';

// 添加自选股
async function addToWatchlist(symbol, notes) {
    const response = await fetch(`${baseUrl}/api/watchlist/add`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            symbol: symbol,
            notes: notes
        })
    });
    return await response.json();
}

// 运行回测
async function runBacktest(strategy, symbols, startDate, endDate) {
    const response = await fetch(`${baseUrl}/api/backtest/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            strategy_name: strategy,
            symbols: symbols,
            start_date: startDate,
            end_date: endDate,
            initial_capital: 1000000.0
        })
    });
    return await response.json();
}

// 获取AI分析
async function analyzeStock(symbol, analysisType) {
    const response = await fetch(`${baseUrl}/api/analysis/stock`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            symbol: symbol,
            analysis_type: analysisType,
            data_period: 30
        })
    });
    return await response.json();
}

// 使用示例
async function main() {
    try {
        // 添加自选股
        const addResult = await addToWatchlist('AAPL', '看好苹果长期发展');
        console.log('添加自选股:', addResult);
        
        // 运行回测
        const backtestResult = await runBacktest(
            'momentum',
            ['AAPL', 'MSFT'],
            '2023-01-01',
            '2024-01-01'
        );
        console.log('回测结果:', backtestResult);
        
        // 获取技术分析
        const analysis = await analyzeStock('AAPL', 'technical');
        console.log('技术分析:', analysis);
        
    } catch (error) {
        console.error('请求失败:', error);
    }
}

main();
```

## 限制和注意事项

1. **API调用频率**: 建议每秒不超过10次请求
2. **数据更新**: 股票数据每小时更新一次
3. **回测限制**: 单次回测最多支持100只股票
4. **AI分析**: 需要配置有效的API密钥
5. **数据存储**: 历史数据保留1年

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 支持基本的股票分析功能
- 支持多种AI模型集成
- 支持策略回测功能
- 支持Web管理界面

## 支持

如有问题或建议，请通过以下方式联系：

- 提交Issue: [GitHub Issues](https://github.com/your-repo/issues)
- 发送邮件: support@example.com
- 微信群: 扫描二维码加入讨论群

---

**免责声明**: 本API仅供学习和研究使用，不构成投资建议。使用本API进行实际交易的风险由用户自行承担。
