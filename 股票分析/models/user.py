from bson.objectid import ObjectId
from extensions import mongo
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
import logging # Import logging

# Configure logging
logging.basicConfig(level=logging.ERROR) # Log errors

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
    def create(username, password, email=None):
        # Check if username already exists
        if User.get_by_username(username):
            return None # Indicate failure if username exists

        # Check if email already exists (if provided)
        if email and User.get_by_email(email):
             # Handle email already exists - depends on how you want to signal this
             # Currently, User.create only returns None for username conflict.
             # To handle email conflict specifically, you might need a different return value or raise an exception.
             # For simplicity, we'll assume username conflict is the primary check in User.create returning None.
             pass # Keep existing email check in routes/auth.py

        user_data = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.utcnow(),
            'followers_count': 0,
            'following_count': 0
        }
        if email:
            user_data['email'] = email

        try:
            result = mongo.db.users.insert_one(user_data)
            user_data['_id'] = result.inserted_id

            # 创建索引 (Ensure unique index on username is created)
            # It's better to ensure indexes are created during application startup, e.g., in create_app or init_extensions
            # Calling create_index here on every user creation might be inefficient.
            # For now, keeping it as is based on original code, but note this potential optimization.
            mongo.db.users.create_index([('username', 1)], unique=True)
            if email: # Also ensure unique index on email if you want emails to be unique
                 mongo.db.users.create_index([('email', 1)], unique=True)

            return User(user_data)
        except Exception as e:
            logging.error(f"Error creating user {username}: {e}") # Log the specific error
            return None # Indicate failure

    @staticmethod
    def get_by_id(user_id):
        try:
            user_data = mongo.db.users.find_one({'_id': ObjectId(user_id)})
            return User(user_data) if user_data else None
        except Exception as e:
             logging.error(f"Error getting user by id {user_id}: {e}")
             return None

    @staticmethod
    def get_by_username(username):
        try:
            user_data = mongo.db.users.find_one({'username': username})
            return User(user_data) if user_data else None
        except Exception as e:
             logging.error(f"Error getting user by username {username}: {e}")
             return None

    @staticmethod
    def get_by_email(email):
         try:
            user_data = mongo.db.users.find_one({'email': email})
            return User(user_data) if user_data else None
         except Exception as e:
            logging.error(f"Error getting user by email {email}: {e}")
            return None

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