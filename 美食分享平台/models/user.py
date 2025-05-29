from bson.objectid import ObjectId
from extensions import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

class User(UserMixin):
    def __init__(self, user_data):
        self.id = str(user_data['_id'])
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']
        self.created_at = user_data.get('created_at', datetime.utcnow())
        # 从数据库中获取最新的关注数
        user_stats = mongo.db.users.find_one(
            {'_id': ObjectId(self.id)},
            {'followers_count': 1, 'following_count': 1}
        )
        self.followers_count = user_stats.get('followers_count', 0) if user_stats else 0
        self.following_count = user_stats.get('following_count', 0) if user_stats else 0

    @staticmethod
    def create(username, password):
        if User.get_by_username(username):
            return None
        
        user_data = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.utcnow(),
            'followers_count': 0,
            'following_count': 0
        }
        
        result = mongo.db.users.insert_one(user_data)
        user_data['_id'] = result.inserted_id
        
        # 创建索引
        mongo.db.users.create_index([('username', 1)], unique=True)
        
        return User(user_data)

    @staticmethod
    def get_by_id(user_id):
        user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
        return User(user_data) if user_data else None

    @staticmethod
    def get_by_username(username):
        user_data = mongo.db.users.find_one({'username': username})
        return User(user_data) if user_data else None

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def update_profile(self, data):
        update_data = {}
        
        if 'username' in data:
            update_data['username'] = data['username']
        
        if update_data:
            mongo.db.users.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': update_data}
            )
            
            # 更新实例属性
            for key, value in update_data.items():
                setattr(self, key, value)

    def update_password(self, new_password):
        mongo.db.users.update_one(
            {'_id': ObjectId(self.id)},
            {'$set': {'password_hash': generate_password_hash(new_password)}}
        )
        self.password_hash = generate_password_hash(new_password) 