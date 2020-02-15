#coding:utf-8
from pymongo import MongoClient


uri = 'localhost'
client = MongoClient(uri, 27017)
db = client['nCoV']


class DB:
    def __init__(self):
        self.db = db

    def insert(self, collection, data):
        self.db[collection].insert(data)

    def find_one(self, collection, data=None):
        return self.db[collection].find_one(data)
