import random
from datetime import datetime, timedelta
import numpy as np
from models.stock import Stock
from models.prediction import StockPrediction
from extensions import mongo

# 预定义的股票列表
STOCK_LIST = [
    {'code': '600000', 'name': '浦发银行', 'description': '上海浦东发展银行股份有限公司'},
    {'code': '601318', 'name': '中国平安', 'description': '中国平安保险(集团)股份有限公司'},
    {'code': '600036', 'name': '招商银行', 'description': '招商银行股份有限公司'},
    {'code': '000001', 'name': '平安银行', 'description': '平安银行股份有限公司'},
    {'code': '600519', 'name': '贵州茅台', 'description': '贵州茅台酒股份有限公司'},
    {'code': '000858', 'name': '五粮液', 'description': '宜宾五粮液股份有限公司'},
    {'code': '601166', 'name': '兴业银行', 'description': '兴业银行股份有限公司'},
    {'code': '600276', 'name': '恒瑞医药', 'description': '江苏恒瑞医药股份有限公司'},
    {'code': '000333', 'name': '美的集团', 'description': '美的集团股份有限公司'},
    {'code': '600887', 'name': '伊利股份', 'description': '内蒙古伊利实业集团股份有限公司'}
]

def generate_stock_price(base_price, volatility=0.02):
    """生成模拟的股票价格"""
    change = random.gauss(0, volatility)
    new_price = base_price * (1 + change)
    return round(new_price, 2)

def generate_stock_data(days=30):
    """生成指定天数的股票历史数据"""
    data = []
    base_price = random.uniform(10, 1000)
    current_price = base_price
    
    for i in range(days):
        date = datetime.now() - timedelta(days=days-i-1)
        open_price = current_price
        high_price = open_price * (1 + random.uniform(0, 0.05))
        low_price = open_price * (1 - random.uniform(0, 0.05))
        close_price = generate_stock_price(open_price)
        volume = int(random.uniform(1000000, 100000000))
        
        data.append({
            'date': date,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
        
        current_price = close_price
    
    return data

def generate_market_data():
    """生成市场数据"""
    stocks = []
    for stock_info in STOCK_LIST:
        base_price = random.uniform(10, 1000)
        current_price = generate_stock_price(base_price)
        change_percent = random.uniform(-10, 10)
        volume = int(random.uniform(1000000, 100000000))
        market_cap = current_price * volume
        
        stock_data = {
            'code': stock_info['code'],
            'name': stock_info['name'],
            'description': stock_info['description'],
            'current_price': current_price,
            'change_percent': round(change_percent, 2),
            'volume': volume,
            'market_cap': round(market_cap, 2),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        stocks.append(stock_data)
    
    return stocks

def seed_database():
    """向数据库填充模拟数据"""
    # 生成并保存股票数据
    stocks = generate_market_data()
    for stock_data in stocks:
        stock = Stock.create(stock_data)
        
        # 为每个股票生成历史数据
        history_data = generate_stock_data()
        for data in history_data:
            data['stock_id'] = stock.id
            mongo.db.stock_history.insert_one(data)
        
        # 生成预测数据
        for _ in range(5):
            prediction_data = {
                'stock_id': stock.id,
                'date': datetime.utcnow(),
                'predicted_price': generate_stock_price(stock.current_price),
                'confidence': random.uniform(0.5, 0.95),
                'direction': random.choice(['up', 'down'])
            }
            StockPrediction.create(prediction_data)

if __name__ == '__main__':
    seed_database() 