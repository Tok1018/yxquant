"""
K线图生成模块
使用pyecharts生成专业的K线图
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from pyecharts import options as opts
from pyecharts.charts import Kline, Line, Bar, Grid
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType
from simple_chart import create_simple_kline_chart

logger = logging.getLogger(__name__)

class KlineChartGenerator:
    """K线图生成器"""
    
    def __init__(self):
        self.theme = ThemeType.LIGHT
    
    def create_kline_chart(self, 
                          symbol: str, 
                          stock_name: str, 
                          data: pd.DataFrame,
                          chart_type: str = "kline") -> str:
        """
        创建K线图
        
        Args:
            symbol: 股票代码
            stock_name: 股票名称
            data: K线数据，包含date, open, high, low, close, volume列
            chart_type: 图表类型 ("kline", "line", "candlestick")
        
        Returns:
            HTML字符串
        """
        try:
            if data.empty:
                return self._create_empty_chart("暂无数据")
            
            # 数据预处理
            data = self._prepare_data(data)
            
            if chart_type == "kline":
                return self._create_kline_with_volume(symbol, stock_name, data)
            elif chart_type == "line":
                return self._create_line_chart(symbol, stock_name, data)
            elif chart_type == "candlestick":
                return self._create_candlestick_chart(symbol, stock_name, data)
            else:
                return self._create_kline_with_volume(symbol, stock_name, data)
                
        except Exception as e:
            logger.error(f"创建K线图失败: {e}")
            return self._create_error_chart(str(e))
    
    def _prepare_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        # 创建数据副本避免SettingWithCopyWarning
        data = data.copy()
        
        # 确保日期列是datetime类型
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
            data = data.sort_values('date')
        
        # 确保数值列是float类型
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in data.columns:
                data[col] = pd.to_numeric(data[col], errors='coerce')
        
        # 删除包含NaN的行
        data = data.dropna()
        
        return data
    
    def _create_kline_with_volume(self, symbol: str, stock_name: str, data: pd.DataFrame) -> str:
        """创建K线图+成交量组合图 - 按照示例"""
        # 准备K线数据
        dates = data['date'].dt.strftime('%Y-%m-%d').tolist()
        kline_data = data[['open', 'close', 'low', 'high']].values.tolist()
        
        # 按照示例创建K线图
        kline = (
            Kline()
            .add_xaxis(dates)
            .add_yaxis("K线", kline_data)
            .set_global_opts(
                xaxis_opts=opts.AxisOpts(is_scale=True),
                yaxis_opts=opts.AxisOpts(
                    is_scale=True,
                    splitarea_opts=opts.SplitAreaOpts(
                        is_show=True,
                        areastyle_opts=opts.AreaStyleOpts(opacity=1)
                    )
                ),
                datazoom_opts=[opts.DataZoomOpts(pos_bottom="-2%")],
                title_opts=opts.TitleOpts(title=f"{stock_name} ({symbol}) K线图")
            )
        )
        
        # 返回Pyecharts生成的HTML
        return kline.render_embed()
    
    def _create_line_chart(self, symbol: str, stock_name: str, data: pd.DataFrame) -> str:
        """创建折线图"""
        dates = data['date'].dt.strftime('%Y-%m-%d').tolist()
        close_prices = data['close'].tolist()
        
        line = (
            Line(init_opts=opts.InitOpts(
                width="100%",
                height="500px",
                theme=self.theme
            ))
            .add_xaxis(dates)
            .add_yaxis(
                series_name="收盘价",
                y_axis=close_prices,
                is_smooth=True,
                symbol="circle",
                symbol_size=6,
                linestyle_opts=opts.LineStyleOpts(color="#5470c6", width=2),
                itemstyle_opts=opts.ItemStyleOpts(color="#5470c6"),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"{stock_name} ({symbol}) 价格走势图",
                    pos_left="center"
                ),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                ),
                yaxis_opts=opts.AxisOpts(
                    name="价格",
                    type_="value",
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=True,
                        type_="slider",
                        pos_top="90%",
                        range_start=0,
                        range_end=100,
                    )
                ],
            )
        )
        
        return line.render_embed()
    
    def _create_candlestick_chart(self, symbol: str, stock_name: str, data: pd.DataFrame) -> str:
        """创建蜡烛图（简化版K线图）"""
        dates = data['date'].dt.strftime('%Y-%m-%d').tolist()
        kline_data = data[['open', 'close', 'low', 'high']].values.tolist()
        
        kline = (
            Kline(init_opts=opts.InitOpts(
                width="100%",
                height="500px",
                theme=self.theme
            ))
            .add_xaxis(dates)
            .add_yaxis(
                series_name="蜡烛图",
                y_axis=kline_data,
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#ef232a",
                    color0="#00da3c",
                    border_color="#ef232a",
                    border_color0="#00da3c",
                ),
            )
            .set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"{stock_name} ({symbol}) 蜡烛图",
                    pos_left="center"
                ),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                ),
                yaxis_opts=opts.AxisOpts(
                    name="价格",
                    type_="value",
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=True,
                        type_="slider",
                        pos_top="90%",
                        range_start=0,
                        range_end=100,
                    )
                ],
            )
        )
        
        return kline.render_embed()
    
    def _create_empty_chart(self, message: str) -> str:
        """创建空数据图表"""
        return f"""
        <div style="text-align: center; padding: 50px; color: #999;">
            <h3>{message}</h3>
        </div>
        """
    
    def _create_error_chart(self, error_message: str) -> str:
        """创建错误图表"""
        return f"""
        <div style="text-align: center; padding: 50px; color: #f56c6c;">
            <h3>图表加载失败</h3>
            <p>{error_message}</p>
        </div>
        """
    
    def create_technical_indicators_chart(self, 
                                        symbol: str, 
                                        stock_name: str, 
                                        data: pd.DataFrame,
                                        indicators: List[str] = None) -> str:
        """创建技术指标图表"""
        if indicators is None:
            indicators = ['MA5', 'MA10', 'MA20', 'MA60']
        
        try:
            if data.empty:
                return self._create_empty_chart("暂无数据")
            
            data = self._prepare_data(data)
            dates = data['date'].dt.strftime('%Y-%m-%d').tolist()
            
            # 创建K线图
            kline_data = data[['open', 'close', 'low', 'high']].values.tolist()
            
            kline = (
                Kline(init_opts=opts.InitOpts(
                    width="100%",
                    height="400px",
                    theme=self.theme
                ))
                .add_xaxis(dates)
                .add_yaxis(
                    series_name="K线",
                    y_axis=kline_data,
                    itemstyle_opts=opts.ItemStyleOpts(
                        color="#ef232a",
                        color0="#00da3c",
                        border_color="#ef232a",
                        border_color0="#00da3c",
                    ),
                )
            )
            
            # 添加移动平均线
            for indicator in indicators:
                if indicator in data.columns:
                    ma_data = data[indicator].fillna(0).tolist()
                    kline.add_yaxis(
                        series_name=indicator,
                        y_axis=ma_data,
                        type_="line",
                        is_smooth=True,
                        symbol="none",
                        linestyle_opts=opts.LineStyleOpts(width=2),
                    )
            
            kline.set_global_opts(
                title_opts=opts.TitleOpts(
                    title=f"{stock_name} ({symbol}) 技术指标图",
                    pos_left="center"
                ),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    boundary_gap=False,
                ),
                yaxis_opts=opts.AxisOpts(
                    name="价格",
                    type_="value",
                ),
                tooltip_opts=opts.TooltipOpts(
                    trigger="axis",
                    axis_pointer_type="cross",
                ),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=True,
                        type_="slider",
                        pos_top="90%",
                        range_start=0,
                        range_end=100,
                    )
                ],
                legend_opts=opts.LegendOpts(
                    is_show=True,
                    pos_left="center",
                    pos_top="5%"
                ),
            )
            
            return kline.render_embed()
            
        except Exception as e:
            logger.error(f"创建技术指标图表失败: {e}")
            return self._create_error_chart(str(e))

# 全局K线图生成器实例
kline_chart_generator = KlineChartGenerator()
