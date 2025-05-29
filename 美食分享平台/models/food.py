from bson.objectid import ObjectId
from extensions import mongo
from datetime import datetime
from models.user import User

class Food:
    def __init__(self, food_data):
        self.id = str(food_data['_id'])
        self.name = food_data['name']
        self.description = food_data.get('description', '')
        self.price = food_data.get('price', 0)
        self.image = food_data.get('image')
        if self.image:
            try:
                if isinstance(self.image, ObjectId):
                    self.image = str(self.image)
                elif not isinstance(self.image, str):
                    self.image = str(self.image)
            except Exception as e:
                print(f"Error processing image ID: {str(e)}")
                self.image = None
        self.location = food_data.get('location', {
            'type': 'Point',
            'coordinates': [0, 0]
        })
        self.user_id = food_data['user_id']
        # 获取用户信息
        user = User.get_by_id(self.user_id)
        self.username = user.username if user else 'Unknown User'
        self.tags = food_data.get('tags', [])
        self.rating = food_data.get('rating', 0)
        self.reviews = food_data.get('reviews', [])
        self.favorites = food_data.get('favorites', 0)
        self.created_at = food_data.get('created_at', datetime.utcnow())
        self.updated_at = food_data.get('updated_at', datetime.utcnow())

    @staticmethod
    def create(name, user_id, description='', price=0, image=None, location=None, tags=None):
        food_data = {
            'name': name,
            'description': description,
            'price': price,
            'image': image,
            'location': location or {
                'type': 'Point',
                'coordinates': [0, 0]
            },
            'user_id': user_id,
            'tags': tags or [],
            'rating': 0,
            'reviews': [],
            'favorites': 0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = mongo.db.foods.insert_one(food_data)
        food_data['_id'] = result.inserted_id
        return Food(food_data)

    @staticmethod
    def get_by_id(food_id):
        print(f"Querying food with ID: {food_id}")
        try:
            if not food_id:
                print("Error: food_id is None or empty")
                return None
                
            try:
                food_id = ObjectId(food_id)
            except Exception as e:
                print(f"Error converting food_id to ObjectId: {str(e)}")
                return None
                
            food_data = mongo.db.foods.find_one({'_id': food_id})
            print(f"Query result: {food_data}")
            
            if not food_data:
                print("No food found with the given ID")
                return None
                
            return Food(food_data)
        except Exception as e:
            print(f"Error in get_by_id: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return None

    @staticmethod
    def get_by_user(user_id):
        foods = mongo.db.foods.find({'user_id': user_id})
        return [Food(food) for food in foods]

    @staticmethod
    def get_all():
        return mongo.db.foods.find()

    def update(self, data):
        update_data = {}
        
        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'price' in data:
            update_data['price'] = data['price']
        if 'image' in data:
            update_data['image'] = data['image']
        if 'location' in data:
            update_data['location'] = data['location']
        if 'tags' in data:
            update_data['tags'] = data['tags']
        
        if update_data:
            update_data['updated_at'] = datetime.utcnow()
            mongo.db.foods.update_one(
                {'_id': ObjectId(self.id)},
                {'$set': update_data}
            )
            
            # 更新实例属性
            for key, value in update_data.items():
                setattr(self, key, value)

    def delete(self):
        mongo.db.foods.delete_one({'_id': ObjectId(self.id)})

    @staticmethod
    def get_nearby(longitude, latitude, max_distance=10000):
        return list(mongo.db.foods.find({
            'location': {
                '$near': {
                    '$geometry': {
                        'type': 'Point',
                        'coordinates': [float(longitude), float(latitude)]
                    },
                    '$maxDistance': int(max_distance)
                }
            }
        }))
    
    @staticmethod
    def search(query):
        return list(mongo.db.foods.find(
            {'$text': {'$search': query}},
            {'score': {'$meta': 'textScore'}}
        ).sort([('score', {'$meta': 'textScore'})]))
    
    @staticmethod
    def get_by_price_range(min_price, max_price):
        return list(mongo.db.foods.find({
            'price': {'$gte': float(min_price), '$lte': float(max_price)}
        }).sort('price', 1))
    
    @staticmethod
    def get_by_rating(min_rating):
        return list(mongo.db.foods.find({
            'rating': {'$gte': float(min_rating)}
        }).sort('rating', -1))
    
    @staticmethod
    def get_popular_tags(limit=10):
        pipeline = [
            {'$unwind': '$tags'},
            {'$group': {'_id': '$tags', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}},
            {'$limit': limit}
        ]
        return list(mongo.db.foods.aggregate(pipeline))
    
    @staticmethod
    def add_review(food_id, user_id, rating, comment):
        # Get user information
        user = User.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
            
        review = {
            'user_id': user_id,
            'username': user.username,  # Add username to the review
            'rating': float(rating),
            'comment': comment,
            'created_at': datetime.utcnow()
        }
        
        # 更新评论
        mongo.db.foods.update_one(
            {'_id': ObjectId(food_id)},
            {'$push': {'reviews': review}}
        )
        
        # 更新平均评分
        food = mongo.db.foods.find_one({'_id': ObjectId(food_id)})
        if food and food['reviews']:
            total_rating = sum(r['rating'] for r in food['reviews'])
            avg_rating = total_rating / len(food['reviews'])
            mongo.db.foods.update_one(
                {'_id': ObjectId(food_id)},
                {'$set': {'rating': avg_rating}}
            )
    
    @staticmethod
    def add_favorite(food_id, user_id):
        mongo.db.foods.update_one(
            {'_id': ObjectId(food_id)},
            {
                '$inc': {'favorites': 1},
                '$addToSet': {'favorite_users': user_id}
            }
        )
    
    @staticmethod
    def remove_favorite(food_id, user_id):
        mongo.db.foods.update_one(
            {'_id': ObjectId(food_id)},
            {
                '$inc': {'favorites': -1},
                '$pull': {'favorite_users': user_id}
            }
        )
    
    @staticmethod
    def get_by_tag(tag):
        return list(mongo.db.foods.find({'tags': tag}))
    
    @staticmethod
    def get_popular_foods(limit=10):
        return list(mongo.db.foods.find().sort('favorites', -1).limit(limit))
    
    @staticmethod
    def get_recent_foods(limit=10):
        return list(mongo.db.foods.find().sort('created_at', -1).limit(limit))
    
    @staticmethod
    def get_user_favorites(user_id):
        return list(mongo.db.foods.find({'favorite_users': user_id}))
    
    @staticmethod
    def get_user_reviews(user_id):
        pipeline = [
            {'$unwind': '$reviews'},
            {'$match': {'reviews.user_id': user_id}},
            {'$project': {
                'food_id': '$_id',
                'food_name': '$name',
                'rating': '$reviews.rating',
                'comment': '$reviews.comment',
                'created_at': '$reviews.created_at'
            }}
        ]
        return list(mongo.db.foods.aggregate(pipeline)) 