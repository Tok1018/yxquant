"""
Web管理界面模块
提供自选股管理、策略配置、结果展示等功能
"""
from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import pandas as pd
import json
import logging
from datetime import datetime, timedelta
import asyncio
from pathlib import Path

from database import db_manager
from data_acquisition import data_manager
from technical_indicators import indicators_calculator
from backtest_engine import run_backtest, create_backtest_config, BacktestConfig
from ai_enhanced_strategies import create_ai_strategy_manager
from ai_integration import ai_manager
from strategy_config import strategy_config_manager, StrategyConfig, StrategyType, StrategyStatus, StrategyParameter
from risk_management import risk_manager, PortfolioRisk, RiskLevel, RiskType
from kline_chart import kline_chart_generator

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(title="量化交易AI系统", version="1.0.0")

# 设置模板和静态文件
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# 创建必要的目录
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)

# Pydantic模型
class StockInfo(BaseModel):
    symbol: str
    name: str
    industry: str
    market: str

class WatchlistItem(BaseModel):
    symbol: str
    notes: str

class StrategyConfig(BaseModel):
    name: str
    parameters: Dict[str, Any]
    enabled: bool = True

class BacktestRequest(BaseModel):
    strategy_name: str
    symbols: List[str]
    start_date: str
    end_date: str
    initial_capital: float = 1000000.0

class AnalysisRequest(BaseModel):
    symbol: str
    analysis_type: str
    data_period: int = 30

# 主页路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页"""
    try:
        # 获取系统统计信息
        stats = await get_system_stats()
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"主页加载失败: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

# 自选股管理
@app.get("/watchlist", response_class=HTMLResponse)
async def watchlist_page(request: Request):
    """自选股页面"""
    try:
        watchlist = db_manager.get_watchlist()
        return templates.TemplateResponse("watchlist.html", {
            "request": request,
            "watchlist": watchlist
        })
    except Exception as e:
        logger.error(f"自选股页面加载失败: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/api/watchlist")
async def get_watchlist():
    """获取自选股列表"""
    try:
        watchlist = db_manager.get_watchlist()
        return {"status": "success", "watchlist": watchlist.to_dict('records')}
    except Exception as e:
        logger.error(f"获取自选股列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/watchlist/add")
async def add_to_watchlist(item: WatchlistItem):
    """添加自选股"""
    try:
        logger.info(f"接收到添加自选股请求: symbol={item.symbol}, notes={item.notes}")
        
        # 验证输入
        if not item.symbol or not item.symbol.strip():
            raise HTTPException(status_code=400, detail="股票代码不能为空")
        
        # 先添加股票信息（如果不存在）
        db_manager.add_stock(
            symbol=item.symbol.strip(),
            name=f"{item.symbol.strip()}公司",  # 这里可以从API获取真实名称
            industry="未知",
            market="未知"
        )
        
        # 添加到自选股
        db_manager.add_to_watchlist(item.symbol.strip(), item.notes)
        
        return {"status": "success", "message": f"已添加 {item.symbol} 到自选股"}
    except Exception as e:
        logger.error(f"添加自选股失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/watchlist/{symbol}")
async def remove_from_watchlist(symbol: str):
    """移除自选股"""
    try:
        db_manager.remove_from_watchlist(symbol)
        return {"status": "success", "message": f"已移除 {symbol} 从自选股"}
    except Exception as e:
        logger.error(f"移除自选股失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 策略管理
@app.get("/strategies", response_class=HTMLResponse)
async def strategies_page(request: Request):
    """策略管理页面"""
    return templates.TemplateResponse("strategies.html", {"request": request})

@app.get("/risk", response_class=HTMLResponse)
async def risk_page(request: Request):
    """风险管理页面"""
    return templates.TemplateResponse("risk.html", {"request": request})


# 回测功能
@app.get("/backtest", response_class=HTMLResponse)
async def backtest_page(request: Request):
    """回测页面"""
    try:
        watchlist = db_manager.get_watchlist()
        strategies = await get_available_strategies()
        return templates.TemplateResponse("backtest.html", {
            "request": request,
            "watchlist": watchlist,
            "strategies": strategies
        })
    except Exception as e:
        logger.error(f"回测页面加载失败: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.post("/api/backtest/run")
async def run_backtest_api(request: BacktestRequest):
    """运行回测"""
    try:
        # 创建回测配置
        config = create_backtest_config(
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital
        )
        
        # 运行回测
        results = await run_backtest(
            strategy_name=request.strategy_name,
            symbols=request.symbols,
            config=config
        )
        
        # 转换结果为可序列化格式
        results_dict = {
            "total_return": results.total_return,
            "annual_return": results.annual_return,
            "volatility": results.volatility,
            "sharpe_ratio": results.sharpe_ratio,
            "max_drawdown": results.max_drawdown,
            "calmar_ratio": results.calmar_ratio,
            "win_rate": results.win_rate,
            "profit_factor": results.profit_factor,
            "trades_count": len(results.trades),
            "equity_curve": results.equity_curve.to_dict() if not results.equity_curve.empty else {},
            "daily_returns": results.daily_returns.to_dict() if not results.daily_returns.empty else {}
        }
        
        return {"status": "success", "results": results_dict}
        
    except Exception as e:
        logger.error(f"回测运行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI分析功能
@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """分析页面"""
    try:
        watchlist = db_manager.get_watchlist()
        return templates.TemplateResponse("analysis.html", {
            "request": request,
            "watchlist": watchlist
        })
    except Exception as e:
        logger.error(f"分析页面加载失败: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.post("/api/analysis/stock")
async def analyze_stock(request: AnalysisRequest):
    """分析股票"""
    try:
        # 获取股票数据
        data = await data_manager.get_stock_data(
            symbol=request.symbol,
            start_date=(datetime.now() - timedelta(days=request.data_period)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"无法获取 {request.symbol} 的数据")
        
        # 计算技术指标
        data_with_indicators = indicators_calculator.calculate_all_indicators(data)
        
        # 根据分析类型进行分析
        if request.analysis_type == "technical":
            analysis_result = await technical_analysis(data_with_indicators, request.symbol)
        elif request.analysis_type == "sentiment":
            analysis_result = await sentiment_analysis(data_with_indicators, request.symbol)
        elif request.analysis_type == "ai_signal":
            analysis_result = await ai_signal_analysis(data_with_indicators, request.symbol)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的分析类型: {request.analysis_type}")
        
        return {"status": "success", "analysis": analysis_result}
        
    except Exception as e:
        logger.error(f"股票分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 图表页面
@app.get("/chart/{symbol}", response_class=HTMLResponse)
async def chart_page(request: Request, symbol: str):
    """股票图表页面"""
    try:
        # 获取股票数据
        data = db_manager.get_kline_data(symbol)
        
        if data.empty:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": f"没有找到 {symbol} 的数据"
            })
        
        # 获取股票基本信息
        stocks = db_manager.get_all_stocks()
        stock_info = stocks[stocks['symbol'] == symbol]
        stock_name = stock_info['name'].iloc[0] if not stock_info.empty else symbol
        
        return templates.TemplateResponse("chart.html", {
            "request": request,
            "symbol": symbol,
            "stock_name": stock_name,
            "data": data
        })
    except Exception as e:
        logger.error(f"图表页面加载失败: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

# 数据管理
@app.get("/data", response_class=HTMLResponse)
async def data_page(request: Request):
    """数据管理页面"""
    try:
        # 获取数据统计
        data_stats = await get_data_stats()
        # 获取自选股列表用于数据更新
        watchlist = db_manager.get_watchlist()
        return templates.TemplateResponse("data.html", {
            "request": request,
            "data_stats": data_stats,
            "watchlist": watchlist
        })
    except Exception as e:
        logger.error(f"数据页面加载失败: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.post("/api/data/update/{symbol}")
async def update_stock_data(symbol: str):
    """更新股票数据"""
    try:
        # 获取最新数据
        data = await data_manager.get_stock_data(
            symbol=symbol,
            start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"无法获取 {symbol} 的数据")
        
        # 保存到数据库
        for _, row in data.iterrows():
            db_manager.add_kline_data(
                symbol=symbol,
                date=row['date'],
                open_price=row['open'],
                high_price=row['high'],
                low_price=row['low'],
                close_price=row['close'],
                volume=row['volume']
            )
        
        return {"status": "success", "message": f"已更新 {symbol} 的数据"}
        
    except Exception as e:
        logger.error(f"更新数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 系统监控
@app.get("/monitor", response_class=HTMLResponse)
async def monitor_page(request: Request):
    """系统监控页面"""
    try:
        system_status = await get_system_status()
        return templates.TemplateResponse("monitor.html", {
            "request": request,
            "system_status": system_status
        })
    except Exception as e:
        logger.error(f"监控页面加载失败: {e}")
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })

@app.get("/api/monitor/status")
async def get_system_status_api():
    """获取系统状态"""
    try:
        status = await get_system_status()
        return {"status": "success", "data": status}
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 辅助函数
async def get_system_stats() -> Dict[str, Any]:
    """获取系统统计信息"""
    try:
        watchlist_count = len(db_manager.get_watchlist())
        stocks_count = len(db_manager.get_all_stocks())
        
        # 获取AI模型状态
        ai_status = await ai_manager.health_check_all()
        active_models = [model for model, status in ai_status.items() if status]
        
        return {
            "watchlist_count": watchlist_count,
            "stocks_count": stocks_count,
            "active_ai_models": len(active_models),
            "ai_models": list(ai_status.keys())
        }
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        return {}

async def get_available_strategies() -> List[Dict[str, Any]]:
    """获取可用策略列表"""
    return [
        {
            "name": "momentum",
            "display_name": "动量策略",
            "description": "基于价格动量的趋势跟踪策略",
            "parameters": {
                "lookback_period": 20,
                "threshold": 0.02,
                "position_ratio": 0.1
            },
            "enabled": True
        },
        {
            "name": "mean_reversion",
            "display_name": "均值回归策略",
            "description": "基于布林带和RSI的均值回归策略",
            "parameters": {
                "lookback_period": 20,
                "bb_period": 20,
                "bb_std": 2,
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "position_ratio": 0.1
            },
            "enabled": True
        },
        {
            "name": "ai_enhanced",
            "display_name": "AI增强策略",
            "description": "结合AI分析的智能策略",
            "parameters": {
                "position_ratio": 0.1
            },
            "enabled": True
        }
    ]

async def technical_analysis(data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """技术分析"""
    try:
        latest = data.iloc[-1]
        
        # 计算技术指标信号
        signals = {}
        
        # RSI信号
        if 'RSI_14' in data.columns:
            rsi = latest['RSI_14']
            if rsi > 70:
                signals['rsi'] = "超买"
            elif rsi < 30:
                signals['rsi'] = "超卖"
            else:
                signals['rsi'] = "中性"
        
        # MACD信号
        if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
            macd = latest['MACD']
            macd_signal = latest['MACD_Signal']
            if macd > macd_signal:
                signals['macd'] = "看涨"
            else:
                signals['macd'] = "看跌"
        
        # 布林带信号
        if 'BB_Upper' in data.columns and 'BB_Lower' in data.columns:
            price = latest['close']
            bb_upper = latest['BB_Upper']
            bb_lower = latest['BB_Lower']
            if price > bb_upper:
                signals['bb'] = "突破上轨"
            elif price < bb_lower:
                signals['bb'] = "跌破下轨"
            else:
                signals['bb'] = "区间震荡"
        
        return {
            "symbol": symbol,
            "current_price": latest['close'],
            "signals": signals,
            "indicators": {
                "rsi": latest.get('RSI_14', 0),
                "macd": latest.get('MACD', 0),
                "bb_position": latest.get('BB_Position', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"技术分析失败: {e}")
        return {"error": str(e)}

async def sentiment_analysis(data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """情绪分析"""
    try:
        # 这里可以集成AI情绪分析
        # 暂时返回模拟数据
        return {
            "symbol": symbol,
            "sentiment_score": 0.6,
            "sentiment_label": "中性偏乐观",
            "confidence": 0.75
        }
    except Exception as e:
        logger.error(f"情绪分析失败: {e}")
        return {"error": str(e)}

async def ai_signal_analysis(data: pd.DataFrame, symbol: str) -> Dict[str, Any]:
    """AI信号分析"""
    try:
        # 使用AI策略管理器生成信号
        strategy_manager = create_ai_strategy_manager()
        signal = await strategy_manager.get_consensus_signal(symbol, data)
        
        return {
            "symbol": symbol,
            "signal_type": signal.signal_type.value,
            "confidence": signal.confidence,
            "target_price": signal.target_price,
            "stop_loss": signal.stop_loss,
            "reasoning": signal.reasoning
        }
    except Exception as e:
        logger.error(f"AI信号分析失败: {e}")
        return {"error": str(e)}

async def get_data_stats() -> Dict[str, Any]:
    """获取数据统计"""
    try:
        # 这里可以添加更详细的数据统计
        return {
            "total_stocks": len(db_manager.get_all_stocks()),
            "watchlist_count": len(db_manager.get_watchlist()),
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取数据统计失败: {e}")
        return {}

async def get_system_status() -> Dict[str, Any]:
    """获取系统状态"""
    try:
        # 检查AI模型状态
        ai_status = await ai_manager.health_check_all()
        
        # 检查数据库连接
        db_status = "正常"  # 这里可以添加实际的数据库健康检查
        
        return {
            "ai_models": ai_status,
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return {"error": str(e)}

# ==================== 策略管理API ====================

class StrategyCreateRequest(BaseModel):
    """创建策略请求"""
    name: str
    description: str
    strategy_type: str
    parameters: Dict[str, Any]
    tags: List[str] = []

class StrategyUpdateRequest(BaseModel):
    """更新策略请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None

@app.get("/api/strategies/types")
async def get_strategy_types():
    """获取策略类型列表"""
    return {
        "types": [
            {"value": "momentum", "label": "动量策略", "description": "基于价格动量的策略"},
            {"value": "mean_reversion", "label": "均值回归策略", "description": "基于价格均值回归的策略"},
            {"value": "breakout", "label": "突破策略", "description": "基于价格突破的策略"},
            {"value": "custom", "label": "自定义策略", "description": "用户自定义的策略"}
        ]
    }

@app.get("/api/strategies")
async def get_strategies():
    """获取所有策略"""
    try:
        strategies = strategy_config_manager.get_all_strategies()
        result = {}
        for strategy_id, strategy in strategies.items():
            result[strategy_id] = {
                "id": strategy.id,
                "name": strategy.name,
                "description": strategy.description,
                "strategy_type": strategy.strategy_type.value,
                "status": strategy.status.value,
                "parameters": {k: {
                    "name": v.name,
                    "value": v.value,
                    "min_value": v.min_value,
                    "max_value": v.max_value,
                    "step": v.step,
                    "description": v.description,
                    "parameter_type": v.parameter_type
                } for k, v in strategy.parameters.items()},
                "created_at": strategy.created_at.isoformat(),
                "updated_at": strategy.updated_at.isoformat(),
                "created_by": strategy.created_by,
                "version": strategy.version,
                "tags": strategy.tags
            }
        return {"strategies": result}
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/strategies/{strategy_id}")
async def get_strategy(strategy_id: str):
    """获取单个策略"""
    try:
        strategy = strategy_config_manager.get_strategy(strategy_id)
        if not strategy:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return {
            "id": strategy.id,
            "name": strategy.name,
            "description": strategy.description,
            "strategy_type": strategy.strategy_type.value,
            "status": strategy.status.value,
            "parameters": {k: {
                "name": v.name,
                "value": v.value,
                "min_value": v.min_value,
                "max_value": v.max_value,
                "step": v.step,
                "description": v.description,
                "parameter_type": v.parameter_type
            } for k, v in strategy.parameters.items()},
            "created_at": strategy.created_at.isoformat(),
            "updated_at": strategy.updated_at.isoformat(),
            "created_by": strategy.created_by,
            "version": strategy.version,
            "tags": strategy.tags
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/strategies")
async def create_strategy(request: StrategyCreateRequest):
    """创建新策略"""
    try:
        # 生成策略ID
        strategy_id = f"{request.strategy_type}_{len(strategy_config_manager.get_all_strategies()) + 1}"
        
        # 转换参数
        parameters = {}
        for param_name, param_data in request.parameters.items():
            parameters[param_name] = StrategyParameter(
                name=param_data.get("name", param_name),
                value=param_data.get("value"),
                min_value=param_data.get("min_value"),
                max_value=param_data.get("max_value"),
                step=param_data.get("step"),
                description=param_data.get("description", ""),
                parameter_type=param_data.get("parameter_type", "float")
            )
        
        # 创建策略配置
        strategy = StrategyConfig(
            id=strategy_id,
            name=request.name,
            description=request.description,
            strategy_type=StrategyType(request.strategy_type),
            status=StrategyStatus.ENABLED,
            parameters=parameters,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=request.tags
        )
        
        success = strategy_config_manager.add_strategy(strategy)
        if not success:
            raise HTTPException(status_code=400, detail="创建策略失败")
        
        return {"message": "策略创建成功", "strategy_id": strategy_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/strategies/{strategy_id}")
async def update_strategy(strategy_id: str, request: StrategyUpdateRequest):
    """更新策略"""
    try:
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.status is not None:
            updates["status"] = StrategyStatus(request.status)
        if request.tags is not None:
            updates["tags"] = request.tags
        
        success = strategy_config_manager.update_strategy(strategy_id, updates)
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在或更新失败")
        
        return {"message": "策略更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/strategies/{strategy_id}/parameters")
async def update_strategy_parameters(strategy_id: str, parameters: Dict[str, Any]):
    """更新策略参数"""
    try:
        success = strategy_config_manager.update_strategy_parameters(strategy_id, parameters)
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在或更新失败")
        
        return {"message": "策略参数更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新策略参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/strategies/{strategy_id}/enable")
async def enable_strategy(strategy_id: str):
    """启用策略"""
    try:
        success = strategy_config_manager.enable_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return {"message": "策略已启用"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启用策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/strategies/{strategy_id}/disable")
async def disable_strategy(strategy_id: str):
    """禁用策略"""
    try:
        success = strategy_config_manager.disable_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return {"message": "策略已禁用"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"禁用策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/strategies/{strategy_id}")
async def delete_strategy(strategy_id: str):
    """删除策略"""
    try:
        success = strategy_config_manager.delete_strategy(strategy_id)
        if not success:
            raise HTTPException(status_code=404, detail="策略不存在")
        
        return {"message": "策略已删除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 风险管理API ====================

class RiskAnalysisRequest(BaseModel):
    """风险分析请求"""
    symbols: List[str]
    positions: Dict[str, float]  # 股票代码 -> 持仓金额
    portfolio_value: float

@app.post("/api/risk/analyze")
async def analyze_portfolio_risk(request: RiskAnalysisRequest):
    """分析投资组合风险"""
    try:
        # 获取股票价格数据
        prices = {}
        for symbol in request.symbols:
            data = await data_manager.get_stock_data(symbol)
            if not data.empty:
                prices[symbol] = data
        
        # 进行风险分析
        risk_result = risk_manager.analyze_portfolio_risk(
            positions=request.positions,
            prices=prices,
            portfolio_value=request.portfolio_value
        )
        
        # 转换为可序列化的格式
        result = {
            "portfolio_value": risk_result.portfolio_value,
            "overall_risk_level": risk_result.overall_risk_level.value,
            "risk_score": risk_result.risk_score,
            "risk_metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "threshold": metric.threshold,
                    "level": metric.level.value,
                    "description": metric.description,
                    "recommendation": metric.recommendation
                }
                for metric in risk_result.risk_metrics
            ],
            "alerts": [
                {
                    "risk_type": alert.risk_type.value,
                    "level": alert.level.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                    "symbol": alert.symbol,
                    "value": alert.value,
                    "threshold": alert.threshold
                }
                for alert in risk_result.alerts
            ],
            "recommendations": risk_result.recommendations,
            "timestamp": risk_result.timestamp.isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"风险分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/risk/thresholds")
async def get_risk_thresholds():
    """获取风险阈值配置"""
    try:
        return {"thresholds": risk_manager.get_risk_thresholds()}
    except Exception as e:
        logger.error(f"获取风险阈值失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/risk/thresholds")
async def update_risk_thresholds(thresholds: Dict[str, float]):
    """更新风险阈值配置"""
    try:
        risk_manager.update_risk_thresholds(thresholds)
        return {"message": "风险阈值更新成功"}
    except Exception as e:
        logger.error(f"更新风险阈值失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/risk/levels")
async def get_risk_levels():
    """获取风险等级列表"""
    return {
        "levels": [
            {"value": "low", "label": "低风险", "color": "success"},
            {"value": "medium", "label": "中风险", "color": "warning"},
            {"value": "high", "label": "高风险", "color": "danger"},
            {"value": "critical", "label": "极高风险", "color": "dark"}
        ]
    }

@app.get("/api/risk/types")
async def get_risk_types():
    """获取风险类型列表"""
    return {
        "types": [
            {"value": "market", "label": "市场风险", "description": "由市场波动引起的风险"},
            {"value": "concentration", "label": "集中度风险", "description": "投资过于集中带来的风险"},
            {"value": "liquidity", "label": "流动性风险", "description": "无法及时买卖的风险"},
            {"value": "volatility", "label": "波动性风险", "description": "价格波动过大的风险"},
            {"value": "drawdown", "label": "回撤风险", "description": "投资组合价值下降的风险"},
            {"value": "correlation", "label": "相关性风险", "description": "资产间相关性过高的风险"}
        ]
    }

# ==================== K线图API ====================

@app.get("/api/chart/{symbol}")
async def get_kline_chart(symbol: str, chart_type: str = "kline", days: int = 30):
    """获取K线图"""
    try:
        # 获取股票数据
        data = await data_manager.get_stock_data(symbol)
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"没有找到 {symbol} 的数据")
        
        # 限制数据量
        if len(data) > days:
            data = data.tail(days)
        
        # 获取股票基本信息
        stocks = db_manager.get_all_stocks()
        stock_info = stocks[stocks['symbol'] == symbol]
        stock_name = stock_info['name'].iloc[0] if not stock_info.empty else symbol
        
        # 准备K线图数据数组
        import pandas as pd
        data = data.copy()
        if not pd.api.types.is_datetime64_any_dtype(data['date']):
            data['date'] = pd.to_datetime(data['date'])
        
        dates = data['date'].dt.strftime('%Y-%m-%d').tolist()
        kline_data = data[['open', 'close', 'low', 'high']].values.tolist()
        
        return {
            "symbol": symbol,
            "stock_name": stock_name,
            "dates": dates,
            "kline_data": kline_data,
            "chart_type": chart_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成K线图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chart/{symbol}/technical")
async def get_technical_chart(symbol: str, days: int = 30):
    """获取技术指标图表"""
    try:
        # 获取股票数据
        data = await data_manager.get_stock_data(symbol)
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"没有找到 {symbol} 的数据")
        
        # 限制数据量
        if len(data) > days:
            data = data.tail(days)
        
        # 计算技术指标
        if not data.empty:
            data = indicators_calculator.calculate_all_indicators(data)
        
        # 获取股票基本信息
        stocks = db_manager.get_all_stocks()
        stock_info = stocks[stocks['symbol'] == symbol]
        stock_name = stock_info['name'].iloc[0] if not stock_info.empty else symbol
        
        # 生成技术指标图表
        chart_html = kline_chart_generator.create_technical_indicators_chart(
            symbol=symbol,
            stock_name=stock_name,
            data=data
        )
        
        return {"chart_html": chart_html}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成技术指标图表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}")
async def get_stock_info(symbol: str):
    """获取股票基本信息"""
    try:
        # 获取股票基本信息
        stocks = db_manager.get_all_stocks()
        stock_info = stocks[stocks['symbol'] == symbol]
        
        if stock_info.empty:
            raise HTTPException(status_code=404, detail=f"股票 {symbol} 不存在")
        
        stock = stock_info.iloc[0]
        
        # 获取最新价格数据
        try:
            data = await data_manager.get_stock_data(symbol)
            current_price = None
            change_percent = 0
            volume = 0
            
            if not data.empty:
                latest = data.iloc[-1]
                current_price = float(latest.get('close', 0)) if latest.get('close') is not None else None
                volume = int(latest.get('volume', 0)) if latest.get('volume') is not None else 0
                
                # 计算涨跌幅（如果有前一天数据）
                if len(data) > 1:
                    prev_close = float(data.iloc[-2].get('close', 0)) if data.iloc[-2].get('close') is not None else 0
                    if prev_close > 0 and current_price is not None:
                        change_percent = ((current_price - prev_close) / prev_close) * 100
        except Exception as e:
            logger.warning(f"获取价格数据失败: {e}")
            current_price = None
            change_percent = 0
            volume = 0
        
        return {
            "stock": {
                "symbol": stock['symbol'],
                "name": stock['name'],
                "industry": stock['industry'],
                "market": stock['market'],
                "current_price": current_price,
                "change_percent": change_percent,
                "volume": volume,
                "market_cap": None  # 可以后续添加市值计算
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取股票信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
