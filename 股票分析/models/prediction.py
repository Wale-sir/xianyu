from datetime import datetime
from extensions import mongo
from bson import ObjectId

class StockPrediction:
    @classmethod
    def get_collection(cls):
        return mongo.db.stock_predictions

    def __init__(self, data):
        self.id = str(data.get('_id'))
        self.stock_id = data.get('stock_id')
        self.date = data.get('date')
        self.predicted_price = data.get('predicted_price')
        self.confidence = data.get('confidence')
        self.direction = data.get('direction')

    @classmethod
    def create(cls, data):
        result = cls.get_collection().insert_one(data)
        return cls.get_by_id(result.inserted_id)

    @classmethod
    def get_by_id(cls, prediction_id):
        data = cls.get_collection().find_one({'_id': ObjectId(prediction_id)})
        return cls(data) if data else None

    @classmethod
    def get_latest_predictions(cls, stock_id, limit=10):
        predictions = cls.get_collection().find(
            {'stock_id': stock_id}
        ).sort('date', -1).limit(limit)
        return [cls(prediction) for prediction in predictions]

    @classmethod
    def get_prediction_accuracy(cls, stock_id, days=30):
        """计算预测准确率"""
        predictions = cls.get_collection().find(
            {'stock_id': stock_id}
        ).sort('date', -1).limit(days)
        
        correct_predictions = 0
        total_predictions = 0
        
        for pred in predictions:
            # 获取实际价格变化
            stock = mongo.db.stocks.find_one({'_id': ObjectId(stock_id)})
            if not stock:
                continue
                
            actual_direction = 'up' if stock['current_price'] > pred['predicted_price'] else 'down'
            if actual_direction == pred['direction']:
                correct_predictions += 1
            total_predictions += 1
        
        return (correct_predictions / total_predictions * 100) if total_predictions > 0 else 0

    def delete(self):
        self.get_collection().delete_one({'_id': ObjectId(self.id)}) 