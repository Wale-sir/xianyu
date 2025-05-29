from bson.objectid import ObjectId
from extensions import mongo
from datetime import datetime

class Search:
    @staticmethod
    def save_search(user_id, query):
        """保存搜索记录"""
        mongo.db.search_history.insert_one({
            'user_id': user_id,
            'query': query,
            'created_at': datetime.utcnow()
        })

    @staticmethod
    def get_recent_searches(user_id, limit=10):
        """获取最近的搜索记录"""
        return list(mongo.db.search_history.find(
            {'user_id': user_id}
        ).sort('created_at', -1).limit(limit))

    @staticmethod
    def clear_history(user_id):
        """清除搜索历史"""
        mongo.db.search_history.delete_many({'user_id': user_id})

    @staticmethod
    def get_popular_searches(limit=10):
        """获取热门搜索"""
        pipeline = [
            {'$group': {
                '_id': '$query',
                'count': {'$sum': 1},
                'last_searched': {'$max': '$created_at'}
            }},
            {'$sort': {'count': -1, 'last_searched': -1}},
            {'$limit': limit}
        ]
        return list(mongo.db.search_history.aggregate(pipeline))

    @staticmethod
    def get_search_suggestions(query, limit=5):
        """获取搜索建议"""
        return list(mongo.db.search_history.find(
            {'query': {'$regex': f'^{query}', '$options': 'i'}}
        ).sort('created_at', -1).limit(limit))

class Share:
    @staticmethod
    def save_share(user_id, food_id, platform):
        """保存分享记录"""
        mongo.db.shares.insert_one({
            'user_id': user_id,
            'food_id': food_id,
            'platform': platform,
            'created_at': datetime.utcnow()
        })

    @staticmethod
    def get_share_stats(food_id):
        """获取分享统计"""
        pipeline = [
            {'$match': {'food_id': food_id}},
            {'$group': {
                '_id': '$platform',
                'count': {'$sum': 1}
            }},
            {'$sort': {'count': -1}}
        ]
        return list(mongo.db.shares.aggregate(pipeline))

    @staticmethod
    def get_user_shares(user_id, limit=10):
        """获取用户的分享记录"""
        return list(mongo.db.shares.find(
            {'user_id': user_id}
        ).sort('created_at', -1).limit(limit)) 