# 开发者指南

## 目录

1. [项目架构](#项目架构)
2. [开发环境搭建](#开发环境搭建)
3. [代码结构](#代码结构)
4. [开发规范](#开发规范)
5. [扩展开发](#扩展开发)
6. [调试和测试](#调试和测试)
7. [部署指南](#部署指南)

## 项目架构

### 整体架构

```
yxquant/
├── core/                    # 核心模块
│   ├── database.py         # 数据库管理
│   ├── data_acquisition.py # 数据获取
│   ├── technical_indicators.py # 技术指标
│   └── backtest_engine.py  # 回测引擎
├── ai/                     # AI集成模块
│   ├── ai_integration.py   # AI集成
│   ├── ai_enhanced_strategies.py # AI增强策略
│   └── ai_config_manager.py # AI配置管理
├── web/                    # Web界面
│   ├── web_interface.py    # Web API
│   ├── templates/          # HTML模板
│   └── static/            # 静态资源
├── visualization/          # 可视化
│   └── visualization.py    # 图表生成
├── tests/                 # 测试
│   ├── test_*.py          # 单元测试
│   └── run_tests.py       # 测试运行器
├── docs/                  # 文档
│   ├── API_REFERENCE.md   # API文档
│   ├── USER_GUIDE.md      # 用户指南
│   └── DEVELOPER_GUIDE.md # 开发者指南
└── config/                # 配置文件
    ├── config.py          # 基础配置
    └── ai_config.json     # AI配置
```

### 技术栈

- **后端**: Python 3.8+, FastAPI, SQLite
- **前端**: HTML5, CSS3, JavaScript, Bootstrap 5
- **AI集成**: OpenAI, DeepSeek, Gemini, Qwen, Grok
- **数据处理**: Pandas, NumPy, TA-Lib
- **可视化**: Plotly, Matplotlib
- **测试**: unittest, pytest
- **部署**: Docker, Docker Compose

## 开发环境搭建

### 1. 环境要求

- Python 3.8+
- Git
- 代码编辑器 (推荐 VS Code)
- 数据库管理工具 (可选)

### 2. 克隆项目

```bash
git clone https://github.com/your-repo/yxquant.git
cd yxquant
```

### 3. 创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 4. 安装依赖

```bash
# 安装开发依赖
pip install -r requirements.txt

# 安装开发工具
pip install -r requirements-dev.txt
```

### 5. 配置环境

```bash
# 复制配置文件
cp config.example.py config.py

# 编辑配置文件
# 设置数据库路径、API密钥等
```

### 6. 初始化数据库

```bash
python start.py
```

### 7. 运行测试

```bash
# 运行所有测试
python tests/run_tests.py

# 运行特定测试
python tests/run_tests.py --module test_database
```

## 代码结构

### 核心模块

#### database.py
数据库管理模块，提供数据持久化功能。

**主要类**:
- `DatabaseManager`: 数据库管理器
- `StockInfo`: 股票信息模型
- `KlineData`: K线数据模型

**主要方法**:
- `add_stock()`: 添加股票
- `get_kline_data()`: 获取K线数据
- `add_ai_analysis()`: 添加AI分析结果

#### data_acquisition.py
数据获取模块，支持多数据源回退。

**主要类**:
- `DataAcquisitionManager`: 数据获取管理器
- `DataSource`: 数据源枚举
- `DataConfig`: 数据配置

**主要方法**:
- `get_stock_data()`: 获取股票数据
- `get_market_data()`: 批量获取数据
- `get_realtime_data()`: 获取实时数据

#### technical_indicators.py
技术指标计算模块。

**主要类**:
- `TechnicalIndicators`: 技术指标计算器
- `IndicatorType`: 指标类型枚举
- `IndicatorConfig`: 指标配置

**主要方法**:
- `calculate_all_indicators()`: 计算所有指标
- `calculate_single_indicator()`: 计算单个指标
- `detect_patterns()`: 检测技术形态

#### backtest_engine.py
回测引擎模块。

**主要类**:
- `BacktestEngine`: 回测引擎
- `Strategy`: 策略基类
- `MomentumStrategy`: 动量策略
- `MeanReversionStrategy`: 均值回归策略
- `AIEnhancedStrategy`: AI增强策略

**主要方法**:
- `run_backtest()`: 运行回测
- `calculate_results()`: 计算结果
- `place_order()`: 下单

### AI模块

#### ai_integration.py
AI集成模块，支持多种AI模型。

**主要类**:
- `AIManager`: AI管理器
- `AIModelConfig`: AI模型配置
- `AIAnalysisResult`: AI分析结果

**主要方法**:
- `analyze_market_sentiment()`: 市场情绪分析
- `generate_trading_signal()`: 生成交易信号
- `optimize_strategy_parameters()`: 优化策略参数

#### ai_enhanced_strategies.py
AI增强策略模块。

**主要类**:
- `AIStrategyManager`: AI策略管理器
- `ConsensusSignal`: 共识信号
- `SignalType`: 信号类型

**主要方法**:
- `get_consensus_signal()`: 获取共识信号
- `analyze_market_conditions()`: 分析市场条件
- `optimize_parameters()`: 优化参数

### Web模块

#### web_interface.py
Web API接口模块。

**主要路由**:
- `/`: 主页
- `/watchlist`: 自选股管理
- `/strategies`: 策略管理
- `/backtest`: 回测功能
- `/analysis`: AI分析
- `/data`: 数据管理
- `/monitor`: 系统监控

**主要方法**:
- `add_to_watchlist()`: 添加自选股
- `run_backtest_api()`: 运行回测API
- `analyze_stock()`: 分析股票

### 可视化模块

#### visualization.py
图表生成模块。

**主要类**:
- `ChartGenerator`: 图表生成器

**主要方法**:
- `create_candlestick_chart()`: 创建K线图
- `create_technical_indicators_chart()`: 创建技术指标图
- `create_backtest_results_chart()`: 创建回测结果图

## 开发规范

### 1. 代码风格

#### Python代码规范
- 遵循PEP 8规范
- 使用4个空格缩进
- 行长度不超过88字符
- 使用有意义的变量名和函数名

#### 文档字符串
```python
def calculate_sma(data: pd.DataFrame, period: int) -> pd.Series:
    """
    计算简单移动平均线
    
    Args:
        data: 包含价格数据的DataFrame
        period: 移动平均周期
        
    Returns:
        移动平均线序列
        
    Raises:
        ValueError: 当period小于等于0时
    """
    pass
```

#### 类型注解
```python
from typing import Dict, List, Optional, Union

def process_data(
    symbols: List[str], 
    start_date: str, 
    end_date: str
) -> Dict[str, pd.DataFrame]:
    pass
```

### 2. 错误处理

#### 异常处理
```python
try:
    result = risky_operation()
except SpecificException as e:
    logger.error(f"操作失败: {e}")
    return None
except Exception as e:
    logger.error(f"未知错误: {e}")
    raise
```

#### 日志记录
```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.info("开始执行操作")
    try:
        # 操作代码
        logger.info("操作成功完成")
    except Exception as e:
        logger.error(f"操作失败: {e}")
        raise
```

### 3. 测试规范

#### 单元测试
```python
import unittest
from unittest.mock import Mock, patch

class TestDataAcquisition(unittest.TestCase):
    def setUp(self):
        """测试前准备"""
        self.manager = DataAcquisitionManager()
    
    def test_get_stock_data(self):
        """测试获取股票数据"""
        # 测试代码
        pass
    
    def tearDown(self):
        """测试后清理"""
        pass
```

#### 集成测试
```python
class TestIntegration(unittest.TestCase):
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 集成测试代码
        pass
```

### 4. 配置管理

#### 环境变量
```python
import os
from pathlib import Path

# 数据库路径
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/quant.db')

# API密钥
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
```

#### 配置文件
```python
import json

def load_config(config_file: str) -> dict:
    """加载配置文件"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)
```

## 扩展开发

### 1. 添加新的数据源

#### 创建数据源类
```python
class CustomDataSource:
    """自定义数据源"""
    
    def __init__(self, config: dict):
        self.config = config
    
    async def get_stock_data(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """获取股票数据"""
        # 实现数据获取逻辑
        pass
```

#### 集成到数据管理器
```python
class DataAcquisitionManager:
    def __init__(self):
        self.sources = {
            'custom': CustomDataSource(config)
        }
    
    async def _fetch_from_custom(self, symbol, start_date, end_date):
        """从自定义数据源获取数据"""
        return await self.sources['custom'].get_stock_data(
            symbol, start_date, end_date
        )
```

### 2. 添加新的技术指标

#### 实现指标计算
```python
def calculate_custom_indicator(
    data: pd.DataFrame, 
    period: int = 20
) -> pd.Series:
    """计算自定义指标"""
    # 实现指标计算逻辑
    return result
```

#### 注册到指标计算器
```python
class TechnicalIndicators:
    def __init__(self):
        self.indicators_config['CUSTOM'] = IndicatorConfig(
            "CUSTOM", 
            IndicatorType.MOMENTUM, 
            {"period": 20}, 
            "自定义指标"
        )
    
    def _calculate_custom_indicator(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算自定义指标"""
        data['CUSTOM'] = calculate_custom_indicator(data)
        return data
```

### 3. 添加新的策略

#### 实现策略类
```python
class CustomStrategy(Strategy):
    """自定义策略"""
    
    def __init__(self, config: Dict = None):
        super().__init__("Custom", config)
        self.param1 = self.config.get('param1', 10)
        self.param2 = self.config.get('param2', 0.5)
    
    async def generate_signals(
        self, 
        data: Dict[str, pd.DataFrame]
    ) -> Dict[str, SignalType]:
        """生成交易信号"""
        signals = {}
        for symbol, df in data.items():
            # 实现信号生成逻辑
            signals[symbol] = SignalType.BUY  # 或 SELL, HOLD
        return signals
    
    def calculate_position_size(
        self, 
        symbol: str, 
        signal: SignalType, 
        current_price: float, 
        portfolio_value: float
    ) -> float:
        """计算仓位大小"""
        # 实现仓位计算逻辑
        return 0.1 * portfolio_value / current_price
```

### 4. 添加新的AI模型

#### 实现AI模型类
```python
class CustomAIModel:
    """自定义AI模型"""
    
    def __init__(self, config: AIModelConfig):
        self.config = config
        self.client = self._init_client()
    
    def _init_client(self):
        """初始化客户端"""
        # 实现客户端初始化
        pass
    
    async def analyze(self, prompt: str) -> str:
        """分析文本"""
        # 实现AI分析逻辑
        pass
```

#### 集成到AI管理器
```python
class AIManager:
    def __init__(self):
        self.models = {}
        self._setup_custom_models()
    
    def _setup_custom_models(self):
        """设置自定义模型"""
        if 'custom' in self.config:
            config = AIModelConfig(**self.config['custom'])
            self.models['custom'] = CustomAIModel(config)
```

### 5. 添加新的Web API

#### 定义API路由
```python
@app.post("/api/custom/analyze")
async def custom_analyze(request: CustomRequest):
    """自定义分析API"""
    try:
        # 实现分析逻辑
        result = await custom_analysis_function(request.data)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"自定义分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

#### 定义请求模型
```python
from pydantic import BaseModel

class CustomRequest(BaseModel):
    data: Dict[str, Any]
    parameters: Optional[Dict[str, Any]] = None
```

## 调试和测试

### 1. 调试技巧

#### 使用调试器
```python
import pdb

def debug_function():
    # 设置断点
    pdb.set_trace()
    # 调试代码
    pass
```

#### 日志调试
```python
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG)

def debug_function():
    logger.debug("开始执行")
    # 调试代码
    logger.debug("执行完成")
```

#### 性能分析
```python
import cProfile
import pstats

def profile_function():
    """性能分析函数"""
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 要分析的代码
    your_function()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

### 2. 测试策略

#### 单元测试
```python
class TestCustomFunction(unittest.TestCase):
    def test_normal_case(self):
        """测试正常情况"""
        result = custom_function(input_data)
        self.assertEqual(result, expected_result)
    
    def test_edge_case(self):
        """测试边界情况"""
        result = custom_function(edge_case_input)
        self.assertIsNotNone(result)
    
    def test_error_case(self):
        """测试错误情况"""
        with self.assertRaises(ValueError):
            custom_function(invalid_input)
```

#### 集成测试
```python
class TestIntegration(unittest.TestCase):
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 准备数据
        data = prepare_test_data()
        
        # 2. 执行操作
        result = execute_workflow(data)
        
        # 3. 验证结果
        self.assertIsNotNone(result)
        self.assertTrue(result.success)
```

#### 性能测试
```python
import time

class TestPerformance(unittest.TestCase):
    def test_execution_time(self):
        """测试执行时间"""
        start_time = time.time()
        result = performance_critical_function()
        end_time = time.time()
        
        execution_time = end_time - start_time
        self.assertLess(execution_time, 1.0)  # 应该在1秒内完成
```

### 3. 测试运行

#### 运行所有测试
```bash
python tests/run_tests.py
```

#### 运行特定测试
```bash
python tests/run_tests.py --module test_database
```

#### 运行性能测试
```bash
python tests/run_tests.py --performance
```

## 部署指南

### 1. 本地部署

#### 开发环境
```bash
# 启动开发服务器
python web_interface.py

# 访问 http://localhost:8000
```

#### 生产环境
```bash
# 使用gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker web_interface:app

# 使用nginx反向代理
# 配置nginx.conf
```

### 2. Docker部署

#### 创建Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "web_interface.py"]
```

#### 创建docker-compose.yml
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    environment:
      - DATABASE_PATH=/app/data/quant.db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
```

#### 部署命令
```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 3. 云端部署

#### AWS部署
```bash
# 使用ECS
aws ecs create-service --cluster yxquant --service-name web

# 使用Lambda
serverless deploy
```

#### 阿里云部署
```bash
# 使用容器服务
aliyun ecs create-instance

# 使用函数计算
fun deploy
```

### 4. 监控和日志

#### 日志配置
```python
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """设置日志"""
    handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
```

#### 监控指标
```python
import psutil
import time

def get_system_metrics():
    """获取系统指标"""
    return {
        'cpu_percent': psutil.cpu_percent(),
        'memory_percent': psutil.virtual_memory().percent,
        'disk_percent': psutil.disk_usage('/').percent,
        'timestamp': time.time()
    }
```

## 贡献指南

### 1. 提交代码

#### 创建分支
```bash
git checkout -b feature/new-feature
```

#### 提交代码
```bash
git add .
git commit -m "feat: 添加新功能"
git push origin feature/new-feature
```

#### 创建Pull Request
1. 在GitHub上创建Pull Request
2. 填写详细的描述
3. 等待代码审查
4. 合并到主分支

### 2. 代码审查

#### 审查要点
- 代码质量和风格
- 测试覆盖率
- 文档完整性
- 性能影响
- 安全性

#### 审查流程
1. 自动检查（CI/CD）
2. 人工审查
3. 测试验证
4. 合并决策

### 3. 发布流程

#### 版本管理
```bash
# 更新版本号
git tag v1.0.0
git push origin v1.0.0

# 创建发布说明
# 更新CHANGELOG.md
```

#### 发布检查
- [ ] 所有测试通过
- [ ] 文档更新
- [ ] 版本号更新
- [ ] 发布说明完整

---

**注意**: 本指南会随着项目发展持续更新，请定期查看最新版本。
