"""
数据获取模块 - 支持多级回退机制
支持yfinance、akshare、tushare等数据源
"""
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import yfinance as yf
import akshare as ak
import tushare as ts
from pathlib import Path
import sqlite3
from database import db_manager

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataSource(Enum):
    """数据源枚举"""
    YFINANCE = "yfinance"
    AKSHARE = "akshare"
    TUSHARE = "tushare"
    LOCAL = "local"

@dataclass
class DataConfig:
    """数据配置"""
    primary_source: DataSource = DataSource.AKSHARE
    fallback_sources: List[DataSource] = None
    cache_duration: int = 300  # 缓存时间（秒）
    max_retries: int = 3
    timeout: int = 30
    
    def __post_init__(self):
        if self.fallback_sources is None:
            self.fallback_sources = [DataSource.AKSHARE, DataSource.TUSHARE]

class DataAcquisitionManager:
    """数据获取管理器"""
    
    def __init__(self, config: DataConfig = None):
        self.config = config or DataConfig()
        self.cache = {}
        self.last_update = {}
        
        # 初始化tushare（如果需要）
        self.ts_pro = None
        self._init_tushare()
    
    def _init_tushare(self):
        """初始化tushare"""
        try:
            # 这里需要配置tushare token
            # ts.set_token('your_tushare_token')
            # self.ts_pro = ts.pro_api()
            logger.info("Tushare初始化成功")
        except Exception as e:
            logger.warning(f"Tushare初始化失败: {e}")
    
    async def get_stock_data(
        self, 
        symbol: str, 
        start_date: str = None, 
        end_date: str = None,
        period: str = "1d",
        source: DataSource = None
    ) -> pd.DataFrame:
        """
        获取股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            period: 数据周期 (1d, 1h, 5m等)
            source: 指定数据源
        
        Returns:
            DataFrame: 包含OHLCV数据的DataFrame
        """
        # 设置默认日期
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
        
        # 检查缓存
        cache_key = f"{symbol}_{start_date}_{end_date}_{period}"
        if self._is_cache_valid(cache_key):
            logger.info(f"从缓存获取数据: {symbol}")
            return self.cache[cache_key]
        
        # 尝试从数据库获取
        if source is None or source == DataSource.LOCAL:
            local_data = self._get_from_database(symbol, start_date, end_date)
            if not local_data.empty:
                logger.info(f"从数据库获取数据: {symbol}")
                self._update_cache(cache_key, local_data)
                return local_data
        
        # 智能选择数据源
        if source:
            sources_to_try = [source]
        else:
            # 根据股票代码智能选择数据源
            if symbol.endswith('.SZ') or symbol.endswith('.SH') or symbol.startswith('00') or symbol.startswith('60'):
                # A股只使用AKShare
                sources_to_try = [DataSource.AKSHARE]
            else:
                # 美股使用YFinance
                sources_to_try = [DataSource.YFINANCE]
        
        for data_source in sources_to_try:
            try:
                # 对于A股，跳过YFinance
                if symbol.endswith('.SZ') or symbol.endswith('.SH') or symbol.startswith('00') or symbol.startswith('60'):
                    if data_source == DataSource.YFINANCE:
                        logger.info(f"跳过YFinance，A股使用AKShare: {symbol}")
                        continue
                
                data = await self._fetch_from_source(
                    data_source, symbol, start_date, end_date, period
                )
                if not data.empty:
                    logger.info(f"从{data_source.value}获取数据成功: {symbol}")
                    
                    # 保存到数据库
                    self._save_to_database(symbol, data)
                    
                    # 更新缓存
                    self._update_cache(cache_key, data)
                    
                    return data
                    
            except Exception as e:
                logger.warning(f"从{data_source.value}获取数据失败: {e}")
                continue
        
        logger.error(f"所有数据源都无法获取{symbol}的数据")
        return pd.DataFrame()
    
    async def _fetch_from_source(
        self, 
        source: DataSource, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        period: str
    ) -> pd.DataFrame:
        """从指定数据源获取数据"""
        
        # 对于A股，强制使用AKShare
        if symbol.endswith('.SZ') or symbol.endswith('.SH') or symbol.startswith('00') or symbol.startswith('60'):
            if source == DataSource.YFINANCE:
                logger.info(f"强制使用AKShare获取A股数据: {symbol}")
                return await self._fetch_from_akshare(symbol, start_date, end_date, period)
        
        if source == DataSource.YFINANCE:
            return await self._fetch_from_yfinance(symbol, start_date, end_date, period)
        elif source == DataSource.AKSHARE:
            return await self._fetch_from_akshare(symbol, start_date, end_date, period)
        elif source == DataSource.TUSHARE:
            return await self._fetch_from_tushare(symbol, start_date, end_date, period)
        else:
            raise ValueError(f"不支持的数据源: {source}")
    
    async def _fetch_from_yfinance(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        period: str
    ) -> pd.DataFrame:
        """从yfinance获取数据 - 已禁用，只用于美股"""
        # 对于A股，直接返回空数据，避免调用YFinance
        if symbol.endswith('.SZ') or symbol.endswith('.SH') or symbol.startswith('00') or symbol.startswith('60'):
            logger.info(f"YFinance已禁用，A股使用AKShare: {symbol}")
            return pd.DataFrame()
        
        import time
        
        for attempt in range(self.config.max_retries):
            try:
                # 检查是否被限流
                if "Too Many Requests" in str(self.cache.get('last_error', '')):
                    wait_time = (attempt + 1) * 10  # 递增等待时间
                    logger.warning(f"YFinance被限流，等待{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=start_date, end=end_date, interval=period)
                
                if data.empty:
                    logger.warning(f"YFinance返回空数据: {symbol}")
                    return pd.DataFrame()
                
                # 标准化列名
                data = data.rename(columns={
                    'Open': 'open',
                    'High': 'high', 
                    'Low': 'low',
                    'Close': 'close',
                    'Volume': 'volume'
                })
                
                # 添加股票代码
                data['symbol'] = symbol
                data['date'] = data.index
                
                # 清除错误缓存
                if 'last_error' in self.cache:
                    del self.cache['last_error']
                
                return data.reset_index(drop=True)
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"YFinance获取数据失败 (尝试 {attempt + 1}/{self.config.max_retries}): {error_msg}")
                
                # 缓存错误信息
                self.cache['last_error'] = error_msg
                
                # 如果是限流错误，等待更长时间
                if "Too Many Requests" in error_msg or "Rate limited" in error_msg:
                    wait_time = (attempt + 1) * 30  # 限流时等待更长时间
                    logger.warning(f"检测到限流，等待{wait_time}秒...")
                    await asyncio.sleep(wait_time)
                elif attempt < self.config.max_retries - 1:
                    # 其他错误，短暂等待后重试
                    await asyncio.sleep(2)
                
                if attempt == self.config.max_retries - 1:
                    logger.error(f"YFinance获取数据最终失败: {symbol}")
                    return pd.DataFrame()
    
    async def _fetch_from_akshare(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        period: str
    ) -> pd.DataFrame:
        """从akshare获取数据"""
        try:
            # 处理A股代码格式
            if symbol.endswith('.SZ') or symbol.endswith('.SH'):
                # 去掉后缀，AKShare需要纯数字代码
                clean_symbol = symbol.split('.')[0]
            else:
                clean_symbol = symbol
            
            logger.info(f"AKShare获取A股数据: {symbol} -> {clean_symbol}")
            
            # 根据周期选择不同的函数
            if period == "1d":
                # 使用AKShare的A股历史数据接口
                data = ak.stock_zh_a_hist(
                    symbol=clean_symbol,
                    period="daily",
                    start_date=start_date.replace("-", "") if start_date else None,
                    end_date=end_date.replace("-", "") if end_date else None,
                    adjust="qfq"  # 前复权
                )
            elif period == "1h":
                # 分钟级数据
                data = ak.stock_zh_a_hist_min_em(
                    symbol=clean_symbol,
                    period="1",
                    start_date=start_date.replace("-", "") if start_date else None,
                    end_date=end_date.replace("-", "") if end_date else None,
                    adjust="qfq"
                )
            else:
                logger.warning(f"AKShare不支持周期: {period}")
                return pd.DataFrame()
            
            if data.empty:
                logger.warning(f"AKShare返回空数据: {symbol}")
                return pd.DataFrame()
            
            # 标准化列名
            data = data.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '最高': 'high',
                '最低': 'low', 
                '收盘': 'close',
                '成交量': 'volume'
            })
            
            # 添加股票代码
            data['symbol'] = symbol
            data['date'] = pd.to_datetime(data['date'])
            
            # 确保数据类型正确
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in data.columns:
                    data[col] = pd.to_numeric(data[col], errors='coerce')
            
            # 删除空值行
            data = data.dropna()
            
            logger.info(f"AKShare成功获取 {symbol} 数据: {len(data)} 条记录")
            return data[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"AKShare获取数据失败: {e}")
            return pd.DataFrame()
    
    async def _fetch_from_tushare(
        self, 
        symbol: str, 
        start_date: str, 
        end_date: str, 
        period: str
    ) -> pd.DataFrame:
        """从tushare获取数据"""
        try:
            if self.ts_pro is None:
                logger.warning("Tushare未初始化")
                return pd.DataFrame()
            
            # 根据周期选择不同的函数
            if period == "1d":
                data = self.ts_pro.daily(
                    ts_code=symbol,
                    start_date=start_date.replace("-", ""),
                    end_date=end_date.replace("-", "")
                )
            else:
                logger.warning(f"Tushare不支持周期: {period}")
                return pd.DataFrame()
            
            if data.empty:
                return pd.DataFrame()
            
            # 标准化列名
            data = data.rename(columns={
                'trade_date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'vol': 'volume'
            })
            
            # 添加股票代码
            data['symbol'] = symbol
            data['date'] = pd.to_datetime(data['date'])
            
            return data[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            logger.error(f"Tushare获取数据失败: {e}")
            return pd.DataFrame()
    
    def _get_from_database(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从数据库获取数据"""
        try:
            return db_manager.get_kline_data(symbol, start_date, end_date)
        except Exception as e:
            logger.warning(f"从数据库获取数据失败: {e}")
            return pd.DataFrame()
    
    def _save_to_database(self, symbol: str, data: pd.DataFrame):
        """保存数据到数据库"""
        try:
            for _, row in data.iterrows():
                # 确保日期是字符串格式
                date_str = str(row['date']).split(' ')[0]  # 只取日期部分
                db_manager.add_kline_data(
                    symbol=symbol,
                    date=date_str,
                    open_price=float(row['open']),
                    high_price=float(row['high']),
                    low_price=float(row['low']),
                    close_price=float(row['close']),
                    volume=int(row['volume'])
                )
        except Exception as e:
            logger.warning(f"保存数据到数据库失败: {e}")
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.cache:
            return False
        
        if cache_key not in self.last_update:
            return False
        
        elapsed = (datetime.now() - self.last_update[cache_key]).total_seconds()
        return elapsed < self.config.cache_duration
    
    def _update_cache(self, cache_key: str, data: pd.DataFrame):
        """更新缓存"""
        self.cache[cache_key] = data.copy()
        self.last_update[cache_key] = datetime.now()
    
    async def get_market_data(
        self, 
        symbols: List[str], 
        start_date: str = None, 
        end_date: str = None,
        period: str = "1d"
    ) -> Dict[str, pd.DataFrame]:
        """批量获取多只股票数据"""
        tasks = []
        for symbol in symbols:
            task = self.get_stock_data(symbol, start_date, end_date, period)
            tasks.append((symbol, task))
        
        results = {}
        for symbol, task in tasks:
            try:
                data = await task
                results[symbol] = data
            except Exception as e:
                logger.error(f"获取{symbol}数据失败: {e}")
                results[symbol] = pd.DataFrame()
        
        return results
    
    async def get_realtime_data(self, symbols: List[str]) -> Dict[str, Dict]:
        """获取实时数据"""
        results = {}
        
        for symbol in symbols:
            try:
                # 使用yfinance获取实时数据
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                results[symbol] = {
                    'symbol': symbol,
                    'price': info.get('currentPrice', 0),
                    'change': info.get('regularMarketChange', 0),
                    'change_percent': info.get('regularMarketChangePercent', 0),
                    'volume': info.get('volume', 0),
                    'market_cap': info.get('marketCap', 0),
                    'timestamp': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"获取{symbol}实时数据失败: {e}")
                results[symbol] = {
                    'symbol': symbol,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return results

# 创建全局数据获取管理器实例
data_manager = DataAcquisitionManager()

# 便捷函数
async def get_stock_data(symbol: str, **kwargs) -> pd.DataFrame:
    """获取股票数据的便捷函数"""
    return await data_manager.get_stock_data(symbol, **kwargs)

async def get_market_data(symbols: List[str], **kwargs) -> Dict[str, pd.DataFrame]:
    """批量获取股票数据的便捷函数"""
    return await data_manager.get_market_data(symbols, **kwargs)

async def get_realtime_data(symbols: List[str]) -> Dict[str, Dict]:
    """获取实时数据的便捷函数"""
    return await data_manager.get_realtime_data(symbols)
