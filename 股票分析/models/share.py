from datetime import datetime
from extensions import mongo
from bson import ObjectId

class Share:
    @classmethod
    def get_collection(cls):
        return mongo.db.shares

    def __init__(self, data):
        self.id = str(data.get('_id'))
        self.user_id = data.get('user_id')
        self.title = data.get('title')
        self.content = data.get('content')
        self.images = data.get('images', [])
        self.likes = data.get('likes', 0)
        self.comments = data.get('comments', [])
        self.created_at = data.get('created_at', datetime.utcnow())
        self.updated_at = data.get('updated_at', datetime.utcnow())

    @classmethod
    def create(cls, data):
        data['created_at'] = datetime.utcnow()
        data['updated_at'] = datetime.utcnow()
        result = cls.get_collection().insert_one(data)
        return cls.get_by_id(result.inserted_id)

    @classmethod
    def get_by_id(cls, share_id):
        data = cls.get_collection().find_one({'_id': ObjectId(share_id)})
        return cls(data) if data else None

    @classmethod
    def get_all_shares(cls, user_id=None, limit=20, skip=0):
        query = {}
        if user_id:
            query['user_id'] = user_id

        shares = cls.get_collection().find(query).sort('created_at', -1).skip(skip).limit(limit)
        return [cls(share) for share in shares]

    def update(self, data):
        data['updated_at'] = datetime.utcnow()
        self.get_collection().update_one(
            {'_id': ObjectId(self.id)},
            {'$set': data}
        )
        return self.get_by_id(self.id)

    def delete(self):
        self.get_collection().delete_one({'_id': ObjectId(self.id)})

    def add_like(self):
        self.get_collection().update_one(
            {'_id': ObjectId(self.id)},
            {'$inc': {'likes': 1}}
        )
        self.likes += 1

    def add_comment(self, user_id, content):
        comment = {
            'user_id': user_id,
            'content': content,
            'created_at': datetime.utcnow()
        }
        self.get_collection().update_one(
            {'_id': ObjectId(self.id)},
            {'$push': {'comments': comment}}
        )
        self.comments.append(comment) 