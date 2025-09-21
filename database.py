"""
数据库管理模块
"""
import sqlite3
import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from config import DATABASE_PATH, DATA_DIR
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理类"""
    
    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE_PATH
        self.init_database()
    
    def init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 股票基本信息表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks (
                    symbol TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    industry TEXT,
                    market TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 自选股表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT,
                    FOREIGN KEY (symbol) REFERENCES stocks (symbol)
                )
            ''')
            
            # K线数据表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kline_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    open REAL NOT NULL,
                    high REAL NOT NULL,
                    low REAL NOT NULL,
                    close REAL NOT NULL,
                    volume INTEGER NOT NULL,
                    amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            ''')
            
            # 技术指标表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS technical_indicators (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    ma5 REAL,
                    ma10 REAL,
                    ma20 REAL,
                    ma30 REAL,
                    ma60 REAL,
                    ma120 REAL,
                    ma250 REAL,
                    macd REAL,
                    macd_signal REAL,
                    macd_histogram REAL,
                    kdj_k REAL,
                    kdj_d REAL,
                    kdj_j REAL,
                    cci REAL,
                    boll_upper REAL,
                    boll_middle REAL,
                    boll_lower REAL,
                    rsi REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol, date)
                )
            ''')
            
            # 策略配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS strategy_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 交易记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    trade_type TEXT NOT NULL,  -- 'buy' or 'sell'
                    quantity INTEGER NOT NULL,
                    price REAL NOT NULL,
                    amount REAL NOT NULL,
                    commission REAL DEFAULT 0,
                    slippage REAL DEFAULT 0,
                    strategy_name TEXT,
                    trade_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                )
            ''')
            
            # 持仓表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    avg_price REAL NOT NULL,
                    current_price REAL,
                    market_value REAL,
                    unrealized_pnl REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(symbol)
                )
            ''')
            
            # 回测结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    initial_capital REAL NOT NULL,
                    final_capital REAL NOT NULL,
                    total_return REAL NOT NULL,
                    annual_return REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    sharpe_ratio REAL,
                    win_rate REAL,
                    total_trades INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # AI分析结果表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    analysis_type TEXT NOT NULL,  -- 'sentiment', 'signal', 'risk', 'optimization'
                    model_used TEXT NOT NULL,
                    input_data TEXT,  -- JSON格式的输入数据
                    analysis_result TEXT NOT NULL,  -- JSON格式的分析结果
                    confidence_score REAL,
                    processing_time REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # AI使用统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_usage_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    request_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    tokens_used INTEGER DEFAULT 0,
                    cost REAL DEFAULT 0.0,
                    response_time REAL,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # AI策略配置表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_strategy_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    ai_model TEXT NOT NULL,
                    parameters TEXT NOT NULL,  -- JSON格式参数
                    is_active BOOLEAN DEFAULT 1,
                    performance_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("数据库初始化完成")
    
    def add_stock(self, symbol, name, industry=None, market=None):
        """添加股票信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO stocks (symbol, name, industry, market, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (symbol, name, industry, market, datetime.now()))
            conn.commit()
            logger.info(f"添加股票: {symbol} - {name}")
    
    def add_to_watchlist(self, symbol, notes=None):
        """添加自选股"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 检查是否已存在
            cursor.execute('SELECT id FROM watchlist WHERE symbol = ?', (symbol,))
            if cursor.fetchone():
                logger.warning(f"股票 {symbol} 已在自选股中")
                return False
            
            cursor.execute('''
                INSERT INTO watchlist (symbol, notes)
                VALUES (?, ?)
            ''', (symbol, notes))
            conn.commit()
            logger.info(f"添加自选股: {symbol}")
            return True
    
    def remove_from_watchlist(self, symbol):
        """从自选股中移除"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM watchlist WHERE symbol = ?', (symbol,))
            conn.commit()
            logger.info(f"移除自选股: {symbol}")
    
    def get_watchlist(self):
        """获取自选股列表"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT w.symbol, s.name, s.industry, s.market, w.added_at, w.notes
                FROM watchlist w
                JOIN stocks s ON w.symbol = s.symbol
                ORDER BY w.added_at DESC
            '''
            return pd.read_sql_query(query, conn)
    
    def get_all_stocks(self):
        """获取所有股票列表"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT symbol, name, industry, market, is_active, created_at, updated_at
                FROM stocks
                ORDER BY symbol
            '''
            return pd.read_sql_query(query, conn)
    
    def add_kline_data(self, symbol, date, open_price, high_price, low_price, close_price, volume, amount=None):
        """添加单条K线数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO kline_data 
                (symbol, date, open, high, low, close, volume, amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, date, open_price, high_price, low_price, close_price, volume, amount))
            conn.commit()
    
    def save_kline_data(self, symbol, data):
        """保存K线数据"""
        with sqlite3.connect(self.db_path) as conn:
            data['symbol'] = symbol
            data.to_sql('kline_data', conn, if_exists='append', index=False, method='multi')
            logger.info(f"保存K线数据: {symbol}, 共 {len(data)} 条记录")
    
    def get_kline_data(self, symbol, start_date=None, end_date=None):
        """获取K线数据"""
        with sqlite3.connect(self.db_path) as conn:
            query = '''
                SELECT * FROM kline_data 
                WHERE symbol = ?
            '''
            params = [symbol]
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            query += " ORDER BY date"
            
            return pd.read_sql_query(query, conn, params=params)
    
    def save_technical_indicators(self, symbol, data):
        """保存技术指标数据"""
        with sqlite3.connect(self.db_path) as conn:
            data['symbol'] = symbol
            data.to_sql('technical_indicators', conn, if_exists='append', index=False, method='multi')
            logger.info(f"保存技术指标: {symbol}, 共 {len(data)} 条记录")
    
    def get_technical_indicators(self, symbol, start_date=None, end_date=None):
        """获取技术指标数据"""
        with sqlite3.connect(self.db_path) as conn:
            query = f'''
                SELECT * FROM technical_indicators 
                WHERE symbol = '{symbol}'
            '''
            if start_date:
                query += f" AND date >= '{start_date}'"
            if end_date:
                query += f" AND date <= '{end_date}'"
            query += " ORDER BY date"
            
            return pd.read_sql_query(query, conn)
    
    def save_trade(self, symbol, trade_type, quantity, price, strategy_name=None, notes=None):
        """保存交易记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            amount = quantity * price
            cursor.execute('''
                INSERT INTO trades (symbol, trade_type, quantity, price, amount, strategy_name, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, trade_type, quantity, price, amount, strategy_name, notes))
            conn.commit()
            logger.info(f"保存交易记录: {symbol} {trade_type} {quantity}股 @{price}")
    
    def get_trades(self, symbol=None, start_date=None, end_date=None):
        """获取交易记录"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if start_date:
                query += " AND trade_date >= ?"
                params.append(start_date)
            if end_date:
                query += " AND trade_date <= ?"
                params.append(end_date)
            
            query += " ORDER BY trade_date DESC"
            
            return pd.read_sql_query(query, conn, params=params)
    
    def save_ai_analysis(self, symbol, analysis_type, model_used, input_data, analysis_result, 
                        confidence_score=None, processing_time=None):
        """保存AI分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_analysis_results 
                (symbol, analysis_type, model_used, input_data, analysis_result, 
                 confidence_score, processing_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, analysis_type, model_used, 
                  json.dumps(input_data) if input_data else None,
                  json.dumps(analysis_result), confidence_score, processing_time))
            conn.commit()
            logger.info(f"保存AI分析结果: {symbol} - {analysis_type}")
    
    def get_ai_analysis(self, symbol=None, analysis_type=None, start_date=None, end_date=None):
        """获取AI分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM ai_analysis_results WHERE 1=1"
            params = []
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if analysis_type:
                query += " AND analysis_type = ?"
                params.append(analysis_type)
            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)
            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC"
            
            return pd.read_sql_query(query, conn, params=params)
    
    def save_ai_usage_stats(self, model_name, request_type, success, tokens_used=0, 
                           cost=0.0, response_time=None, error_message=None):
        """保存AI使用统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ai_usage_stats 
                (model_name, request_type, success, tokens_used, cost, response_time, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (model_name, request_type, success, tokens_used, cost, response_time, error_message))
            conn.commit()
    
    def get_ai_usage_stats(self, model_name=None, start_date=None, end_date=None):
        """获取AI使用统计"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM ai_usage_stats WHERE 1=1"
            params = []
            
            if model_name:
                query += " AND model_name = ?"
                params.append(model_name)
            if start_date:
                query += " AND created_at >= ?"
                params.append(start_date)
            if end_date:
                query += " AND created_at <= ?"
                params.append(end_date)
            
            query += " ORDER BY created_at DESC"
            
            return pd.read_sql_query(query, conn, params=params)
    
    def save_ai_strategy_config(self, strategy_name, ai_model, parameters, performance_score=None):
        """保存AI策略配置"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO ai_strategy_config 
                (strategy_name, ai_model, parameters, performance_score, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (strategy_name, ai_model, json.dumps(parameters), performance_score, datetime.now()))
            conn.commit()
            logger.info(f"保存AI策略配置: {strategy_name}")
    
    def get_ai_strategy_config(self, strategy_name=None):
        """获取AI策略配置"""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM ai_strategy_config WHERE 1=1"
            params = []
            
            if strategy_name:
                query += " AND strategy_name = ?"
                params.append(strategy_name)
            
            query += " ORDER BY updated_at DESC"
            
            return pd.read_sql_query(query, conn, params=params)

# 创建数据库管理器实例
db_manager = DatabaseManager()
