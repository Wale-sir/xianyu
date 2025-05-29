from bson.objectid import ObjectId
from extensions import mongo
from datetime import datetime
from models.user import User

class Relationship:
    @staticmethod
    def follow(follower_id, following_id):
        """关注用户"""
        # 确保 ID 是 ObjectId 类型
        follower_id = ObjectId(follower_id)
        following_id = ObjectId(following_id)
        
        # 检查是否已经关注
        if Relationship.is_following(str(follower_id), str(following_id)):
            return True  # 已经关注，返回 True 表示操作成功
            
        # 创建关注关系
        mongo.db.relationships.insert_one({
            'follower_id': follower_id,
            'following_id': following_id,
            'created_at': datetime.utcnow()
        })
        
        # 更新关注数
        mongo.db.users.update_one(
            {'_id': follower_id},
            {'$inc': {'following_count': 1}}
        )
        mongo.db.users.update_one(
            {'_id': following_id},
            {'$inc': {'followers_count': 1}}
        )
        return True

    @staticmethod
    def unfollow(follower_id, following_id):
        """取消关注"""
        # 确保 ID 是 ObjectId 类型
        follower_id = ObjectId(follower_id)
        following_id = ObjectId(following_id)
        
        # 删除关注关系
        result = mongo.db.relationships.delete_one({
            'follower_id': follower_id,
            'following_id': following_id
        })
        
        # 如果成功删除了关注关系，更新关注数
        if result.deleted_count > 0:
            mongo.db.users.update_one(
                {'_id': follower_id},
                {'$inc': {'following_count': -1}}
            )
            mongo.db.users.update_one(
                {'_id': following_id},
                {'$inc': {'followers_count': -1}}
            )
            return True
        return False

    @staticmethod
    def get_followers(user_id):
        """获取粉丝列表"""
        followers = mongo.db.relationships.find(
            {'following_id': ObjectId(user_id)}
        ).sort('created_at', -1)
        return [User.get_by_id(str(f['follower_id'])) for f in followers]

    @staticmethod
    def get_following(user_id):
        """获取关注列表"""
        following = mongo.db.relationships.find(
            {'follower_id': ObjectId(user_id)}
        ).sort('created_at', -1)
        return [User.get_by_id(str(f['following_id'])) for f in following]

    @staticmethod
    def is_following(follower_id, following_id):
        """检查是否已关注"""
        return bool(mongo.db.relationships.find_one({
            'follower_id': ObjectId(follower_id),
            'following_id': ObjectId(following_id)
        }))

class Message:
    @staticmethod
    def send(sender_id, receiver_id, content):
        """发送私信"""
        message = {
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'content': content,
            'is_read': False,
            'created_at': datetime.utcnow()
        }
        return mongo.db.messages.insert_one(message)

    @staticmethod
    def get_conversation(user1_id, user2_id, limit=50):
        """获取两个用户之间的对话"""
        return list(mongo.db.messages.find({
            '$or': [
                {'sender_id': user1_id, 'receiver_id': user2_id},
                {'sender_id': user2_id, 'receiver_id': user1_id}
            ]
        }).sort('created_at', -1).limit(limit))

    @staticmethod
    def get_unread_count(user_id):
        """获取未读消息数"""
        return mongo.db.messages.count_documents({
            'receiver_id': user_id,
            'is_read': False
        })

    @staticmethod
    def mark_as_read(user_id, sender_id):
        """标记消息为已读"""
        mongo.db.messages.update_many({
            'receiver_id': user_id,
            'sender_id': sender_id,
            'is_read': False
        }, {
            '$set': {'is_read': True}
        })

    @staticmethod
    def get_conversations(user_id):
        """获取用户的所有对话列表"""
        conversations = []
        # 获取用户发送和接收的所有消息
        messages = mongo.db.messages.find({
            '$or': [
                {'sender_id': ObjectId(user_id)},
                {'receiver_id': ObjectId(user_id)}
            ]
        }).sort('created_at', -1)
        
        # 用于记录已经处理过的对话
        processed = set()
        
        for msg in messages:
            # 确定对话的另一方
            other_user_id = msg['receiver_id'] if str(msg['sender_id']) == user_id else msg['sender_id']
            other_user_id = str(other_user_id)
            
            # 如果这个对话已经处理过，跳过
            if other_user_id in processed:
                continue
                
            # 获取未读消息数
            unread_count = mongo.db.messages.count_documents({
                'sender_id': ObjectId(other_user_id),
                'receiver_id': ObjectId(user_id),
                'read': False
            })
            
            conversations.append({
                'user': User.get_by_id(other_user_id),
                'last_message': msg['content'],
                'unread_count': unread_count
            })
            
            processed.add(other_user_id)
            
        return conversations 