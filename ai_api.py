"""
AI集成的Web API接口
提供AI分析、策略优化、风险预警等功能的REST API
"""
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd

from ai_integration import ai_manager, QuantAIAnalyzer
from ai_enhanced_strategies import AIStrategyManager, create_ai_strategy_manager
from ai_config_manager import ai_config_manager, ai_usage_tracker
from database import db_manager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="量化交易AI系统",
    description="基于AI的量化交易分析和策略系统",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建AI分析器实例
quant_ai = QuantAIAnalyzer(ai_manager)
strategy_manager = create_ai_strategy_manager()

# Pydantic模型定义
class StockAnalysisRequest(BaseModel):
    symbol: str
    analysis_type: str  # 'sentiment', 'signal', 'risk', 'comprehensive'
    data_period: Optional[int] = 30  # 分析数据天数

class StrategyOptimizationRequest(BaseModel):
    strategy_name: str
    backtest_results: Dict[str, Any]
    optimization_goals: List[str]  # ['return', 'sharpe', 'drawdown', 'win_rate']

class AIConfigRequest(BaseModel):
    model_name: str
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None

class TradingSignalRequest(BaseModel):
    symbol: str
    strategies: Optional[List[str]] = None
    use_consensus: bool = True

class RiskAnalysisRequest(BaseModel):
    portfolio_data: Dict[str, Any]
    risk_metrics: Optional[List[str]] = None

# API端点
@app.get("/")
async def root():
    """根端点"""
    return {
        "message": "量化交易AI系统API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ai/status")
async def get_ai_status():
    """获取AI系统状态"""
    try:
        # 获取模型状态
        model_status = ai_config_manager.get_model_status()
        
        # 健康检查
        health_status = await ai_manager.health_check_all()
        
        # 使用统计
        usage_stats = ai_usage_tracker.get_stats()
        
        return {
            "models": model_status,
            "health": health_status,
            "usage": usage_stats,
            "active_provider": ai_manager.active_provider,
            "fallback_chain": ai_manager.fallback_chain
        }
    except Exception as e:
        logger.error(f"获取AI状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/analyze/stock")
async def analyze_stock(request: StockAnalysisRequest, background_tasks: BackgroundTasks):
    """分析股票"""
    try:
        # 获取股票数据
        data = db_manager.get_kline_data(
            request.symbol, 
            start_date=(datetime.now() - timedelta(days=request.data_period)).strftime("%Y-%m-%d")
        )
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票 {request.symbol} 的数据")
        
        # 根据分析类型执行不同分析
        if request.analysis_type == "sentiment":
            result = await quant_ai.analyze_market_sentiment(request.symbol)
        elif request.analysis_type == "signal":
            result = await quant_ai.generate_trading_signals(request.symbol, data)
        elif request.analysis_type == "risk":
            portfolio_data = {"symbol": request.symbol, "data": data.to_dict()}
            result = await quant_ai.generate_risk_warning(portfolio_data)
        elif request.analysis_type == "comprehensive":
            # 综合分析
            sentiment = await quant_ai.analyze_market_sentiment(request.symbol)
            signals = await quant_ai.generate_trading_signals(request.symbol, data)
            portfolio_data = {"symbol": request.symbol, "data": data.to_dict()}
            risk = await quant_ai.generate_risk_warning(portfolio_data)
            
            result = {
                "sentiment": sentiment,
                "signals": signals,
                "risk": risk,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的分析类型")
        
        # 保存分析结果到数据库
        background_tasks.add_task(
            db_manager.save_ai_analysis,
            request.symbol,
            request.analysis_type,
            ai_manager.active_provider or "unknown",
            {"data_period": request.data_period},
            result,
            result.get("confidence", 0.5) if isinstance(result, dict) else 0.5
        )
        
        return {
            "symbol": request.symbol,
            "analysis_type": request.analysis_type,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"股票分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/strategies/signals")
async def get_trading_signals(request: TradingSignalRequest, background_tasks: BackgroundTasks):
    """获取交易信号"""
    try:
        # 获取股票数据
        data = db_manager.get_kline_data(request.symbol)
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票 {request.symbol} 的数据")
        
        if request.use_consensus:
            # 获取共识信号
            signal = await strategy_manager.get_consensus_signal(request.symbol, data)
            signals = {"consensus": signal}
        else:
            # 获取指定策略信号
            strategies = request.strategies or ["momentum", "mean_reversion", "breakout"]
            signals = await strategy_manager.analyze_symbol(request.symbol, data, strategies)
        
        # 保存信号到数据库
        for strategy_name, signal in signals.items():
            background_tasks.add_task(
                db_manager.save_ai_analysis,
                request.symbol,
                f"signal_{strategy_name}",
                ai_manager.active_provider or "unknown",
                {"strategies": strategies},
                signal.__dict__,
                signal.confidence
            )
        
        return {
            "symbol": request.symbol,
            "signals": {k: {
                "signal_type": v.signal_type.value,
                "confidence": v.confidence,
                "price": v.price,
                "target_price": v.target_price,
                "stop_loss": v.stop_loss,
                "reasoning": v.reasoning,
                "timestamp": v.timestamp.isoformat()
            } for k, v in signals.items()}
        }
    
    except Exception as e:
        logger.error(f"获取交易信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/strategies/optimize")
async def optimize_strategy(request: StrategyOptimizationRequest, background_tasks: BackgroundTasks):
    """优化策略参数"""
    try:
        result = await quant_ai.optimize_strategy_parameters(
            request.strategy_name,
            request.backtest_results
        )
        
        # 保存优化结果
        background_tasks.add_task(
            db_manager.save_ai_analysis,
            "strategy_optimization",
            "optimization",
            ai_manager.active_provider or "unknown",
            {
                "strategy_name": request.strategy_name,
                "goals": request.optimization_goals
            },
            result
        )
        
        return {
            "strategy_name": request.strategy_name,
            "optimization": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"策略优化失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/risk/analyze")
async def analyze_risk(request: RiskAnalysisRequest, background_tasks: BackgroundTasks):
    """风险分析"""
    try:
        result = await quant_ai.generate_risk_warning(request.portfolio_data)
        
        # 保存风险分析结果
        background_tasks.add_task(
            db_manager.save_ai_analysis,
            "portfolio",
            "risk",
            ai_manager.active_provider or "unknown",
            request.portfolio_data,
            result
        )
        
        return {
            "risk_analysis": result,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"风险分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/analysis/history")
async def get_analysis_history(
    symbol: Optional[str] = None,
    analysis_type: Optional[str] = None,
    limit: int = 100
):
    """获取分析历史"""
    try:
        results = db_manager.get_ai_analysis(symbol, analysis_type)
        
        # 限制返回数量
        if len(results) > limit:
            results = results.head(limit)
        
        return {
            "results": results.to_dict("records"),
            "total": len(results),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"获取分析历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/usage/stats")
async def get_usage_stats(
    model_name: Optional[str] = None,
    days: int = 7
):
    """获取使用统计"""
    try:
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        stats = db_manager.get_ai_usage_stats(model_name, start_date)
        
        # 计算统计信息
        total_requests = len(stats)
        successful_requests = len(stats[stats['success'] == True])
        failed_requests = total_requests - successful_requests
        success_rate = successful_requests / total_requests if total_requests > 0 else 0
        
        total_tokens = stats['tokens_used'].sum()
        total_cost = stats['cost'].sum()
        avg_response_time = stats['response_time'].mean() if 'response_time' in stats.columns else 0
        
        return {
            "period_days": days,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": success_rate,
            "total_tokens": int(total_tokens),
            "total_cost": float(total_cost),
            "avg_response_time": float(avg_response_time),
            "model_breakdown": stats.groupby('model_name').agg({
                'success': ['count', 'sum'],
                'tokens_used': 'sum',
                'cost': 'sum'
            }).to_dict(),
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"获取使用统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/config/update")
async def update_ai_config(request: AIConfigRequest):
    """更新AI配置"""
    try:
        updates = {}
        if request.api_key is not None:
            updates["api_key"] = request.api_key
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        if request.parameters:
            updates.update(request.parameters)
        
        success = ai_config_manager.update_model_config(request.model_name, updates)
        
        if success:
            return {
                "message": f"模型 {request.model_name} 配置更新成功",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="配置更新失败")
    
    except Exception as e:
        logger.error(f"更新AI配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/config/export")
async def export_ai_config():
    """导出AI配置"""
    try:
        config = ai_config_manager.config
        return {
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"导出AI配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/config/import")
async def import_ai_config(config_data: Dict[str, Any]):
    """导入AI配置"""
    try:
        ai_config_manager.config = config_data
        ai_config_manager.save_config()
        ai_config_manager._setup_ai_models()
        
        return {
            "message": "AI配置导入成功",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"导入AI配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ai/strategies/list")
async def list_strategies():
    """获取可用策略列表"""
    try:
        strategies = {}
        for name, strategy in strategy_manager.strategies.items():
            strategies[name] = {
                "name": strategy.name,
                "enabled": strategy.enabled,
                "parameters": strategy.parameters
            }
        
        return {
            "strategies": strategies,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"获取策略列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/strategies/{strategy_name}/enable")
async def enable_strategy(strategy_name: str):
    """启用策略"""
    try:
        strategy_manager.enable_strategy(strategy_name)
        return {
            "message": f"策略 {strategy_name} 已启用",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"启用策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/strategies/{strategy_name}/disable")
async def disable_strategy(strategy_name: str):
    """禁用策略"""
    try:
        strategy_manager.disable_strategy(strategy_name)
        return {
            "message": f"策略 {strategy_name} 已禁用",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"禁用策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ai/strategies/{strategy_name}/parameters")
async def update_strategy_parameters(strategy_name: str, parameters: Dict[str, Any]):
    """更新策略参数"""
    try:
        strategy_manager.update_strategy_parameters(strategy_name, parameters)
        return {
            "message": f"策略 {strategy_name} 参数更新成功",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        logger.error(f"更新策略参数失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 启动事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info("AI量化交易系统启动中...")
    
    # 初始化AI配置
    try:
        ai_config_manager._setup_ai_models()
        logger.info("AI模型初始化完成")
    except Exception as e:
        logger.error(f"AI模型初始化失败: {e}")
    
    logger.info("AI量化交易系统启动完成")

# 关闭事件
@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("AI量化交易系统关闭中...")
    logger.info("AI量化交易系统已关闭")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
