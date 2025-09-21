"""
可视化模块
提供图表展示、策略表现分析等功能
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
from typing import Dict, List, Optional, Tuple, Any
import logging
from datetime import datetime, timedelta
import json
from pathlib import Path

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChartGenerator:
    """图表生成器"""
    
    def __init__(self):
        self.chart_style = {
            'width': 1200,
            'height': 600,
            'template': 'plotly_white'
        }
    
    def create_candlestick_chart(self, data: pd.DataFrame, symbol: str, 
                                indicators: Dict[str, pd.Series] = None) -> go.Figure:
        """创建K线图"""
        try:
            fig = go.Figure()
            
            # 添加K线图
            fig.add_trace(go.Candlestick(
                x=data['date'],
                open=data['open'],
                high=data['high'],
                low=data['low'],
                close=data['close'],
                name=symbol,
                increasing_line_color='red',
                decreasing_line_color='green'
            ))
            
            # 添加技术指标
            if indicators:
                for name, series in indicators.items():
                    if not series.empty and name in data.columns:
                        fig.add_trace(go.Scatter(
                            x=data['date'],
                            y=data[name],
                            mode='lines',
                            name=name,
                            line=dict(width=2)
                        ))
            
            # 设置布局
            fig.update_layout(
                title=f'{symbol} K线图',
                xaxis_title='日期',
                yaxis_title='价格',
                xaxis_rangeslider_visible=False,
                **self.chart_style
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建K线图失败: {e}")
            return go.Figure()
    
    def create_volume_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        """创建成交量图"""
        try:
            fig = go.Figure()
            
            # 添加成交量柱状图
            colors = ['red' if close >= open else 'green' 
                     for close, open in zip(data['close'], data['open'])]
            
            fig.add_trace(go.Bar(
                x=data['date'],
                y=data['volume'],
                name='成交量',
                marker_color=colors
            ))
            
            # 设置布局
            fig.update_layout(
                title=f'{symbol} 成交量',
                xaxis_title='日期',
                yaxis_title='成交量',
                **self.chart_style
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建成交量图失败: {e}")
            return go.Figure()
    
    def create_technical_indicators_chart(self, data: pd.DataFrame, symbol: str) -> go.Figure:
        """创建技术指标图"""
        try:
            # 创建子图
            fig = make_subplots(
                rows=4, cols=1,
                subplot_titles=('价格与均线', 'MACD', 'RSI', '布林带'),
                vertical_spacing=0.05,
                row_heights=[0.4, 0.2, 0.2, 0.2]
            )
            
            # 价格与均线
            fig.add_trace(go.Scatter(
                x=data['date'], y=data['close'],
                mode='lines', name='收盘价',
                line=dict(color='blue', width=2)
            ), row=1, col=1)
            
            if 'SMA_20' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['SMA_20'],
                    mode='lines', name='SMA20',
                    line=dict(color='orange', width=1)
                ), row=1, col=1)
            
            if 'SMA_50' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['SMA_50'],
                    mode='lines', name='SMA50',
                    line=dict(color='red', width=1)
                ), row=1, col=1)
            
            # MACD
            if 'MACD' in data.columns and 'MACD_Signal' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['MACD'],
                    mode='lines', name='MACD',
                    line=dict(color='blue', width=2)
                ), row=2, col=1)
                
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['MACD_Signal'],
                    mode='lines', name='MACD Signal',
                    line=dict(color='red', width=2)
                ), row=2, col=1)
                
                # MACD柱状图
                macd_hist = data['MACD'] - data['MACD_Signal']
                colors = ['green' if val >= 0 else 'red' for val in macd_hist]
                fig.add_trace(go.Bar(
                    x=data['date'], y=macd_hist,
                    name='MACD Hist',
                    marker_color=colors
                ), row=2, col=1)
            
            # RSI
            if 'RSI_14' in data.columns:
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['RSI_14'],
                    mode='lines', name='RSI',
                    line=dict(color='purple', width=2)
                ), row=3, col=1)
                
                # RSI超买超卖线
                fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
                fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            
            # 布林带
            if all(col in data.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['close'],
                    mode='lines', name='收盘价',
                    line=dict(color='blue', width=2)
                ), row=4, col=1)
                
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['BB_Upper'],
                    mode='lines', name='布林上轨',
                    line=dict(color='gray', width=1, dash='dash')
                ), row=4, col=1)
                
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['BB_Middle'],
                    mode='lines', name='布林中轨',
                    line=dict(color='orange', width=1)
                ), row=4, col=1)
                
                fig.add_trace(go.Scatter(
                    x=data['date'], y=data['BB_Lower'],
                    mode='lines', name='布林下轨',
                    line=dict(color='gray', width=1, dash='dash')
                ), row=4, col=1)
            
            # 设置布局
            fig.update_layout(
                title=f'{symbol} 技术指标分析',
                height=800,
                showlegend=True,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建技术指标图失败: {e}")
            return go.Figure()
    
    def create_backtest_results_chart(self, results: Dict[str, Any]) -> go.Figure:
        """创建回测结果图"""
        try:
            # 创建子图
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('净值曲线', '回撤曲线', '收益分布', '月度收益'),
                specs=[[{"secondary_y": True}, {"secondary_y": False}],
                     [{"secondary_y": False}, {"secondary_y": False}]]
            )
            
            # 净值曲线
            if 'equity_curve' in results and not results['equity_curve'].empty:
                equity_data = results['equity_curve']
                fig.add_trace(go.Scatter(
                    x=equity_data.index,
                    y=equity_data.values,
                    mode='lines',
                    name='净值曲线',
                    line=dict(color='blue', width=2)
                ), row=1, col=1)
            
            # 基准曲线
            if 'benchmark_returns' in results and not results['benchmark_returns'].empty:
                benchmark_data = results['benchmark_returns'].cumsum()
                fig.add_trace(go.Scatter(
                    x=benchmark_data.index,
                    y=benchmark_data.values,
                    mode='lines',
                    name='基准曲线',
                    line=dict(color='red', width=2, dash='dash')
                ), row=1, col=1)
            
            # 回撤曲线
            if 'daily_returns' in results and not results['daily_returns'].empty:
                returns = results['daily_returns']
                cumulative = (1 + returns).cumprod()
                running_max = cumulative.expanding().max()
                drawdown = (cumulative - running_max) / running_max
                
                fig.add_trace(go.Scatter(
                    x=drawdown.index,
                    y=drawdown.values,
                    mode='lines',
                    name='回撤',
                    line=dict(color='red', width=2),
                    fill='tonexty'
                ), row=1, col=2)
            
            # 收益分布
            if 'daily_returns' in results and not results['daily_returns'].empty:
                returns = results['daily_returns']
                fig.add_trace(go.Histogram(
                    x=returns.values,
                    name='收益分布',
                    nbinsx=50,
                    marker_color='lightblue'
                ), row=2, col=1)
            
            # 月度收益热力图
            if 'daily_returns' in results and not results['daily_returns'].empty:
                returns = results['daily_returns']
                monthly_returns = returns.resample('M').apply(lambda x: (1 + x).prod() - 1)
                
                # 创建月度收益矩阵
                monthly_data = []
                for date, ret in monthly_returns.items():
                    monthly_data.append({
                        'year': date.year,
                        'month': date.month,
                        'return': ret
                    })
                
                if monthly_data:
                    df_monthly = pd.DataFrame(monthly_data)
                    pivot_table = df_monthly.pivot(index='year', columns='month', values='return')
                    
                    fig.add_trace(go.Heatmap(
                        z=pivot_table.values,
                        x=pivot_table.columns,
                        y=pivot_table.index,
                        colorscale='RdYlGn',
                        name='月度收益'
                    ), row=2, col=2)
            
            # 设置布局
            fig.update_layout(
                title='回测结果分析',
                height=600,
                showlegend=True,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建回测结果图失败: {e}")
            return go.Figure()
    
    def create_correlation_heatmap(self, data: pd.DataFrame, symbols: List[str]) -> go.Figure:
        """创建相关性热力图"""
        try:
            # 计算相关性矩阵
            close_prices = data.pivot_table(
                index='date', 
                columns='symbol', 
                values='close'
            )
            
            correlation_matrix = close_prices.corr()
            
            # 创建热力图
            fig = go.Figure(data=go.Heatmap(
                z=correlation_matrix.values,
                x=correlation_matrix.columns,
                y=correlation_matrix.index,
                colorscale='RdBu',
                zmid=0,
                text=correlation_matrix.round(3).values,
                texttemplate="%{text}",
                textfont={"size": 10}
            ))
            
            fig.update_layout(
                title='股票相关性热力图',
                xaxis_title='股票代码',
                yaxis_title='股票代码',
                **self.chart_style
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建相关性热力图失败: {e}")
            return go.Figure()
    
    def create_risk_metrics_chart(self, results: Dict[str, Any]) -> go.Figure:
        """创建风险指标图"""
        try:
            # 提取风险指标
            metrics = {
                '总收益率': results.get('total_return', 0),
                '年化收益率': results.get('annual_return', 0),
                '波动率': results.get('volatility', 0),
                '夏普比率': results.get('sharpe_ratio', 0),
                '最大回撤': results.get('max_drawdown', 0),
                '卡玛比率': results.get('calmar_ratio', 0),
                '胜率': results.get('win_rate', 0),
                '盈利因子': results.get('profit_factor', 0)
            }
            
            # 创建雷达图
            fig = go.Figure()
            
            # 标准化指标值（0-1范围）
            normalized_metrics = {}
            for key, value in metrics.items():
                if key in ['总收益率', '年化收益率', '夏普比率', '卡玛比率', '胜率', '盈利因子']:
                    # 正向指标
                    normalized_metrics[key] = max(0, min(1, (value + 1) / 2))
                else:
                    # 负向指标（波动率、最大回撤）
                    normalized_metrics[key] = max(0, min(1, 1 - abs(value)))
            
            # 添加雷达图
            fig.add_trace(go.Scatterpolar(
                r=list(normalized_metrics.values()),
                theta=list(normalized_metrics.keys()),
                fill='toself',
                name='风险指标',
                line_color='blue'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 1]
                    )),
                title='风险指标雷达图',
                **self.chart_style
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建风险指标图失败: {e}")
            return go.Figure()
    
    def create_performance_comparison_chart(self, strategies_results: Dict[str, Dict[str, Any]]) -> go.Figure:
        """创建策略表现对比图"""
        try:
            # 提取对比数据
            strategies = list(strategies_results.keys())
            metrics = ['total_return', 'annual_return', 'volatility', 'sharpe_ratio', 'max_drawdown']
            
            # 创建对比数据
            comparison_data = {}
            for metric in metrics:
                comparison_data[metric] = [strategies_results[strategy].get(metric, 0) for strategy in strategies]
            
            # 创建子图
            fig = make_subplots(
                rows=2, cols=3,
                subplot_titles=('总收益率', '年化收益率', '波动率', '夏普比率', '最大回撤', '综合评分'),
                specs=[[{"type": "bar"}, {"type": "bar"}, {"type": "bar"}],
                     [{"type": "bar"}, {"type": "bar"}, {"type": "bar"}]]
            )
            
            # 添加柱状图
            metric_names = ['总收益率', '年化收益率', '波动率', '夏普比率', '最大回撤']
            positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2)]
            
            for i, (metric, pos) in enumerate(zip(metrics, positions)):
                fig.add_trace(go.Bar(
                    x=strategies,
                    y=comparison_data[metric],
                    name=metric_names[i],
                    showlegend=False
                ), row=pos[0], col=pos[1])
            
            # 综合评分
            scores = []
            for strategy in strategies:
                score = 0
                results = strategies_results[strategy]
                
                # 收益率评分
                score += min(100, max(0, results.get('total_return', 0) * 100))
                
                # 夏普比率评分
                score += min(50, max(0, results.get('sharpe_ratio', 0) * 20))
                
                # 最大回撤评分（负向指标）
                score += min(50, max(0, 50 + results.get('max_drawdown', 0) * 100))
                
                scores.append(score)
            
            fig.add_trace(go.Bar(
                x=strategies,
                y=scores,
                name='综合评分',
                showlegend=False,
                marker_color='gold'
            ), row=2, col=3)
            
            # 设置布局
            fig.update_layout(
                title='策略表现对比',
                height=600,
                showlegend=False,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"创建策略对比图失败: {e}")
            return go.Figure()
    
    def save_chart(self, fig: go.Figure, filename: str, format: str = 'html') -> str:
        """保存图表"""
        try:
            # 创建输出目录
            output_dir = Path("static/charts")
            output_dir.mkdir(exist_ok=True)
            
            filepath = output_dir / f"{filename}.{format}"
            
            if format == 'html':
                fig.write_html(str(filepath))
            elif format == 'png':
                fig.write_image(str(filepath))
            elif format == 'pdf':
                fig.write_image(str(filepath))
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            logger.info(f"图表已保存: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"保存图表失败: {e}")
            return ""

# 创建全局图表生成器实例
chart_generator = ChartGenerator()

# 便捷函数
def create_candlestick_chart(data: pd.DataFrame, symbol: str, **kwargs) -> go.Figure:
    """创建K线图的便捷函数"""
    return chart_generator.create_candlestick_chart(data, symbol, **kwargs)

def create_volume_chart(data: pd.DataFrame, symbol: str) -> go.Figure:
    """创建成交量图的便捷函数"""
    return chart_generator.create_volume_chart(data, symbol)

def create_technical_indicators_chart(data: pd.DataFrame, symbol: str) -> go.Figure:
    """创建技术指标图的便捷函数"""
    return chart_generator.create_technical_indicators_chart(data, symbol)

def create_backtest_results_chart(results: Dict[str, Any]) -> go.Figure:
    """创建回测结果图的便捷函数"""
    return chart_generator.create_backtest_results_chart(results)

def create_correlation_heatmap(data: pd.DataFrame, symbols: List[str]) -> go.Figure:
    """创建相关性热力图的便捷函数"""
    return chart_generator.create_correlation_heatmap(data, symbols)

def create_risk_metrics_chart(results: Dict[str, Any]) -> go.Figure:
    """创建风险指标图的便捷函数"""
    return chart_generator.create_risk_metrics_chart(results)

def create_performance_comparison_chart(strategies_results: Dict[str, Dict[str, Any]]) -> go.Figure:
    """创建策略表现对比图的便捷函数"""
    return chart_generator.create_performance_comparison_chart(strategies_results)
