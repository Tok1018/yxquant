"""
性能优化模块
提供数据库索引、缓存机制、并发处理等性能优化功能
"""
import asyncio
import time
import functools
import threading
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
import sqlite3
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing
import psutil
import gc
import weakref
from collections import OrderedDict
import hashlib
import pickle
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    """缓存配置"""
    max_size: int = 1000
    ttl_seconds: int = 3600  # 1小时
    cleanup_interval: int = 300  # 5分钟
    enable_memory_cache: bool = True
    enable_disk_cache: bool = True
    cache_dir: str = "cache"

@dataclass
class PerformanceMetrics:
    """性能指标"""
    function_name: str
    call_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    memory_usage: float
    last_called: datetime

class LRUCache:
    """LRU缓存实现"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.cache = OrderedDict()
        self.timestamps = {}
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self.lock:
            if key not in self.cache:
                return None
            
            # 检查是否过期
            if time.time() - self.timestamps[key] > self.ttl_seconds:
                del self.cache[key]
                del self.timestamps[key]
                return None
            
            # 移动到末尾（最近使用）
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        with self.lock:
            # 如果键已存在，先删除
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
            
            # 如果缓存已满，删除最旧的项
            while len(self.cache) >= self.max_size:
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                del self.timestamps[oldest_key]
            
            # 添加新项
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def delete(self, key: str) -> None:
        """删除缓存项"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                del self.timestamps[key]
    
    def clear(self) -> None:
        """清空缓存"""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def size(self) -> int:
        """获取缓存大小"""
        with self.lock:
            return len(self.cache)
    
    def cleanup_expired(self) -> int:
        """清理过期项"""
        with self.lock:
            current_time = time.time()
            expired_keys = [
                key for key, timestamp in self.timestamps.items()
                if current_time - timestamp > self.ttl_seconds
            ]
            
            for key in expired_keys:
                del self.cache[key]
                del self.timestamps[key]
            
            return len(expired_keys)

class MemoryCache:
    """内存缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache = LRUCache(config.max_size, config.ttl_seconds)
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        return self.cache.get(key)
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        self.cache.set(key, value)
    
    def delete(self, key: str) -> None:
        """删除缓存项"""
        self.cache.delete(key)
    
    def clear(self) -> None:
        """清空缓存"""
        self.cache.clear()
    
    def _cleanup_loop(self):
        """清理循环"""
        while True:
            try:
                time.sleep(self.config.cleanup_interval)
                expired_count = self.cache.cleanup_expired()
                if expired_count > 0:
                    logger.debug(f"清理了 {expired_count} 个过期缓存项")
            except Exception as e:
                logger.error(f"缓存清理失败: {e}")

class DiskCache:
    """磁盘缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.cache_dir = Path(config.cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """加载元数据"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载缓存元数据失败: {e}")
        return {}
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f)
        except Exception as e:
            logger.error(f"保存缓存元数据失败: {e}")
    
    def _get_cache_path(self, key: str) -> Path:
        """获取缓存文件路径"""
        # 使用哈希避免文件名冲突
        hash_key = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{hash_key}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        try:
            cache_path = self._get_cache_path(key)
            if not cache_path.exists():
                return None
            
            # 检查是否过期
            if key in self.metadata:
                if time.time() - self.metadata[key]['timestamp'] > self.config.ttl_seconds:
                    self.delete(key)
                    return None
            
            # 加载缓存数据
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
                
        except Exception as e:
            logger.error(f"读取磁盘缓存失败: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        try:
            cache_path = self._get_cache_path(key)
            
            # 保存数据
            with open(cache_path, 'wb') as f:
                pickle.dump(value, f)
            
            # 更新元数据
            self.metadata[key] = {
                'timestamp': time.time(),
                'size': cache_path.stat().st_size
            }
            self._save_metadata()
            
        except Exception as e:
            logger.error(f"保存磁盘缓存失败: {e}")
    
    def delete(self, key: str) -> None:
        """删除缓存项"""
        try:
            cache_path = self._get_cache_path(key)
            if cache_path.exists():
                cache_path.unlink()
            
            if key in self.metadata:
                del self.metadata[key]
                self._save_metadata()
                
        except Exception as e:
            logger.error(f"删除磁盘缓存失败: {e}")
    
    def cleanup_expired(self) -> int:
        """清理过期项"""
        current_time = time.time()
        expired_keys = []
        
        for key, metadata in self.metadata.items():
            if current_time - metadata['timestamp'] > self.config.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            self.delete(key)
        
        return len(expired_keys)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.memory_cache = MemoryCache(config) if config.enable_memory_cache else None
        self.disk_cache = DiskCache(config) if config.enable_disk_cache else None
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        # 先尝试内存缓存
        if self.memory_cache:
            value = self.memory_cache.get(key)
            if value is not None:
                return value
        
        # 再尝试磁盘缓存
        if self.disk_cache:
            value = self.disk_cache.get(key)
            if value is not None:
                # 将磁盘缓存加载到内存缓存
                if self.memory_cache:
                    self.memory_cache.set(key, value)
                return value
        
        return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存值"""
        # 设置内存缓存
        if self.memory_cache:
            self.memory_cache.set(key, value)
        
        # 设置磁盘缓存
        if self.disk_cache:
            self.disk_cache.set(key, value)
    
    def delete(self, key: str) -> None:
        """删除缓存项"""
        if self.memory_cache:
            self.memory_cache.delete(key)
        if self.disk_cache:
            self.disk_cache.delete(key)
    
    def clear(self) -> None:
        """清空缓存"""
        if self.memory_cache:
            self.memory_cache.clear()
        if self.disk_cache:
            # 清空磁盘缓存目录
            for file in self.disk_cache.cache_dir.glob("*.cache"):
                file.unlink()
            self.disk_cache.metadata.clear()
            self.disk_cache._save_metadata()

class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.metrics = {}
        self.lock = threading.RLock()
    
    def profile(self, func: Callable) -> Callable:
        """性能分析装饰器"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.time()
                end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
                
                duration = end_time - start_time
                memory_usage = end_memory - start_memory
                
                self._record_metrics(func.__name__, duration, memory_usage)
        
        return wrapper
    
    def _record_metrics(self, function_name: str, duration: float, memory_usage: float):
        """记录性能指标"""
        with self.lock:
            if function_name not in self.metrics:
                self.metrics[function_name] = PerformanceMetrics(
                    function_name=function_name,
                    call_count=0,
                    total_time=0.0,
                    avg_time=0.0,
                    min_time=float('inf'),
                    max_time=0.0,
                    memory_usage=0.0,
                    last_called=datetime.now()
                )
            
            metrics = self.metrics[function_name]
            metrics.call_count += 1
            metrics.total_time += duration
            metrics.avg_time = metrics.total_time / metrics.call_count
            metrics.min_time = min(metrics.min_time, duration)
            metrics.max_time = max(metrics.max_time, duration)
            metrics.memory_usage = max(metrics.memory_usage, memory_usage)
            metrics.last_called = datetime.now()
    
    def get_metrics(self, function_name: str = None) -> Union[Dict, PerformanceMetrics]:
        """获取性能指标"""
        with self.lock:
            if function_name:
                return self.metrics.get(function_name)
            return dict(self.metrics)
    
    def get_slowest_functions(self, limit: int = 10) -> List[PerformanceMetrics]:
        """获取最慢的函数"""
        with self.lock:
            return sorted(
                self.metrics.values(),
                key=lambda x: x.avg_time,
                reverse=True
            )[:limit]

class DatabaseOptimizer:
    """数据库优化器"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.connection = None
        self._setup_connection()
    
    def _setup_connection(self):
        """设置数据库连接"""
        self.connection = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=NORMAL")
        self.connection.execute("PRAGMA cache_size=10000")
        self.connection.execute("PRAGMA temp_store=MEMORY")
    
    def create_indexes(self):
        """创建索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_kline_symbol_date ON kline_data(symbol, date)",
            "CREATE INDEX IF NOT EXISTS idx_kline_date ON kline_data(date)",
            "CREATE INDEX IF NOT EXISTS idx_ai_analysis_symbol ON ai_analysis(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_ai_analysis_timestamp ON ai_analysis(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)",
            "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_watchlist_symbol ON watchlist(symbol)"
        ]
        
        for index_sql in indexes:
            try:
                self.connection.execute(index_sql)
                logger.info(f"创建索引成功: {index_sql}")
            except Exception as e:
                logger.error(f"创建索引失败: {index_sql}, 错误: {e}")
        
        self.connection.commit()
    
    def analyze_tables(self):
        """分析表统计信息"""
        try:
            self.connection.execute("ANALYZE")
            self.connection.commit()
            logger.info("表分析完成")
        except Exception as e:
            logger.error(f"表分析失败: {e}")
    
    def vacuum_database(self):
        """压缩数据库"""
        try:
            self.connection.execute("VACUUM")
            logger.info("数据库压缩完成")
        except Exception as e:
            logger.error(f"数据库压缩失败: {e}")
    
    def get_table_info(self) -> Dict[str, Any]:
        """获取表信息"""
        try:
            cursor = self.connection.cursor()
            
            # 获取表列表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_info = {}
            for table in tables:
                # 获取行数
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                # 获取表大小
                cursor.execute(f"SELECT COUNT(*) FROM pragma_table_info('{table}')")
                column_count = cursor.fetchone()[0]
                
                table_info[table] = {
                    'row_count': row_count,
                    'column_count': column_count
                }
            
            return table_info
            
        except Exception as e:
            logger.error(f"获取表信息失败: {e}")
            return {}
    
    def optimize_queries(self):
        """优化查询"""
        # 创建索引
        self.create_indexes()
        
        # 分析表
        self.analyze_tables()
        
        # 压缩数据库
        self.vacuum_database()
        
        logger.info("数据库优化完成")

class ConcurrencyManager:
    """并发管理器"""
    
    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=self.max_workers)
    
    def run_in_thread(self, func: Callable, *args, **kwargs):
        """在线程池中运行函数"""
        return self.thread_pool.submit(func, *args, **kwargs)
    
    def run_in_process(self, func: Callable, *args, **kwargs):
        """在进程池中运行函数"""
        return self.process_pool.submit(func, *args, **kwargs)
    
    async def run_async(self, func: Callable, *args, **kwargs):
        """异步运行函数"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self.thread_pool, func, *args, **kwargs)
    
    def shutdown(self):
        """关闭线程池和进程池"""
        self.thread_pool.shutdown(wait=True)
        self.process_pool.shutdown(wait=True)

class MemoryManager:
    """内存管理器"""
    
    def __init__(self):
        self.memory_threshold = 0.8  # 80%内存使用率阈值
        self.cleanup_interval = 300  # 5分钟清理一次
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
    
    def _cleanup_loop(self):
        """内存清理循环"""
        while True:
            try:
                time.sleep(self.cleanup_interval)
                self.cleanup_memory()
            except Exception as e:
                logger.error(f"内存清理失败: {e}")
    
    def cleanup_memory(self):
        """清理内存"""
        try:
            # 强制垃圾回收
            collected = gc.collect()
            
            # 获取内存使用情况
            memory_percent = psutil.virtual_memory().percent / 100
            
            if memory_percent > self.memory_threshold:
                logger.warning(f"内存使用率过高: {memory_percent:.1%}, 已清理 {collected} 个对象")
            else:
                logger.debug(f"内存清理完成, 清理了 {collected} 个对象")
                
        except Exception as e:
            logger.error(f"内存清理失败: {e}")
    
    def get_memory_usage(self) -> Dict[str, float]:
        """获取内存使用情况"""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            system_memory = psutil.virtual_memory()
            
            return {
                'process_memory_mb': memory_info.rss / 1024 / 1024,
                'process_memory_percent': process.memory_percent(),
                'system_memory_percent': system_memory.percent,
                'available_memory_mb': system_memory.available / 1024 / 1024
            }
        except Exception as e:
            logger.error(f"获取内存使用情况失败: {e}")
            return {}

# 创建全局实例
cache_config = CacheConfig()
cache_manager = CacheManager(cache_config)
profiler = PerformanceProfiler()
concurrency_manager = ConcurrencyManager()
memory_manager = MemoryManager()

# 便捷函数
def cached(ttl_seconds: int = 3600):
    """缓存装饰器"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # 尝试从缓存获取
            result = cache_manager.get(key)
            if result is not None:
                return result
            
            # 执行函数并缓存结果
            result = func(*args, **kwargs)
            cache_manager.set(key, result)
            return result
        
        return wrapper
    return decorator

def profile_performance(func):
    """性能分析装饰器"""
    return profiler.profile(func)

def run_async(func, *args, **kwargs):
    """异步运行函数"""
    return concurrency_manager.run_async(func, *args, **kwargs)

def optimize_database(db_path: str):
    """优化数据库"""
    optimizer = DatabaseOptimizer(db_path)
    optimizer.optimize_queries()

def get_performance_metrics():
    """获取性能指标"""
    return profiler.get_metrics()

def get_memory_usage():
    """获取内存使用情况"""
    return memory_manager.get_memory_usage()

def cleanup_memory():
    """清理内存"""
    memory_manager.cleanup_memory()
