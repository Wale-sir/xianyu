from extensions import mongo

def create_indexes():
    # 删除旧的 email 索引
    try:
        mongo.db.users.drop_index('email_1')
    except:
        pass
    
    # 美食集合索引
    mongo.db.foods.create_index('name')
    mongo.db.foods.create_index('user_id')
    mongo.db.foods.create_index('price')
    mongo.db.foods.create_index('rating')
    mongo.db.foods.create_index('favorites')
    mongo.db.foods.create_index('created_at')
    mongo.db.foods.create_index('tags')
    mongo.db.foods.create_index('favorite_users')
    mongo.db.foods.create_index([('location', '2dsphere')])
    mongo.db.foods.create_index([('name', 'text'), ('description', 'text')])
    
    # 用户集合索引
    mongo.db.users.create_index([('username', 1)], unique=True)
    mongo.db.users.create_index('followers_count')
    mongo.db.users.create_index('following_count')
    
    # 评论索引
    mongo.db.foods.create_index('reviews.user_id')
    mongo.db.foods.create_index('reviews.created_at')
    
    # 文件索引
    mongo.db.fs.files.create_index('filename')
    mongo.db.fs.files.create_index('uploadDate')
    
    # 社交关系索引
    mongo.db.relationships.create_index([('follower_id', 1), ('following_id', 1)], unique=True)
    mongo.db.relationships.create_index([('follower_id', 1)])
    mongo.db.relationships.create_index([('following_id', 1)])
    mongo.db.relationships.create_index('created_at')
    
    # 消息索引
    mongo.db.messages.create_index([('sender_id', 1), ('receiver_id', 1)])
    mongo.db.messages.create_index([('created_at', -1)])
    mongo.db.messages.create_index([('receiver_id', 1), ('is_read', 1)])
    
    # 搜索历史索引
    mongo.db.search_history.create_index([('user_id', 1), ('created_at', -1)])
    mongo.db.search_history.create_index('query')
    
    # 分享记录索引
    mongo.db.shares.create_index([('user_id', 1), ('created_at', -1)])
    mongo.db.shares.create_index('food_id')
    mongo.db.shares.create_index('platform') 