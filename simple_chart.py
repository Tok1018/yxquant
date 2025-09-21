"""
简单的K线图生成器
"""
import pandas as pd
from datetime import datetime

def create_simple_kline_chart(symbol, stock_name, data):
    """创建简单的K线图HTML"""
    if data is None or (hasattr(data, 'empty') and data.empty) or len(data) == 0:
        return "<div style='text-align:center;padding:50px;'>暂无数据</div>"
    
    # 准备数据
    # 确保日期列是datetime类型
    if not pd.api.types.is_datetime64_any_dtype(data['date']):
        data['date'] = pd.to_datetime(data['date'])
    
    dates = data['date'].dt.strftime('%Y-%m-%d').tolist()
    kline_data = data[['open', 'close', 'low', 'high']].values.tolist()
    volume_data = data['volume'].tolist()
    
    # 生成简单的HTML表格K线图
    html = f"""
    <div style="width: 100%; height: 600px; overflow: auto;">
        <h4>{stock_name} ({symbol}) K线图</h4>
        <table class="table table-striped table-sm">
            <thead>
                <tr>
                    <th>日期</th>
                    <th>开盘</th>
                    <th>最高</th>
                    <th>最低</th>
                    <th>收盘</th>
                    <th>成交量</th>
                    <th>涨跌</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for i, (date, ohlc, volume) in enumerate(zip(dates, kline_data, volume_data)):
        open_price, high, low, close = ohlc
        change = close - open_price
        change_pct = (change / open_price * 100) if open_price > 0 else 0
        
        color = "red" if change >= 0 else "green"
        change_text = f"+{change:.2f}" if change >= 0 else f"{change:.2f}"
        
        html += f"""
                <tr>
                    <td>{date}</td>
                    <td>{open_price:.2f}</td>
                    <td>{high:.2f}</td>
                    <td>{low:.2f}</td>
                    <td style="color: {color}; font-weight: bold;">{close:.2f}</td>
                    <td>{volume:,}</td>
                    <td style="color: {color};">{change_text} ({change_pct:+.2f}%)</td>
                </tr>
        """
    
    html += """
            </tbody>
        </table>
    </div>
    """
    
    return html
