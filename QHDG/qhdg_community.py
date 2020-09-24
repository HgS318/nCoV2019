#coding:utf-8
import requests
import pymongo
import time
import json
import os
import pandas as pd


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
        tb.insert_one(new_dict)

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

    
def get_json_obj(res_text, time_str=None):
    json_text = res_text.strip().strip(";").replace('\'', '\"')
    equal_index = json_text.find('=')
    if -1 < equal_index < 30:
        json_text = json_text[equal_index + 1:]
        json_text = json_text.strip()
    try:
        obj = json.loads(json_text)
        if time_str is not None:
            obj['_id'] = time_str
        return obj
    except Exception as json_err:
        print("parse json error...")
        return None


def json2csv(obj, csv_path):
    data_list = []
    for province_name in obj["community"]:
        for city_name in obj["community"][province_name]:
            for area_name in obj["community"][province_name][city_name]:
                for community in obj["community"][province_name][city_name][area_name]:
                    data_list.append(community)
    df = pd.DataFrame(columns=['id', 'name', 'lng', 'lat', 'address', 'city', 'province', 'count', 'full_address'])
    i = 0
    for community_item in data_list:
        if 'lng' in community_item and 'lat' in community_item:
            community_obj = {
                # 'id': community_item["id"],
                'name': community_item["community"],
                'lng': community_item['lng'],
                'lat': community_item['lat'],
                'city': community_item['city'],
                'province': community_item['province'],
                'address': community_item['show_address'],
                'full_address': community_item['full_address']
            }
            if 'id' in community_item:
                community_obj['id'] = community_item["id"]
            else:
                community_obj['id'] = i
            community_obj['count'] = 1
            try:
                if 'cnt_sum_certain' in community_item and int(community_item['cnt_sum_certain']) > 0:
                    community_obj['count'] = community_item['cnt_sum_certain']
            except:
                community_obj['count'] = 1
            df.loc[i] = community_obj
            i += 1
            if i % 500 == 0:
                print(str(i) + " data processed...")
    df.to_csv(csv_path, encoding='utf-8', header=True, index=False)


def convert_csvs():
    path = './qh_data/'
    files = os.listdir(path)
    for file_name in files:
        if ".js" in file_name:
            with open(path + file_name, 'r', encoding='utf-8') as file:
                js_txt = file.read()
            obj = get_json_obj(js_txt)
            json2csv(obj, path + file_name.replace(".js", ".csv"))
            print(file_name + " converted...")


def fetch_commubities():
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
            obj = get_json_obj(res_text, time_str)
            if obj is not None:
                try:
                    pipeline = MongoDBPipeline()
                    pipeline.insert_data("QHDG", obj, db="nCoV")
                    print("insert mongo ok.")
                except:
                    print("insert mongo error...")
                try:
                    json2csv(obj, save_name.replace(".js", ".csv"))
                    print("save csv ok: " + save_name.replace(".js", ".csv"))
                except Exception as csv_exp:
                    print("save csv error...")
        else:
            print("get data error...")
    except Exception as exp:
        print("get data error...")


if __name__ == '__main__':
    fetch_commubities()
    # convert_csvs()
