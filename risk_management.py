"""
风险管理模块
提供投资组合风险分析、预警和控制功能
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import logging
import json

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskType(Enum):
    """风险类型"""
    MARKET = "market"  # 市场风险
    CONCENTRATION = "concentration"  # 集中度风险
    LIQUIDITY = "liquidity"  # 流动性风险
    VOLATILITY = "volatility"  # 波动性风险
    DRAWDOWN = "drawdown"  # 回撤风险
    CORRELATION = "correlation"  # 相关性风险

@dataclass
class RiskMetric:
    """风险指标"""
    name: str
    value: float
    threshold: float
    level: RiskLevel
    description: str
    recommendation: str

@dataclass
class RiskAlert:
    """风险预警"""
    risk_type: RiskType
    level: RiskLevel
    message: str
    timestamp: datetime
    symbol: Optional[str] = None
    value: Optional[float] = None
    threshold: Optional[float] = None

@dataclass
class PortfolioRisk:
    """投资组合风险分析结果"""
    portfolio_value: float
    risk_metrics: List[RiskMetric]
    alerts: List[RiskAlert]
    overall_risk_level: RiskLevel
    risk_score: float  # 0-100
    recommendations: List[str]
    timestamp: datetime

class RiskManager:
    """风险管理器"""
    
    def __init__(self):
        self.risk_thresholds = {
            "max_position_size": 0.1,  # 单股最大仓位
            "max_total_position": 0.95,  # 总仓位上限
            "max_drawdown": 0.15,  # 最大回撤
            "max_volatility": 0.3,  # 最大波动率
            "min_liquidity": 1000000,  # 最小流动性（成交额）
            "max_correlation": 0.8,  # 最大相关性
            "var_confidence": 0.95,  # VaR置信度
            "var_horizon": 1  # VaR时间跨度（天）
        }
    
    def analyze_portfolio_risk(self, 
                             positions: Dict[str, float], 
                             prices: Dict[str, pd.DataFrame],
                             portfolio_value: float) -> PortfolioRisk:
        """分析投资组合风险"""
        try:
            risk_metrics = []
            alerts = []
            
            # 1. 集中度风险分析
            concentration_metrics = self._analyze_concentration_risk(positions, portfolio_value)
            risk_metrics.extend(concentration_metrics)
            
            # 2. 波动性风险分析
            volatility_metrics = self._analyze_volatility_risk(positions, prices)
            risk_metrics.extend(volatility_metrics)
            
            # 3. 回撤风险分析
            drawdown_metrics = self._analyze_drawdown_risk(positions, prices)
            risk_metrics.extend(drawdown_metrics)
            
            # 4. 流动性风险分析
            liquidity_metrics = self._analyze_liquidity_risk(positions, prices)
            risk_metrics.extend(liquidity_metrics)
            
            # 5. 相关性风险分析
            correlation_metrics = self._analyze_correlation_risk(positions, prices)
            risk_metrics.extend(correlation_metrics)
            
            # 6. VaR计算
            var_metrics = self._calculate_var(positions, prices, portfolio_value)
            risk_metrics.extend(var_metrics)
            
            # 生成预警
            alerts = self._generate_alerts(risk_metrics)
            
            # 计算整体风险等级和分数
            overall_risk_level, risk_score = self._calculate_overall_risk(risk_metrics)
            
            # 生成建议
            recommendations = self._generate_recommendations(risk_metrics, alerts)
            
            return PortfolioRisk(
                portfolio_value=portfolio_value,
                risk_metrics=risk_metrics,
                alerts=alerts,
                overall_risk_level=overall_risk_level,
                risk_score=risk_score,
                recommendations=recommendations,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"投资组合风险分析失败: {e}")
            return self._create_empty_risk_result(portfolio_value)
    
    def _analyze_concentration_risk(self, positions: Dict[str, float], portfolio_value: float) -> List[RiskMetric]:
        """分析集中度风险"""
        metrics = []
        
        if not positions:
            return metrics
        
        # 单股最大仓位
        max_position = max(positions.values()) / portfolio_value if portfolio_value > 0 else 0
        level = RiskLevel.LOW
        if max_position > self.risk_thresholds["max_position_size"]:
            level = RiskLevel.HIGH
        elif max_position > self.risk_thresholds["max_position_size"] * 0.8:
            level = RiskLevel.MEDIUM
        
        metrics.append(RiskMetric(
            name="最大单股仓位",
            value=max_position,
            threshold=self.risk_thresholds["max_position_size"],
            level=level,
            description=f"最大单股仓位占比 {max_position:.2%}",
            recommendation="建议分散投资，降低单股仓位" if level != RiskLevel.LOW else "仓位分布合理"
        ))
        
        # 总仓位
        total_position = sum(positions.values()) / portfolio_value if portfolio_value > 0 else 0
        level = RiskLevel.LOW
        if total_position > self.risk_thresholds["max_total_position"]:
            level = RiskLevel.HIGH
        elif total_position > self.risk_thresholds["max_total_position"] * 0.9:
            level = RiskLevel.MEDIUM
        
        metrics.append(RiskMetric(
            name="总仓位",
            value=total_position,
            threshold=self.risk_thresholds["max_total_position"],
            level=level,
            description=f"总仓位占比 {total_position:.2%}",
            recommendation="建议控制总仓位" if level != RiskLevel.LOW else "总仓位合理"
        ))
        
        return metrics
    
    def _analyze_volatility_risk(self, positions: Dict[str, float], prices: Dict[str, pd.DataFrame]) -> List[RiskMetric]:
        """分析波动性风险"""
        metrics = []
        
        if not positions or not prices:
            return metrics
        
        # 计算投资组合波动率
        portfolio_returns = self._calculate_portfolio_returns(positions, prices)
        if portfolio_returns is not None and len(portfolio_returns) > 1:
            volatility = portfolio_returns.std() * np.sqrt(252)  # 年化波动率
            
            level = RiskLevel.LOW
            if volatility > self.risk_thresholds["max_volatility"]:
                level = RiskLevel.HIGH
            elif volatility > self.risk_thresholds["max_volatility"] * 0.8:
                level = RiskLevel.MEDIUM
            
            metrics.append(RiskMetric(
                name="投资组合波动率",
                value=volatility,
                threshold=self.risk_thresholds["max_volatility"],
                level=level,
                description=f"年化波动率 {volatility:.2%}",
                recommendation="建议降低投资组合波动率" if level != RiskLevel.LOW else "波动率水平合理"
            ))
        
        return metrics
    
    def _analyze_drawdown_risk(self, positions: Dict[str, float], prices: Dict[str, pd.DataFrame]) -> List[RiskMetric]:
        """分析回撤风险"""
        metrics = []
        
        if not positions or not prices:
            return metrics
        
        # 计算投资组合净值曲线
        portfolio_returns = self._calculate_portfolio_returns(positions, prices)
        if portfolio_returns is not None and len(portfolio_returns) > 1:
            cumulative_returns = (1 + portfolio_returns).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            level = RiskLevel.LOW
            if abs(max_drawdown) > self.risk_thresholds["max_drawdown"]:
                level = RiskLevel.HIGH
            elif abs(max_drawdown) > self.risk_thresholds["max_drawdown"] * 0.8:
                level = RiskLevel.MEDIUM
            
            metrics.append(RiskMetric(
                name="最大回撤",
                value=abs(max_drawdown),
                threshold=self.risk_thresholds["max_drawdown"],
                level=level,
                description=f"最大回撤 {abs(max_drawdown):.2%}",
                recommendation="建议控制回撤风险" if level != RiskLevel.LOW else "回撤控制良好"
            ))
        
        return metrics
    
    def _analyze_liquidity_risk(self, positions: Dict[str, float], prices: Dict[str, pd.DataFrame]) -> List[RiskMetric]:
        """分析流动性风险"""
        metrics = []
        
        if not positions or not prices:
            return metrics
        
        # 检查每只股票的流动性
        low_liquidity_stocks = []
        for symbol, position in positions.items():
            if symbol in prices and not prices[symbol].empty:
                avg_volume = prices[symbol]['volume'].mean()
                if avg_volume < self.risk_thresholds["min_liquidity"]:
                    low_liquidity_stocks.append(symbol)
        
        if low_liquidity_stocks:
            level = RiskLevel.HIGH if len(low_liquidity_stocks) > len(positions) * 0.5 else RiskLevel.MEDIUM
            metrics.append(RiskMetric(
                name="流动性风险",
                value=len(low_liquidity_stocks),
                threshold=0,
                level=level,
                description=f"{len(low_liquidity_stocks)} 只股票流动性不足",
                recommendation=f"建议关注流动性: {', '.join(low_liquidity_stocks)}"
            ))
        
        return metrics
    
    def _analyze_correlation_risk(self, positions: Dict[str, float], prices: Dict[str, pd.DataFrame]) -> List[RiskMetric]:
        """分析相关性风险"""
        metrics = []
        
        if len(positions) < 2 or not prices:
            return metrics
        
        # 计算股票间相关性
        returns_data = {}
        for symbol in positions.keys():
            if symbol in prices and not prices[symbol].empty:
                returns = prices[symbol]['close'].pct_change().dropna()
                if len(returns) > 10:  # 至少需要10个数据点
                    returns_data[symbol] = returns
        
        if len(returns_data) < 2:
            return metrics
        
        # 计算相关性矩阵
        returns_df = pd.DataFrame(returns_data)
        correlation_matrix = returns_df.corr()
        
        # 找出高相关性股票对
        high_correlation_pairs = []
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr = abs(correlation_matrix.iloc[i, j])
                if corr > self.risk_thresholds["max_correlation"]:
                    high_correlation_pairs.append((
                        correlation_matrix.columns[i],
                        correlation_matrix.columns[j],
                        corr
                    ))
        
        if high_correlation_pairs:
            level = RiskLevel.HIGH if len(high_correlation_pairs) > 2 else RiskLevel.MEDIUM
            metrics.append(RiskMetric(
                name="相关性风险",
                value=len(high_correlation_pairs),
                threshold=0,
                level=level,
                description=f"{len(high_correlation_pairs)} 对股票高度相关",
                recommendation="建议分散投资，降低相关性"
            ))
        
        return metrics
    
    def _calculate_var(self, positions: Dict[str, float], prices: Dict[str, pd.DataFrame], portfolio_value: float) -> List[RiskMetric]:
        """计算VaR (Value at Risk)"""
        metrics = []
        
        if not positions or not prices or portfolio_value <= 0:
            return metrics
        
        try:
            # 计算投资组合收益率
            portfolio_returns = self._calculate_portfolio_returns(positions, prices)
            if portfolio_returns is None or len(portfolio_returns) < 10:
                return metrics
            
            # 计算VaR
            confidence_level = self.risk_thresholds["var_confidence"]
            var_1d = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
            var_1d_value = abs(var_1d * portfolio_value)
            
            # 计算CVaR (Conditional VaR)
            cvar_1d = portfolio_returns[portfolio_returns <= var_1d].mean()
            cvar_1d_value = abs(cvar_1d * portfolio_value)
            
            # 评估风险等级
            var_ratio = var_1d_value / portfolio_value
            level = RiskLevel.LOW
            if var_ratio > 0.05:  # 5%
                level = RiskLevel.HIGH
            elif var_ratio > 0.03:  # 3%
                level = RiskLevel.MEDIUM
            
            metrics.append(RiskMetric(
                name="VaR (1天)",
                value=var_1d_value,
                threshold=portfolio_value * 0.05,
                level=level,
                description=f"1天VaR: {var_1d_value:,.0f} 元 ({var_ratio:.2%})",
                recommendation="建议控制VaR风险" if level != RiskLevel.LOW else "VaR风险可控"
            ))
            
            metrics.append(RiskMetric(
                name="CVaR (1天)",
                value=cvar_1d_value,
                threshold=portfolio_value * 0.05,
                level=level,
                description=f"1天CVaR: {cvar_1d_value:,.0f} 元",
                recommendation="建议关注极端损失风险" if level != RiskLevel.LOW else "极端损失风险可控"
            ))
            
        except Exception as e:
            logger.error(f"VaR计算失败: {e}")
        
        return metrics
    
    def _calculate_portfolio_returns(self, positions: Dict[str, float], prices: Dict[str, pd.DataFrame]) -> Optional[pd.Series]:
        """计算投资组合收益率"""
        try:
            returns_list = []
            weights = []
            
            for symbol, position in positions.items():
                if symbol in prices and not prices[symbol].empty:
                    stock_returns = prices[symbol]['close'].pct_change().dropna()
                    if len(stock_returns) > 0:
                        returns_list.append(stock_returns)
                        weights.append(position)
            
            if not returns_list:
                return None
            
            # 标准化权重
            total_weight = sum(weights)
            if total_weight == 0:
                return None
            
            weights = [w / total_weight for w in weights]
            
            # 计算加权平均收益率
            min_length = min(len(r) for r in returns_list)
            if min_length < 2:
                return None
            
            # 截取相同长度的数据
            aligned_returns = [r.tail(min_length) for r in returns_list]
            
            # 计算加权组合收益率
            portfolio_returns = pd.Series(0, index=aligned_returns[0].index)
            for i, returns in enumerate(aligned_returns):
                portfolio_returns += weights[i] * returns
            
            return portfolio_returns
            
        except Exception as e:
            logger.error(f"投资组合收益率计算失败: {e}")
            return None
    
    def _generate_alerts(self, risk_metrics: List[RiskMetric]) -> List[RiskAlert]:
        """生成风险预警"""
        alerts = []
        
        for metric in risk_metrics:
            if metric.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                alerts.append(RiskAlert(
                    risk_type=self._get_risk_type_from_metric(metric.name),
                    level=metric.level,
                    message=metric.description,
                    timestamp=datetime.now(),
                    value=metric.value,
                    threshold=metric.threshold
                ))
        
        return alerts
    
    def _get_risk_type_from_metric(self, metric_name: str) -> RiskType:
        """根据指标名称获取风险类型"""
        if "仓位" in metric_name:
            return RiskType.CONCENTRATION
        elif "波动率" in metric_name:
            return RiskType.VOLATILITY
        elif "回撤" in metric_name:
            return RiskType.DRAWDOWN
        elif "流动性" in metric_name:
            return RiskType.LIQUIDITY
        elif "相关性" in metric_name:
            return RiskType.CORRELATION
        else:
            return RiskType.MARKET
    
    def _calculate_overall_risk(self, risk_metrics: List[RiskMetric]) -> Tuple[RiskLevel, float]:
        """计算整体风险等级和分数"""
        if not risk_metrics:
            return RiskLevel.LOW, 0.0
        
        # 计算风险分数 (0-100)
        high_risk_count = sum(1 for m in risk_metrics if m.level == RiskLevel.HIGH)
        critical_risk_count = sum(1 for m in risk_metrics if m.level == RiskLevel.CRITICAL)
        medium_risk_count = sum(1 for m in risk_metrics if m.level == RiskLevel.MEDIUM)
        
        risk_score = (critical_risk_count * 40 + high_risk_count * 25 + medium_risk_count * 10) / len(risk_metrics) * 100
        risk_score = min(risk_score, 100)
        
        # 确定风险等级
        if critical_risk_count > 0 or risk_score > 80:
            level = RiskLevel.CRITICAL
        elif high_risk_count > 0 or risk_score > 60:
            level = RiskLevel.HIGH
        elif medium_risk_count > 0 or risk_score > 30:
            level = RiskLevel.MEDIUM
        else:
            level = RiskLevel.LOW
        
        return level, risk_score
    
    def _generate_recommendations(self, risk_metrics: List[RiskMetric], alerts: List[RiskAlert]) -> List[str]:
        """生成风险控制建议"""
        recommendations = []
        
        # 基于风险指标生成建议
        for metric in risk_metrics:
            if metric.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                recommendations.append(metric.recommendation)
        
        # 基于预警生成建议
        if alerts:
            recommendations.append("立即关注风险预警，考虑调整投资组合")
        
        # 通用建议
        if not recommendations:
            recommendations.append("当前投资组合风险水平合理，建议持续监控")
        
        return list(set(recommendations))  # 去重
    
    def _create_empty_risk_result(self, portfolio_value: float) -> PortfolioRisk:
        """创建空的风险分析结果"""
        return PortfolioRisk(
            portfolio_value=portfolio_value,
            risk_metrics=[],
            alerts=[],
            overall_risk_level=RiskLevel.LOW,
            risk_score=0.0,
            recommendations=["无法进行风险分析，请检查数据"],
            timestamp=datetime.now()
        )
    
    def update_risk_thresholds(self, new_thresholds: Dict[str, float]):
        """更新风险阈值"""
        self.risk_thresholds.update(new_thresholds)
        logger.info("风险阈值已更新")
    
    def get_risk_thresholds(self) -> Dict[str, float]:
        """获取当前风险阈值"""
        return self.risk_thresholds.copy()

# 全局风险管理器实例
risk_manager = RiskManager()
