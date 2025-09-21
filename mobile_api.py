"""
移动端API模块
提供移动端专用的API接口和响应式设计支持
"""
from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import json
import logging
from datetime import datetime, timedelta
import asyncio

from database import db_manager
from data_acquisition import data_manager
from technical_indicators import indicators_calculator
from ai_enhanced_strategies import create_ai_strategy_manager
from security import validate_jwt_token, validate_api_key, log_audit_event
from monitoring import get_health_status, get_system_metrics

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建移动端API应用
app = FastAPI(
    title="量化交易AI系统 - 移动端API",
    version="1.0.0",
    description="专为移动设备优化的API接口"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务
app.mount("/static", StaticFiles(directory="static"), name="static")

# Pydantic模型
class MobileStockInfo(BaseModel):
    symbol: str
    name: str
    price: float
    change: float
    change_percent: float
    volume: int
    market_cap: float
    last_updated: str

class MobileSignal(BaseModel):
    symbol: str
    signal_type: str
    confidence: float
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    reasoning: str
    timestamp: str

class MobilePortfolio(BaseModel):
    total_value: float
    total_change: float
    total_change_percent: float
    positions: List[Dict[str, Any]]
    last_updated: str

class MobileAlert(BaseModel):
    alert_id: str
    symbol: str
    alert_type: str
    message: str
    is_read: bool
    created_at: str

class MobileNews(BaseModel):
    news_id: str
    title: str
    summary: str
    source: str
    published_at: str
    sentiment: Optional[str] = None

# 认证依赖
async def get_current_user(request: Request, authorization: str = Header(None)):
    """获取当前用户"""
    if not authorization:
        raise HTTPException(status_code=401, detail="缺少认证信息")
    
    try:
        # 支持Bearer token和API key两种认证方式
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            user_info = validate_jwt_token(token)
            if not user_info:
                raise HTTPException(status_code=401, detail="无效的JWT令牌")
            return user_info
        else:
            # API key认证
            api_key_info = validate_api_key(authorization)
            if not api_key_info:
                raise HTTPException(status_code=401, detail="无效的API密钥")
            return {"user_id": api_key_info.user_id, "is_admin": False}
    except Exception as e:
        logger.error(f"认证失败: {e}")
        raise HTTPException(status_code=401, detail="认证失败")

# 移动端首页
@app.get("/", response_class=HTMLResponse)
async def mobile_home():
    """移动端首页"""
    return """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>量化交易AI系统 - 移动端</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="/static/css/mobile.css" rel="stylesheet">
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <div class="col-12">
                    <h1 class="text-center mb-4">量化交易AI系统</h1>
                    <div class="card">
                        <div class="card-body text-center">
                            <h5>移动端API服务</h5>
                            <p>专为移动设备优化的量化交易分析平台</p>
                            <a href="/docs" class="btn btn-primary">查看API文档</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """

# 市场概览
@app.get("/api/mobile/market/overview")
async def get_market_overview(current_user: dict = Depends(get_current_user)):
    """获取市场概览"""
    try:
        # 获取系统健康状态
        health_status = get_health_status()
        
        # 获取自选股数量
        watchlist_count = len(db_manager.get_watchlist())
        
        # 获取系统指标
        system_metrics = get_system_metrics(1)
        
        return {
            "status": "success",
            "data": {
                "system_status": health_status["status"],
                "watchlist_count": watchlist_count,
                "active_ai_models": len([m for m in health_status.get("ai_models", {}).values() if m]),
                "last_updated": datetime.now().isoformat(),
                "system_metrics": system_metrics[-1] if system_metrics else None
            }
        }
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 自选股列表
@app.get("/api/mobile/watchlist")
async def get_mobile_watchlist(current_user: dict = Depends(get_current_user)):
    """获取移动端自选股列表"""
    try:
        watchlist = db_manager.get_watchlist()
        
        # 获取实时价格数据
        symbols = watchlist['symbol'].tolist()
        realtime_data = await data_manager.get_realtime_data(symbols)
        
        # 构建移动端数据
        mobile_stocks = []
        for _, stock in watchlist.iterrows():
            symbol = stock['symbol']
            realtime = realtime_data.get(symbol, {})
            
            mobile_stock = MobileStockInfo(
                symbol=symbol,
                name=stock['name'],
                price=realtime.get('price', 0.0),
                change=realtime.get('change', 0.0),
                change_percent=realtime.get('change_percent', 0.0),
                volume=realtime.get('volume', 0),
                market_cap=realtime.get('market_cap', 0.0),
                last_updated=realtime.get('timestamp', datetime.now().isoformat())
            )
            mobile_stocks.append(mobile_stock)
        
        return {
            "status": "success",
            "data": mobile_stocks
        }
    except Exception as e:
        logger.error(f"获取自选股列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 股票详情
@app.get("/api/mobile/stock/{symbol}")
async def get_mobile_stock_detail(symbol: str, current_user: dict = Depends(get_current_user)):
    """获取移动端股票详情"""
    try:
        # 获取股票数据
        data = await data_manager.get_stock_data(
            symbol=symbol,
            start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
            end_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"未找到股票 {symbol} 的数据")
        
        # 计算技术指标
        data_with_indicators = indicators_calculator.calculate_all_indicators(data)
        
        # 获取最新数据
        latest = data_with_indicators.iloc[-1]
        
        # 构建移动端响应
        stock_detail = {
            "symbol": symbol,
            "name": latest.get('name', symbol),
            "current_price": float(latest['close']),
            "open_price": float(latest['open']),
            "high_price": float(latest['high']),
            "low_price": float(latest['low']),
            "volume": int(latest['volume']),
            "change": float(latest['close'] - latest['open']),
            "change_percent": float((latest['close'] - latest['open']) / latest['open'] * 100),
            "indicators": {
                "rsi": float(latest.get('RSI_14', 0)),
                "macd": float(latest.get('MACD', 0)),
                "bb_position": float(latest.get('BB_Position', 0)),
                "sma_20": float(latest.get('SMA_20', 0)),
                "sma_50": float(latest.get('SMA_50', 0))
            },
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "data": stock_detail
        }
    except Exception as e:
        logger.error(f"获取股票详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI信号
@app.get("/api/mobile/signals")
async def get_mobile_signals(current_user: dict = Depends(get_current_user)):
    """获取移动端AI信号"""
    try:
        # 获取自选股列表
        watchlist = db_manager.get_watchlist()
        symbols = watchlist['symbol'].tolist()
        
        # 获取AI策略管理器
        strategy_manager = create_ai_strategy_manager()
        
        # 获取信号
        signals = []
        for symbol in symbols[:10]:  # 限制数量以提高性能
            try:
                data = await data_manager.get_stock_data(
                    symbol=symbol,
                    start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                    end_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                if not data.empty:
                    signal = await strategy_manager.get_consensus_signal(symbol, data)
                    mobile_signal = MobileSignal(
                        symbol=symbol,
                        signal_type=signal.signal_type.value,
                        confidence=signal.confidence,
                        target_price=signal.target_price,
                        stop_loss=signal.stop_loss,
                        reasoning=signal.reasoning,
                        timestamp=datetime.now().isoformat()
                    )
                    signals.append(mobile_signal)
            except Exception as e:
                logger.warning(f"获取 {symbol} 信号失败: {e}")
                continue
        
        return {
            "status": "success",
            "data": signals
        }
    except Exception as e:
        logger.error(f"获取AI信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 投资组合概览
@app.get("/api/mobile/portfolio")
async def get_mobile_portfolio(current_user: dict = Depends(get_current_user)):
    """获取移动端投资组合概览"""
    try:
        # 这里应该从实际的交易记录中获取投资组合数据
        # 目前返回模拟数据
        portfolio = MobilePortfolio(
            total_value=1000000.0,
            total_change=15000.0,
            total_change_percent=1.5,
            positions=[
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "avg_price": 150.0,
                    "current_price": 165.0,
                    "market_value": 16500.0,
                    "unrealized_pnl": 1500.0,
                    "unrealized_pnl_percent": 10.0
                },
                {
                    "symbol": "MSFT",
                    "quantity": 50,
                    "avg_price": 300.0,
                    "current_price": 315.0,
                    "market_value": 15750.0,
                    "unrealized_pnl": 750.0,
                    "unrealized_pnl_percent": 5.0
                }
            ],
            last_updated=datetime.now().isoformat()
        )
        
        return {
            "status": "success",
            "data": portfolio
        }
    except Exception as e:
        logger.error(f"获取投资组合失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 市场新闻
@app.get("/api/mobile/news")
async def get_mobile_news(limit: int = 20, current_user: dict = Depends(get_current_user)):
    """获取移动端市场新闻"""
    try:
        # 这里应该从新闻API获取数据
        # 目前返回模拟数据
        news = [
            MobileNews(
                news_id="1",
                title="科技股表现强劲，苹果股价创新高",
                summary="受财报利好影响，科技股普遍上涨，苹果股价突破历史新高。",
                source="财经网",
                published_at=datetime.now().isoformat(),
                sentiment="positive"
            ),
            MobileNews(
                news_id="2",
                title="美联储维持利率不变",
                summary="美联储宣布维持当前利率水平，符合市场预期。",
                source="路透社",
                published_at=(datetime.now() - timedelta(hours=2)).isoformat(),
                sentiment="neutral"
            )
        ]
        
        return {
            "status": "success",
            "data": news[:limit]
        }
    except Exception as e:
        logger.error(f"获取市场新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 告警列表
@app.get("/api/mobile/alerts")
async def get_mobile_alerts(current_user: dict = Depends(get_current_user)):
    """获取移动端告警列表"""
    try:
        # 这里应该从告警系统获取数据
        # 目前返回模拟数据
        alerts = [
            MobileAlert(
                alert_id="1",
                symbol="AAPL",
                alert_type="price_alert",
                message="AAPL价格突破165美元",
                is_read=False,
                created_at=datetime.now().isoformat()
            ),
            MobileAlert(
                alert_id="2",
                symbol="MSFT",
                alert_type="volume_alert",
                message="MSFT成交量异常放大",
                is_read=True,
                created_at=(datetime.now() - timedelta(hours=1)).isoformat()
            )
        ]
        
        return {
            "status": "success",
            "data": alerts
        }
    except Exception as e:
        logger.error(f"获取告警列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加自选股
@app.post("/api/mobile/watchlist/add")
async def add_mobile_watchlist(symbol: str, current_user: dict = Depends(get_current_user)):
    """添加自选股到移动端"""
    try:
        # 添加股票信息
        db_manager.add_stock(
            symbol=symbol,
            name=f"{symbol}公司",
            industry="未知",
            market="未知"
        )
        
        # 添加到自选股
        db_manager.add_to_watchlist(symbol, "移动端添加")
        
        # 记录审计日志
        log_audit_event(
            user_id=current_user.get("user_id"),
            action="add_watchlist",
            resource=symbol,
            details=f"通过移动端添加自选股: {symbol}"
        )
        
        return {
            "status": "success",
            "message": f"已添加 {symbol} 到自选股"
        }
    except Exception as e:
        logger.error(f"添加自选股失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 移除自选股
@app.delete("/api/mobile/watchlist/{symbol}")
async def remove_mobile_watchlist(symbol: str, current_user: dict = Depends(get_current_user)):
    """从移动端移除自选股"""
    try:
        db_manager.remove_from_watchlist(symbol)
        
        # 记录审计日志
        log_audit_event(
            user_id=current_user.get("user_id"),
            action="remove_watchlist",
            resource=symbol,
            details=f"通过移动端移除自选股: {symbol}"
        )
        
        return {
            "status": "success",
            "message": f"已移除 {symbol} 从自选股"
        }
    except Exception as e:
        logger.error(f"移除自选股失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 系统状态
@app.get("/api/mobile/system/status")
async def get_mobile_system_status(current_user: dict = Depends(get_current_user)):
    """获取移动端系统状态"""
    try:
        health_status = get_health_status()
        system_metrics = get_system_metrics(1)
        
        return {
            "status": "success",
            "data": {
                "health_status": health_status,
                "system_metrics": system_metrics[-1] if system_metrics else None,
                "timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 错误处理
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """404错误处理"""
    return JSONResponse(
        status_code=404,
        content={
            "status": "error",
            "message": "请求的资源不存在",
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: Exception):
    """500错误处理"""
    logger.error(f"内部服务器错误: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "内部服务器错误",
            "path": str(request.url)
        }
    )

# 启动应用
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
