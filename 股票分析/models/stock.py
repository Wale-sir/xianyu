from datetime import datetime
from extensions import mongo
from bson import ObjectId
import random
from datetime import timedelta

class Stock:
    @classmethod
    def get_collection(cls):
        return mongo.db.stocks

    def __init__(self, data):
        self.id = str(data.get('_id'))
        self.code = data.get('code')
        self.name = data.get('name')
        self.description = data.get('description')
        self.current_price = data.get('current_price')
        self.change_percent = data.get('change_percent')
        self.volume = data.get('volume')
        self.market_cap = data.get('market_cap')
        self.created_by = data.get('created_by')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')

    @classmethod
    def create(cls, data):
        result = cls.get_collection().insert_one(data)
        return cls.get_by_id(result.inserted_id)

    @classmethod
    def get_by_id(cls, stock_id):
        data = cls.get_collection().find_one({'_id': ObjectId(stock_id)})
        return cls(data) if data else None

    @classmethod
    def get_all_stocks(cls):
        stocks = cls.get_collection().find()
        return [cls(stock) for stock in stocks]

    def update(self, data):
        self.get_collection().update_one(
            {'_id': ObjectId(self.id)},
            {'$set': data}
        )
        return self.get_by_id(self.id)

    def delete(self):
        self.get_collection().delete_one({'_id': ObjectId(self.id)})

    @classmethod
    def get_stock_history(cls, stock_id, days=30):
        """获取股票历史数据"""
        base_price = float(cls.get_by_id(stock_id).current_price)
        history = []
        
        for i in range(days):
            date = datetime.utcnow() - timedelta(days=days-i-1)
            price_change = random.uniform(-0.02, 0.02)
            price = base_price * (1 + price_change)
            volume = random.randint(1000, 10000)
            
            history.append({
                'date': date,
                'open': price * (1 + random.uniform(-0.01, 0.01)),
                'high': price * (1 + random.uniform(0, 0.02)),
                'low': price * (1 - random.uniform(0, 0.02)),
                'close': price,
                'volume': volume
            })
            base_price = price
        
        return history

    @classmethod
    def get_stock_predictions(cls, stock_id):
        """获取股票预测数据"""
        pipeline = [
            {'$match': {'_id': ObjectId(stock_id)}},
            {'$lookup': {
                'from': 'stock_predictions',
                'localField': '_id',
                'foreignField': 'stock_id',
                'as': 'predictions'
            }},
            {'$unwind': '$predictions'},
            {'$sort': {'predictions.date': -1}}
        ]
        result = cls.get_collection().aggregate(pipeline)
        return list(result) 