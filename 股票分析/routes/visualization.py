from flask import Blueprint, render_template, jsonify
from models.stock import Stock
from models.prediction import StockPrediction
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from datetime import datetime, timedelta

visualization_bp = Blueprint('visualization', __name__)

@visualization_bp.route('/visualization')
def index():
    """可视化首页"""
    return render_template('visualization/index.html')

@visualization_bp.route('/visualization/stock/<stock_id>')
def stock_visualization(stock_id):
    """股票可视化页面"""
    try:
        stock = Stock.get_by_id(stock_id)
        if not stock:
            return render_template('visualization/stock.html',
                                error='股票不存在')
        
        history = Stock.get_stock_history(stock_id)
        if not history:
            return render_template('visualization/stock.html',
                                stock=stock,
                                error='暂无历史数据')
        
        # 将数据转换为DataFrame以便处理
        df = pd.DataFrame(history)
        
        # 确保数值类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 按日期排序
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 准备K线图数据
        candlestick_data = {
            'x': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'open': df['open'].round(2).tolist(),
            'high': df['high'].round(2).tolist(),
            'low': df['low'].round(2).tolist(),
            'close': df['close'].round(2).tolist()
        }
        
        # 准备成交量数据
        volume_data = {
            'x': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'y': df['volume'].astype(int).tolist()
        }
        
        # 计算技术指标
        df['MA5'] = df['close'].rolling(window=5).mean().round(2)
        df['MA10'] = df['close'].rolling(window=10).mean().round(2)
        df['MA20'] = df['close'].rolling(window=20).mean().round(2)
        
        # 准备技术指标数据 - 使用 None 替换 NaN
        indicators_data = {
            'x': df['date'].dt.strftime('%Y-%m-%d').tolist(),
            'ma5': df['MA5'].replace({np.nan: None}).tolist(),
            'ma10': df['MA10'].replace({np.nan: None}).tolist(),
            'ma20': df['MA20'].replace({np.nan: None}).tolist()
        }
        
        return render_template('visualization/stock.html',
                             stock=stock,
                             candlestick_data=candlestick_data,
                             volume_data=volume_data,
                             indicators_data=indicators_data)
                             
    except Exception as e:
        print(f"Error in stock_visualization: {str(e)}")
        return render_template('visualization/stock.html',
                             error='数据处理出错，请稍后重试')

@visualization_bp.route('/visualization/market-overview')
def market_overview():
    """获取市场概览数据API"""
    try:
        stocks = Stock.get_all_stocks()

        # 计算关键指标 (总市值, 总成交量, 涨跌家数)
        total_market_cap = sum(stock.market_cap for stock in stocks if stock.market_cap is not None)
        total_volume = sum(stock.volume for stock in stocks if stock.volume is not None)
        gainers_count = sum(1 for stock in stocks if stock.change_percent is not None and stock.change_percent > 0)
        losers_count = sum(1 for stock in stocks if stock.change_percent is not None and stock.change_percent < 0)

        # 获取涨幅榜/跌幅榜 (例如，取前10名)
        # 需要确保 stock.change_percent 是可比较的数值类型
        gainers = sorted([s for s in stocks if s.change_percent is not None], key=lambda x: x.change_percent, reverse=True)[:10]
        losers = sorted([s for s in stocks if s.change_percent is not None], key=lambda x: x.change_percent)[:10]

        # 简单的市值分布 (仍然保留，可以用于饼图)
        market_cap_distribution = {
            'labels': ['小盘股', '中盘股', '大盘股'],
            'values': [0, 0, 0]
        }
        for stock in stocks:
             if stock.market_cap is not None:
                if stock.market_cap < 1000000000:  # 10亿以下
                    market_cap_distribution['values'][0] += 1
                elif stock.market_cap < 10000000000:  # 100亿以下
                    market_cap_distribution['values'][1] += 1
                else:  # 100亿以上
                    market_cap_distribution['values'][2] += 1

        # 可以添加更多数据，例如行业分布、交易量排名等

        return jsonify({
            'key_metrics': {
                'total_market_cap': round(total_market_cap / 100000000, 2) if total_market_cap is not None else 0, # 转换为亿元单位
                'total_volume': round(total_volume / 10000, 2) if total_volume is not None else 0, # 转换为万手单位 (假设volume单位是股)
                'gainers_count': gainers_count,
                'losers_count': losers_count,
                'unchanged_count': len(stocks) - gainers_count - losers_count # 估算持平家数
            },
            'top_gainers': [{'code': s.code, 'name': s.name, 'change_percent': round(s.change_percent, 2), 'current_price': round(s.current_price, 2)} for s in gainers],
            'top_losers': [{'code': s.code, 'name': s.name, 'change_percent': round(s.change_percent, 2), 'current_price': round(s.current_price, 2)} for s in losers],
            'market_cap_distribution': market_cap_distribution
            # 添加更多数据...
        })

    except Exception as e:
        print(f"Error in market_overview API: {str(e)}")
        return jsonify({'error': '获取市场概览数据出错'}), 500

@visualization_bp.route('/api/stock/<stock_id>/data')
def get_stock_data(stock_id):
    """获取股票数据API"""
    try:
        stock = Stock.get_by_id(stock_id)
        if not stock:
            return jsonify({'error': '股票不存在'}), 404
        
        history = Stock.get_stock_history(stock_id)
        if not history:
            return jsonify({'error': '暂无历史数据'}), 404
        
        # 将数据转换为DataFrame以便处理
        df = pd.DataFrame(history)
        
        # 确保数值类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 按日期排序
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        return jsonify({
            'stock': {
                'id': stock.id,
                'code': stock.code,
                'name': stock.name,
                'current_price': float(stock.current_price) if stock.current_price is not None else None,
                'change_percent': float(stock.change_percent) if stock.change_percent is not None else None,
                'volume': int(stock.volume) if stock.volume is not None else None,
                'market_cap': float(stock.market_cap) if stock.market_cap is not None else None
            },
            'history': [
                {
                    'date': row['date'].strftime('%Y-%m-%d'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': int(row['volume'])
                }
                for _, row in df.iterrows()
            ]
        })
    except Exception as e:
        print(f"Error in get_stock_data: {str(e)}")
        return jsonify({'error': '数据处理出错'}), 500 