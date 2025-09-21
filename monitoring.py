"""
监控和日志系统模块
提供系统监控、错误追踪、性能指标等功能
"""
import logging
import psutil
import time
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
from collections import defaultdict, deque
import threading
import queue

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    load_average: List[float]

@dataclass
class ApplicationMetrics:
    """应用指标"""
    timestamp: datetime
    active_connections: int
    total_requests: int
    error_requests: int
    avg_response_time: float
    ai_api_calls: int
    ai_api_errors: int
    database_queries: int
    cache_hits: int
    cache_misses: int

@dataclass
class ErrorLog:
    """错误日志"""
    timestamp: datetime
    level: str
    module: str
    function: str
    message: str
    traceback: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, collection_interval: int = 60):
        self.collection_interval = collection_interval
        self.running = False
        self.metrics_queue = queue.Queue()
        self.system_metrics_history = deque(maxlen=1440)  # 保留24小时数据
        self.app_metrics_history = deque(maxlen=1440)
        self.error_logs = deque(maxlen=10000)  # 保留10000条错误日志
        
        # 性能计数器
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        
        # 启动收集线程
        self.collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self.collection_thread.start()
    
    def start(self):
        """启动指标收集"""
        self.running = True
        logger.info("指标收集器已启动")
    
    def stop(self):
        """停止指标收集"""
        self.running = False
        logger.info("指标收集器已停止")
    
    def _collection_loop(self):
        """指标收集循环"""
        while True:
            if self.running:
                try:
                    # 收集系统指标
                    system_metrics = self._collect_system_metrics()
                    self.system_metrics_history.append(system_metrics)
                    
                    # 收集应用指标
                    app_metrics = self._collect_application_metrics()
                    self.app_metrics_history.append(app_metrics)
                    
                except Exception as e:
                    logger.error(f"指标收集失败: {e}")
            
            time.sleep(self.collection_interval)
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用情况
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = memory.used / 1024 / 1024
            memory_total_mb = memory.total / 1024 / 1024
            
            # 磁盘使用情况
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / 1024 / 1024 / 1024
            disk_total_gb = disk.total / 1024 / 1024 / 1024
            
            # 网络使用情况
            network = psutil.net_io_counters()
            network_sent_mb = network.bytes_sent / 1024 / 1024
            network_recv_mb = network.bytes_recv / 1024 / 1024
            
            # 负载平均值
            load_average = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                load_average=list(load_average)
            )
            
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
            return SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=0,
                memory_percent=0,
                memory_used_mb=0,
                memory_total_mb=0,
                disk_percent=0,
                disk_used_gb=0,
                disk_total_gb=0,
                network_sent_mb=0,
                network_recv_mb=0,
                load_average=[0, 0, 0]
            )
    
    def _collect_application_metrics(self) -> ApplicationMetrics:
        """收集应用指标"""
        try:
            # 这里可以添加应用特定的指标收集逻辑
            return ApplicationMetrics(
                timestamp=datetime.now(),
                active_connections=self.counters.get('active_connections', 0),
                total_requests=self.counters.get('total_requests', 0),
                error_requests=self.counters.get('error_requests', 0),
                avg_response_time=self._calculate_avg_response_time(),
                ai_api_calls=self.counters.get('ai_api_calls', 0),
                ai_api_errors=self.counters.get('ai_api_errors', 0),
                database_queries=self.counters.get('database_queries', 0),
                cache_hits=self.counters.get('cache_hits', 0),
                cache_misses=self.counters.get('cache_misses', 0)
            )
            
        except Exception as e:
            logger.error(f"收集应用指标失败: {e}")
            return ApplicationMetrics(
                timestamp=datetime.now(),
                active_connections=0,
                total_requests=0,
                error_requests=0,
                avg_response_time=0,
                ai_api_calls=0,
                ai_api_errors=0,
                database_queries=0,
                cache_hits=0,
                cache_misses=0
            )
    
    def _calculate_avg_response_time(self) -> float:
        """计算平均响应时间"""
        if not self.timers.get('response_time'):
            return 0.0
        
        times = self.timers['response_time']
        if len(times) > 100:  # 只保留最近100次
            times = times[-100:]
        
        return sum(times) / len(times) if times else 0.0
    
    def increment_counter(self, name: str, value: int = 1):
        """增加计数器"""
        self.counters[name] += value
    
    def record_timer(self, name: str, duration: float):
        """记录计时器"""
        if name not in self.timers:
            self.timers[name] = []
        
        self.timers[name].append(duration)
        
        # 保持最近1000个记录
        if len(self.timers[name]) > 1000:
            self.timers[name] = self.timers[name][-1000:]
    
    def log_error(self, level: str, module: str, function: str, 
                  message: str, traceback: str = "", 
                  user_id: str = None, request_id: str = None):
        """记录错误日志"""
        error_log = ErrorLog(
            timestamp=datetime.now(),
            level=level,
            module=module,
            function=function,
            message=message,
            traceback=traceback,
            user_id=user_id,
            request_id=request_id
        )
        
        self.error_logs.append(error_log)
        
        # 同时写入日志文件
        logger.error(f"[{module}.{function}] {message}")
    
    def get_system_metrics(self, hours: int = 1) -> List[Dict]:
        """获取系统指标"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            asdict(metric) for metric in self.system_metrics_history
            if metric.timestamp >= cutoff_time
        ]
    
    def get_application_metrics(self, hours: int = 1) -> List[Dict]:
        """获取应用指标"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            asdict(metric) for metric in self.app_metrics_history
            if metric.timestamp >= cutoff_time
        ]
    
    def get_error_logs(self, hours: int = 24) -> List[Dict]:
        """获取错误日志"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            asdict(log) for log in self.error_logs
            if log.timestamp >= cutoff_time
        ]
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            # 获取最新指标
            if not self.system_metrics_history:
                return {"status": "unknown", "message": "无可用指标"}
            
            latest_system = self.system_metrics_history[-1]
            latest_app = self.app_metrics_history[-1] if self.app_metrics_history else None
            
            # 检查系统健康状态
            health_issues = []
            
            # CPU检查
            if latest_system.cpu_percent > 90:
                health_issues.append(f"CPU使用率过高: {latest_system.cpu_percent:.1f}%")
            
            # 内存检查
            if latest_system.memory_percent > 90:
                health_issues.append(f"内存使用率过高: {latest_system.memory_percent:.1f}%")
            
            # 磁盘检查
            if latest_system.disk_percent > 90:
                health_issues.append(f"磁盘使用率过高: {latest_system.disk_percent:.1f}%")
            
            # 应用指标检查
            if latest_app:
                error_rate = 0
                if latest_app.total_requests > 0:
                    error_rate = latest_app.error_requests / latest_app.total_requests
                
                if error_rate > 0.1:  # 错误率超过10%
                    health_issues.append(f"错误率过高: {error_rate:.1%}")
                
                if latest_app.avg_response_time > 5.0:  # 平均响应时间超过5秒
                    health_issues.append(f"响应时间过长: {latest_app.avg_response_time:.2f}秒")
            
            # 确定健康状态
            if not health_issues:
                status = "healthy"
                message = "系统运行正常"
            elif len(health_issues) <= 2:
                status = "warning"
                message = f"系统存在警告: {'; '.join(health_issues)}"
            else:
                status = "critical"
                message = f"系统存在严重问题: {'; '.join(health_issues)}"
            
            return {
                "status": status,
                "message": message,
                "issues": health_issues,
                "timestamp": datetime.now().isoformat(),
                "system_metrics": asdict(latest_system),
                "application_metrics": asdict(latest_app) if latest_app else None
            }
            
        except Exception as e:
            logger.error(f"获取健康状态失败: {e}")
            return {
                "status": "error",
                "message": f"获取健康状态失败: {e}",
                "timestamp": datetime.now().isoformat()
            }

class LogManager:
    """日志管理器"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置日志格式
        self.formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # 设置根日志器
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(logging.INFO)
        
        # 清除现有处理器
        for handler in self.root_logger.handlers[:]:
            self.root_logger.removeHandler(handler)
        
        # 添加文件处理器
        self._setup_file_handlers()
        
        # 添加控制台处理器
        self._setup_console_handler()
    
    def _setup_file_handlers(self):
        """设置文件处理器"""
        # 系统日志
        system_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "system.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        system_handler.setLevel(logging.INFO)
        system_handler.setFormatter(self.formatter)
        self.root_logger.addHandler(system_handler)
        
        # 错误日志
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "error.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self.formatter)
        self.root_logger.addHandler(error_handler)
        
        # AI使用日志
        ai_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "ai_usage.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        ai_handler.setLevel(logging.INFO)
        ai_handler.setFormatter(self.formatter)
        self.root_logger.addHandler(ai_handler)
        
        # 交易日志
        trading_handler = logging.handlers.RotatingFileHandler(
            self.log_dir / "trading.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        trading_handler.setLevel(logging.INFO)
        trading_handler.setFormatter(self.formatter)
        self.root_logger.addHandler(trading_handler)
    
    def _setup_console_handler(self):
        """设置控制台处理器"""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.formatter)
        self.root_logger.addHandler(console_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器"""
        return logging.getLogger(name)
    
    def get_ai_logger(self) -> logging.Logger:
        """获取AI日志器"""
        logger = logging.getLogger("ai_usage")
        logger.setLevel(logging.INFO)
        return logger
    
    def get_trading_logger(self) -> logging.Logger:
        """获取交易日志器"""
        logger = logging.getLogger("trading")
        logger.setLevel(logging.INFO)
        return logger

class AlertManager:
    """告警管理器"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts = []
        self.alert_rules = self._setup_alert_rules()
    
    def _setup_alert_rules(self) -> List[Dict]:
        """设置告警规则"""
        return [
            {
                "name": "high_cpu_usage",
                "condition": lambda metrics: metrics.cpu_percent > 90,
                "message": "CPU使用率过高",
                "severity": "warning"
            },
            {
                "name": "high_memory_usage",
                "condition": lambda metrics: metrics.memory_percent > 90,
                "message": "内存使用率过高",
                "severity": "warning"
            },
            {
                "name": "high_disk_usage",
                "condition": lambda metrics: metrics.disk_percent > 90,
                "message": "磁盘使用率过高",
                "severity": "critical"
            },
            {
                "name": "high_error_rate",
                "condition": lambda metrics: (
                    metrics.total_requests > 0 and 
                    metrics.error_requests / metrics.total_requests > 0.1
                ),
                "message": "错误率过高",
                "severity": "critical"
            }
        ]
    
    def check_alerts(self):
        """检查告警"""
        try:
            if not self.metrics_collector.system_metrics_history:
                return
            
            latest_system = self.metrics_collector.system_metrics_history[-1]
            latest_app = self.metrics_collector.app_metrics_history[-1] if self.metrics_collector.app_metrics_history else None
            
            for rule in self.alert_rules:
                if rule["condition"](latest_system):
                    self._trigger_alert(rule, latest_system)
                elif latest_app and rule["condition"](latest_app):
                    self._trigger_alert(rule, latest_app)
                    
        except Exception as e:
            logger.error(f"检查告警失败: {e}")
    
    def _trigger_alert(self, rule: Dict, metrics: Any):
        """触发告警"""
        alert = {
            "timestamp": datetime.now(),
            "rule_name": rule["name"],
            "message": rule["message"],
            "severity": rule["severity"],
            "metrics": asdict(metrics) if hasattr(metrics, '__dataclass_fields__') else str(metrics)
        }
        
        self.alerts.append(alert)
        
        # 记录告警日志
        logger.warning(f"告警触发: {rule['message']}")
        
        # 这里可以添加发送邮件、短信等通知逻辑
        self._send_notification(alert)
    
    def _send_notification(self, alert: Dict):
        """发送通知"""
        # 这里可以实现发送邮件、短信、钉钉等通知
        logger.info(f"发送告警通知: {alert['message']}")
    
    def get_alerts(self, hours: int = 24) -> List[Dict]:
        """获取告警列表"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts
            if alert["timestamp"] >= cutoff_time
        ]

# 创建全局实例
metrics_collector = MetricsCollector()
log_manager = LogManager()
alert_manager = AlertManager(metrics_collector)

# 启动监控
metrics_collector.start()

# 便捷函数
def get_system_metrics(hours: int = 1) -> List[Dict]:
    """获取系统指标的便捷函数"""
    return metrics_collector.get_system_metrics(hours)

def get_application_metrics(hours: int = 1) -> List[Dict]:
    """获取应用指标的便捷函数"""
    return metrics_collector.get_application_metrics(hours)

def get_health_status() -> Dict[str, Any]:
    """获取健康状态的便捷函数"""
    return metrics_collector.get_health_status()

def get_error_logs(hours: int = 24) -> List[Dict]:
    """获取错误日志的便捷函数"""
    return metrics_collector.get_error_logs(hours)

def get_alerts(hours: int = 24) -> List[Dict]:
    """获取告警列表的便捷函数"""
    return alert_manager.get_alerts(hours)

def increment_counter(name: str, value: int = 1):
    """增加计数器的便捷函数"""
    metrics_collector.increment_counter(name, value)

def record_timer(name: str, duration: float):
    """记录计时器的便捷函数"""
    metrics_collector.record_timer(name, duration)

def log_error(level: str, module: str, function: str, message: str, 
              traceback: str = "", user_id: str = None, request_id: str = None):
    """记录错误日志的便捷函数"""
    metrics_collector.log_error(level, module, function, message, traceback, user_id, request_id)
