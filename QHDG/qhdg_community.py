#coding:utf-8
import requests
import pymongo
import time
import json


class MongoDBPipeline(object):

    def __init__(self):
        self.clinet = pymongo.MongoClient("localhost", 27017)
        # self.clinet = pymongo.MongoClient("106.12.56.213", 27017)
        db = self.clinet["nCoV"]
        self.db = db

    def insert_data(self, tb_name, new_dict, db=None):
        tb = self.db[tb_name]
        if db is not None:
            tb = self.clinet[db][tb_name]
        tb.insert(new_dict)

    def search(self, tb_name, search_query, fields=None, db=None):
        tb = self.db[tb_name]
        if db is not None:
            tb = self.clinet[db][tb_name]
        show_query = None
        if fields is not None:
            show_query = dict()
            for field in fields:
                show_query[field] = 1
        data = []
        for line in tb.find(search_query, show_query):
            one_data = dict()
            for key in line.keys():
                one_data[key] = line[key]
            data.append(one_data)
        return data

    def update_data(self, tb_name, _id, new_dict, db=None):
        tb = self.db[tb_name]
        if db is not None:
            tb = self.clinet[db][tb_name]
        tb.update_one({'_id': _id}, {'$set': new_dict})

    def update_many(self, tb_name, filter, new_dict, db=None):
        tb = self.db[tb_name]
        if db is not None:
            tb = self.clinet[db][tb_name]
        tb.update(filter, {'$set': new_dict}, upsert=True)


# com_js_url = 'https://ncov.deepeye.tech/javascripts/community_query.js'
com_js_url = 'https://ncov.deepeye.tech/javascripts/community.js'

# 伪装请求头
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'referer': 'https://news.qq.com/zt2020/page/feiyan.htm?from=timeline&isappinstalled=0'
}
try:
    requests.adapters.DEFAULT_RETRIES = 5
    res = requests.get(com_js_url, headers=headers, timeout=60000)
    res_text = res.text
    if len(res_text) > 50:
        time_str = time.strftime("%m%d-%H%M", time.localtime())
        save_name = "./qh_data/community_" + time_str + ".js"
        with open(save_name, 'w', encoding='utf-8') as file:
            file.write(res_text)
        print("save file ok: " + save_name)
        json_text = res_text.strip().strip(";").replace('\'', '\"')
        equal_index = json_text.find('=')
        if -1 < equal_index < 30:
            json_text = json_text[equal_index + 1: ]
            json_text = json_text.strip()
        try:
            obj = json.loads(json_text)
            obj['_id'] = time_str
        except:
            print("parse json error...")
        try:
            pipeline = MongoDBPipeline()
            pipeline.insert_data("QGDG", obj, db="nCoV")
            print("insert mongo ok.")
        except:
            print("insert mongo error...")
    else:
        print("get data error...")
except:
    print("get data error...")
