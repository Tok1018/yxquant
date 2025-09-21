"""
实时数据流处理模块
提供WebSocket连接、实时数据推送、数据流处理等功能
"""
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from websockets.server import WebSocketServerProtocol
import pandas as pd
import numpy as np
from collections import defaultdict, deque
import threading
import queue
import weakref

from data_acquisition import data_manager
from technical_indicators import indicators_calculator
from ai_enhanced_strategies import create_ai_strategy_manager
from monitoring import increment_counter, record_timer

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataStreamType(Enum):
    """数据流类型枚举"""
    PRICE = "price"
    VOLUME = "volume"
    TECHNICAL_INDICATORS = "technical_indicators"
    AI_SIGNALS = "ai_signals"
    MARKET_SENTIMENT = "market_sentiment"
    NEWS = "news"
    ALERTS = "alerts"

@dataclass
class RealtimeData:
    """实时数据结构"""
    symbol: str
    data_type: DataStreamType
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "realtime"

@dataclass
class WebSocketMessage:
    """WebSocket消息结构"""
    message_type: str
    data: Dict[str, Any]
    timestamp: str
    request_id: Optional[str] = None

class DataStreamProcessor:
    """数据流处理器"""
    
    def __init__(self):
        self.subscribers = defaultdict(set)  # 订阅者管理
        self.data_cache = defaultdict(lambda: deque(maxlen=1000))  # 数据缓存
        self.processing_queue = queue.Queue()
        self.running = False
        self.processing_thread = None
        
        # 启动处理线程
        self.start_processing()
    
    def start_processing(self):
        """启动数据处理线程"""
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        logger.info("数据流处理器已启动")
    
    def stop_processing(self):
        """停止数据处理"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
        logger.info("数据流处理器已停止")
    
    def _processing_loop(self):
        """数据处理循环"""
        while self.running:
            try:
                # 处理队列中的数据
                if not self.processing_queue.empty():
                    data = self.processing_queue.get_nowait()
                    self._process_data(data)
                else:
                    time.sleep(0.1)  # 避免CPU占用过高
            except Exception as e:
                logger.error(f"数据处理循环错误: {e}")
                time.sleep(1)
    
    def _process_data(self, data: RealtimeData):
        """处理单个数据"""
        try:
            # 缓存数据
            self.data_cache[data.symbol].append(data)
            
            # 通知订阅者
            self._notify_subscribers(data)
            
            # 记录统计
            increment_counter(f"realtime_data_{data.data_type.value}")
            
        except Exception as e:
            logger.error(f"处理数据失败: {e}")
    
    def _notify_subscribers(self, data: RealtimeData):
        """通知订阅者"""
        subscribers = self.subscribers.get(data.symbol, set())
        for subscriber in list(subscribers):  # 创建副本避免修改时出错
            try:
                if subscriber and hasattr(subscriber, 'send_data'):
                    subscriber.send_data(data)
            except Exception as e:
                logger.error(f"通知订阅者失败: {e}")
                # 移除无效的订阅者
                subscribers.discard(subscriber)
    
    def add_data(self, data: RealtimeData):
        """添加数据到处理队列"""
        self.processing_queue.put(data)
    
    def subscribe(self, symbol: str, subscriber):
        """订阅数据流"""
        self.subscribers[symbol].add(subscriber)
        logger.info(f"订阅 {symbol} 数据流")
    
    def unsubscribe(self, symbol: str, subscriber):
        """取消订阅"""
        self.subscribers[symbol].discard(subscriber)
        logger.info(f"取消订阅 {symbol} 数据流")
    
    def get_cached_data(self, symbol: str, data_type: DataStreamType = None, limit: int = 100) -> List[Dict]:
        """获取缓存数据"""
        cached_data = self.data_cache.get(symbol, deque())
        
        if data_type:
            filtered_data = [asdict(d) for d in cached_data if d.data_type == data_type]
        else:
            filtered_data = [asdict(d) for d in cached_data]
        
        return filtered_data[-limit:] if limit else filtered_data

class RealtimeDataCollector:
    """实时数据收集器"""
    
    def __init__(self, stream_processor: DataStreamProcessor):
        self.stream_processor = stream_processor
        self.collection_tasks = {}
        self.running = False
        self.collection_interval = 5  # 5秒收集一次
    
    async def start_collection(self, symbols: List[str]):
        """开始数据收集"""
        self.running = True
        
        for symbol in symbols:
            task = asyncio.create_task(self._collect_symbol_data(symbol))
            self.collection_tasks[symbol] = task
        
        logger.info(f"开始收集 {len(symbols)} 个股票的数据")
    
    async def stop_collection(self):
        """停止数据收集"""
        self.running = False
        
        for task in self.collection_tasks.values():
            task.cancel()
        
        await asyncio.gather(*self.collection_tasks.values(), return_exceptions=True)
        self.collection_tasks.clear()
        
        logger.info("数据收集已停止")
    
    async def _collect_symbol_data(self, symbol: str):
        """收集单个股票的数据"""
        while self.running:
            try:
                # 获取实时价格数据
                await self._collect_price_data(symbol)
                
                # 获取技术指标数据
                await self._collect_technical_data(symbol)
                
                # 获取AI信号数据
                await self._collect_ai_signal_data(symbol)
                
                await asyncio.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"收集 {symbol} 数据失败: {e}")
                await asyncio.sleep(self.collection_interval)
    
    async def _collect_price_data(self, symbol: str):
        """收集价格数据"""
        try:
            realtime_data = await data_manager.get_realtime_data([symbol])
            if symbol in realtime_data:
                data = realtime_data[symbol]
                
                price_data = RealtimeData(
                    symbol=symbol,
                    data_type=DataStreamType.PRICE,
                    timestamp=datetime.now(),
                    data={
                        'price': data.get('price', 0),
                        'change': data.get('change', 0),
                        'change_percent': data.get('change_percent', 0),
                        'volume': data.get('volume', 0),
                        'market_cap': data.get('market_cap', 0)
                    }
                )
                
                self.stream_processor.add_data(price_data)
                
        except Exception as e:
            logger.error(f"收集 {symbol} 价格数据失败: {e}")
    
    async def _collect_technical_data(self, symbol: str):
        """收集技术指标数据"""
        try:
            # 获取历史数据
            data = await data_manager.get_stock_data(
                symbol=symbol,
                start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            if not data.empty:
                # 计算技术指标
                data_with_indicators = indicators_calculator.calculate_all_indicators(data)
                latest = data_with_indicators.iloc[-1]
                
                technical_data = RealtimeData(
                    symbol=symbol,
                    data_type=DataStreamType.TECHNICAL_INDICATORS,
                    timestamp=datetime.now(),
                    data={
                        'rsi': float(latest.get('RSI_14', 0)),
                        'macd': float(latest.get('MACD', 0)),
                        'bb_position': float(latest.get('BB_Position', 0)),
                        'sma_20': float(latest.get('SMA_20', 0)),
                        'sma_50': float(latest.get('SMA_50', 0))
                    }
                )
                
                self.stream_processor.add_data(technical_data)
                
        except Exception as e:
            logger.error(f"收集 {symbol} 技术指标数据失败: {e}")
    
    async def _collect_ai_signal_data(self, symbol: str):
        """收集AI信号数据"""
        try:
            # 获取历史数据
            data = await data_manager.get_stock_data(
                symbol=symbol,
                start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d")
            )
            
            if not data.empty:
                # 获取AI策略管理器
                strategy_manager = create_ai_strategy_manager()
                
                # 生成AI信号
                signal = await strategy_manager.get_consensus_signal(symbol, data)
                
                ai_signal_data = RealtimeData(
                    symbol=symbol,
                    data_type=DataStreamType.AI_SIGNALS,
                    timestamp=datetime.now(),
                    data={
                        'signal_type': signal.signal_type.value,
                        'confidence': signal.confidence,
                        'target_price': signal.target_price,
                        'stop_loss': signal.stop_loss,
                        'reasoning': signal.reasoning
                    }
                )
                
                self.stream_processor.add_data(ai_signal_data)
                
        except Exception as e:
            logger.error(f"收集 {symbol} AI信号数据失败: {e}")

class WebSocketManager:
    """WebSocket连接管理器"""
    
    def __init__(self, stream_processor: DataStreamProcessor):
        self.stream_processor = stream_processor
        self.connections = set()
        self.connection_subscriptions = defaultdict(set)  # 连接订阅的股票
        self.running = False
    
    async def start_server(self, host: str = "localhost", port: int = 8765):
        """启动WebSocket服务器"""
        self.running = True
        
        async def handle_connection(websocket: WebSocketServerProtocol, path: str):
            """处理WebSocket连接"""
            self.connections.add(websocket)
            logger.info(f"新的WebSocket连接: {websocket.remote_address}")
            
            try:
                async for message in websocket:
                    await self._handle_message(websocket, message)
            except websockets.exceptions.ConnectionClosed:
                logger.info(f"WebSocket连接关闭: {websocket.remote_address}")
            finally:
                self.connections.discard(websocket)
                # 清理订阅
                for symbol in self.connection_subscriptions[websocket]:
                    self.stream_processor.unsubscribe(symbol, websocket)
                self.connection_subscriptions.pop(websocket, None)
        
        server = await websockets.serve(handle_connection, host, port)
        logger.info(f"WebSocket服务器启动: ws://{host}:{port}")
        
        return server
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            message_type = data.get('type')
            
            if message_type == 'subscribe':
                await self._handle_subscribe(websocket, data)
            elif message_type == 'unsubscribe':
                await self._handle_unsubscribe(websocket, data)
            elif message_type == 'ping':
                await self._handle_ping(websocket, data)
            else:
                await self._send_error(websocket, f"未知消息类型: {message_type}")
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "无效的JSON格式")
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {e}")
            await self._send_error(websocket, str(e))
    
    async def _handle_subscribe(self, websocket: WebSocketServerProtocol, data: Dict):
        """处理订阅请求"""
        symbol = data.get('symbol')
        data_types = data.get('data_types', ['price'])
        
        if not symbol:
            await self._send_error(websocket, "缺少股票代码")
            return
        
        # 订阅数据流
        self.stream_processor.subscribe(symbol, websocket)
        self.connection_subscriptions[websocket].add(symbol)
        
        # 发送确认消息
        await self._send_message(websocket, {
            'type': 'subscribe_confirm',
            'symbol': symbol,
            'data_types': data_types,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"订阅 {symbol} 数据流: {websocket.remote_address}")
    
    async def _handle_unsubscribe(self, websocket: WebSocketServerProtocol, data: Dict):
        """处理取消订阅请求"""
        symbol = data.get('symbol')
        
        if not symbol:
            await self._send_error(websocket, "缺少股票代码")
            return
        
        # 取消订阅
        self.stream_processor.unsubscribe(symbol, websocket)
        self.connection_subscriptions[websocket].discard(symbol)
        
        # 发送确认消息
        await self._send_message(websocket, {
            'type': 'unsubscribe_confirm',
            'symbol': symbol,
            'timestamp': datetime.now().isoformat()
        })
        
        logger.info(f"取消订阅 {symbol} 数据流: {websocket.remote_address}")
    
    async def _handle_ping(self, websocket: WebSocketServerProtocol, data: Dict):
        """处理ping请求"""
        await self._send_message(websocket, {
            'type': 'pong',
            'timestamp': datetime.now().isoformat()
        })
    
    async def _send_message(self, websocket: WebSocketServerProtocol, data: Dict):
        """发送消息"""
        try:
            message = json.dumps(data, ensure_ascii=False)
            await websocket.send(message)
        except Exception as e:
            logger.error(f"发送WebSocket消息失败: {e}")
    
    async def _send_error(self, websocket: WebSocketServerProtocol, error_message: str):
        """发送错误消息"""
        await self._send_message(websocket, {
            'type': 'error',
            'message': error_message,
            'timestamp': datetime.now().isoformat()
        })
    
    async def broadcast_data(self, data: RealtimeData):
        """广播数据到所有连接"""
        if not self.connections:
            return
        
        message = {
            'type': 'data_update',
            'symbol': data.symbol,
            'data_type': data.data_type.value,
            'data': data.data,
            'timestamp': data.timestamp.isoformat()
        }
        
        # 并发发送到所有连接
        tasks = []
        for websocket in list(self.connections):
            if websocket and not websocket.closed:
                tasks.append(self._send_message(websocket, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

class RealtimeDataService:
    """实时数据服务"""
    
    def __init__(self):
        self.stream_processor = DataStreamProcessor()
        self.data_collector = RealtimeDataCollector(self.stream_processor)
        self.websocket_manager = WebSocketManager(self.stream_processor)
        self.running = False
    
    async def start(self, symbols: List[str], host: str = "localhost", port: int = 8765):
        """启动实时数据服务"""
        if self.running:
            logger.warning("实时数据服务已在运行")
            return
        
        self.running = True
        
        # 启动数据收集
        await self.data_collector.start_collection(symbols)
        
        # 启动WebSocket服务器
        server = await self.websocket_manager.start_server(host, port)
        
        # 设置数据广播
        self.stream_processor.subscribe = self._create_broadcast_subscriber()
        
        logger.info("实时数据服务已启动")
        
        return server
    
    async def stop(self):
        """停止实时数据服务"""
        if not self.running:
            return
        
        self.running = False
        
        # 停止数据收集
        await self.data_collector.stop_collection()
        
        # 停止数据流处理
        self.stream_processor.stop_processing()
        
        logger.info("实时数据服务已停止")
    
    def _create_broadcast_subscriber(self):
        """创建广播订阅者"""
        async def broadcast_subscriber(data: RealtimeData):
            await self.websocket_manager.broadcast_data(data)
        
        return broadcast_subscriber
    
    def get_cached_data(self, symbol: str, data_type: DataStreamType = None, limit: int = 100) -> List[Dict]:
        """获取缓存数据"""
        return self.stream_processor.get_cached_data(symbol, data_type, limit)
    
    def get_connection_count(self) -> int:
        """获取连接数"""
        return len(self.websocket_manager.connections)

# 创建全局实时数据服务实例
realtime_service = RealtimeDataService()

# 便捷函数
async def start_realtime_service(symbols: List[str], host: str = "localhost", port: int = 8765):
    """启动实时数据服务的便捷函数"""
    return await realtime_service.start(symbols, host, port)

async def stop_realtime_service():
    """停止实时数据服务的便捷函数"""
    await realtime_service.stop()

def get_realtime_data(symbol: str, data_type: DataStreamType = None, limit: int = 100) -> List[Dict]:
    """获取实时数据的便捷函数"""
    return realtime_service.get_cached_data(symbol, data_type, limit)

def get_connection_count() -> int:
    """获取连接数的便捷函数"""
    return realtime_service.get_connection_count()

# WebSocket客户端示例
class RealtimeDataClient:
    """实时数据客户端"""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        self.running = False
        self.data_handlers = {}
    
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            logger.info(f"已连接到 {self.uri}")
            
            # 启动消息处理循环
            asyncio.create_task(self._message_loop())
            
        except Exception as e:
            logger.error(f"连接失败: {e}")
            raise
    
    async def disconnect(self):
        """断开连接"""
        self.running = False
        if self.websocket:
            await self.websocket.close()
        logger.info("连接已断开")
    
    async def subscribe(self, symbol: str, data_types: List[str] = None):
        """订阅数据流"""
        if not self.websocket:
            raise Exception("未连接到服务器")
        
        message = {
            'type': 'subscribe',
            'symbol': symbol,
            'data_types': data_types or ['price']
        }
        
        await self.websocket.send(json.dumps(message))
        logger.info(f"订阅 {symbol} 数据流")
    
    async def unsubscribe(self, symbol: str):
        """取消订阅"""
        if not self.websocket:
            raise Exception("未连接到服务器")
        
        message = {
            'type': 'unsubscribe',
            'symbol': symbol
        }
        
        await self.websocket.send(json.dumps(message))
        logger.info(f"取消订阅 {symbol} 数据流")
    
    async def _message_loop(self):
        """消息处理循环"""
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self._handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            logger.info("服务器连接已关闭")
        except Exception as e:
            logger.error(f"消息处理错误: {e}")
    
    async def _handle_message(self, data: Dict):
        """处理接收到的消息"""
        message_type = data.get('type')
        
        if message_type == 'data_update':
            symbol = data.get('symbol')
            data_type = data.get('data_type')
            
            # 调用相应的处理器
            handler_key = f"{symbol}_{data_type}"
            if handler_key in self.data_handlers:
                await self.data_handlers[handler_key](data)
        
        elif message_type == 'error':
            logger.error(f"服务器错误: {data.get('message')}")
    
    def set_data_handler(self, symbol: str, data_type: str, handler: Callable):
        """设置数据处理函数"""
        handler_key = f"{symbol}_{data_type}"
        self.data_handlers[handler_key] = handler

# 使用示例
async def example_usage():
    """使用示例"""
    # 启动实时数据服务
    symbols = ['AAPL', 'MSFT', 'GOOGL']
    server = await start_realtime_service(symbols)
    
    # 创建客户端
    client = RealtimeDataClient()
    await client.connect()
    
    # 设置数据处理函数
    async def handle_price_data(data):
        print(f"收到价格数据: {data}")
    
    client.set_data_handler('AAPL', 'price', handle_price_data)
    
    # 订阅数据
    await client.subscribe('AAPL', ['price', 'technical_indicators'])
    
    # 运行一段时间
    await asyncio.sleep(60)
    
    # 清理
    await client.disconnect()
    await stop_realtime_service()

if __name__ == "__main__":
    asyncio.run(example_usage())
