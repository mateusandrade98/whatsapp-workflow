from uuid import uuid4
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.cursor import Cursor
from pymongo.database import Database
from bson import ObjectId
from ujson import loads, dumps, JSONDecodeError
from redis import Redis as ModuleRedis
from urllib.parse import quote_plus


class Cache:
    def __init__(self, Env: dict):
        self.Env = Env
        self.Redis = Redis(Env=self.Env)
        self.MongoDB = MongoDB(Env=self.Env)

    def getRedis(self):
        return self.Redis

    def getMongoDB(self):
        return self.MongoDB

    def get(self, name: str) -> dict:
        cache = self.Redis.get(prefix='cache', key=name)

        if not cache:
            cache = self.MongoDB.findOne(filter={'key': name}, collection='cache')
            if cache:
                self.Redis.set(prefix='cache', key=name, values=cache)

        return cache

    def set(self, name: str, values: dict) -> dict:
        if self.Redis.set(prefix='cache', key=name, values=values):
            n = {'isCache': True, 'key': name}
            n.update(values)

            if type(n.get('_id') != ObjectId):
                n['_id'] = ObjectId(n['_id'])

            return self.MongoDB.set(data=n, prefix='cache', collection='cache')

    def clear(self, name: str) -> bool:
        self.Redis.delete(prefix='cache', key=name)
        return self.MongoDB.delete(filter={'key': name}, collection='cache')


class MongoDB:
    def __init__(self, Env: dict):
        self.Env = Env
        self.conn = None
        self.db = None
        self.collection = None

    def generateKey(self, prefix: str = 'bot') -> str:
        return ''.join((prefix, uuid4().hex))

    def getDB(self) -> Database:
        if self.conn is None:
            self.conn = self.connection()

        return self.conn['botManager']

    def getCollection(self, name: str) -> Collection:
        if self.conn is None:
            self.conn = self.connection()

        if self.db is None:
            self.db = self.getDB()

        self.collection = self.db[name]

        return self.collection

    def findOne(self, filter: dict, collection: str = 'Bots') -> dict:
        if self.conn is None:
            self.conn = self.connection()

        self.collection = self.getCollection(name=collection)

        result = self.collection.find_one(filter=filter)

        if result:
            n_values = {}
            for key in result:
                if type(result[key]) != str and not type(result[key]) == dict:
                    result[key] = str(result[key])
                n_values.update({key: result[key]})
            return n_values
        return {}

    def findAll(self, filter: dict, collection: str = 'Bots') -> Cursor:
        if self.conn is None:
            self.conn = self.connection()

        self.collection = self.getCollection(name=collection)

        return self.collection.find(filter=filter)

    def delete(self, filter: dict, collection: str = 'Bots') -> bool:
        if self.conn is None:
            self.conn = self.connection()

        self.collection = self.getCollection(name=collection)

        result = self.collection.delete_one(
            filter=filter
        )

        return result.deleted_count > 0

    def set(self, _id: str = '', uid: str = '', data: dict = None, collection: str = 'Bots', prefix: str = '') -> dict:
        if not data:
            return {}

        if self.conn is None:
            self.conn = self.connection()

        self.collection = self.getCollection(name=collection)

        data['uid'] = uid if uid else self.generateKey(prefix=prefix)

        _get = {}

        if _id:
            _get = self.findOne(filter={'_id': ObjectId(_id)})

        if uid and not _id:
            _get = self.findOne(filter={'uid': uid})

        if not _get:
            insert = self.collection.insert_one(
                document=data
            )

            if type(data.get('_id')) == ObjectId:
                data['_id'] = ObjectId(data['_id']).__str__()

            if self.collection.count_documents(filter={'_id': insert.inserted_id}):
                result = {'insert': 1, 'values': data}
            else:
                result = {'insert': 0, 'values': {}}
        else:
            if type(_get.get('_id')) != ObjectId:
                _get['_id'] = ObjectId(_get['_id'])

            n_data = _get
            n_data.update(data)

            update = self.collection.update_one(
                filter={'_id': _get.get('_id')},
                update={"$set": n_data},
                upsert=True
            )

            if type(n_data.get('_id')) == ObjectId:
                n_data['_id'] = ObjectId(n_data['_id']).__str__()

            if update.modified_count:
                result = {'update': 1, 'values': n_data}
            else:
                result = {'update': 0, 'values': {}}

        return result

    def connection(self) -> MongoClient:
        if self.Env.get('mongodb_password'):
            uri = "mongodb://%s:%s@%s" % (
                quote_plus(self.Env.get('mongodb_username')), quote_plus(self.Env.get('mongodb_password')),
                ':'.join((self.Env.get('mongodb_host'), str(self.Env.get('mongodb_port')))))
        else:
            uri = "mongodb://%s" % (':'.join((self.Env.get('mongodb_host'), str(self.Env.get('mongodb_port')))))

        self.conn = MongoClient(uri)

        return self.conn

    def close(self) -> bool:
        if self.conn is None:
            return False

        self.conn.close()
        self.conn = None

        return True


class Redis:
    def __init__(self, Env: dict):
        self.Env = Env
        self.conn = None

    def generateKey(self) -> str:
        return uuid4().hex

    def expire(self, prefix: str = "cache", key: str = "", ttl: int = 600) -> bool:
        if not key:
            return False

        if self.conn is None:
            self.conn = self.connection()

        return self.conn.expire(
            name="{}:{}".format(prefix, key),
            time=ttl
        )

    def delete(self, prefix: str = "cache", key: str = "") -> bool:
        if not key:
            return False

        if self.conn is None:
            self.conn = self.connection()

        count = 0
        for key in self.conn.scan_iter('{}:*'.format(prefix)):
            self.conn.delete(key)
            count += 1

        return count > 0

    def get(self, prefix: str = "cache", key: str = "") -> dict:
        if not key:
            return {}

        if self.conn is None:
            self.conn = self.connection()

        try:
            result = self.conn.get(
                name='{}:{}'.format(prefix, key)
            )
            if result:
                return loads(result)
            return {}
        except JSONDecodeError:
            return {}

    def set(self, prefix: str = "cache", key: str = "", values: dict = None, ttl: int = 600) -> bool:
        if not values:
            return False

        if not key:
            key = self.generateKey()

        if self.conn is None:
            self.conn = self.connection()

        self.conn.set(
            name='{}:{}'.format(prefix, key),
            value=dumps(values)
        )

        return self.expire(
            prefix=prefix,
            key=key,
            ttl=ttl
        )

    def connection(self) -> ModuleRedis:
        if self.Env.get('redis_password'):
            self.conn = ModuleRedis(
                host=self.Env.get('redis_host'),
                port=self.Env.get('redis_port'),
                db=self.Env.get('redis_db'),
                password=self.Env.get('redis_password')
            )
        else:
            self.conn = ModuleRedis(
                host=self.Env.get('redis_host'),
                port=self.Env.get('redis_port'),
                db=self.Env.get('redis_db')
            )

        return self.conn

    async def close(self) -> bool:
        if not self.conn is None:
            self.conn.close()
            self.conn = None
            return True
        return False
