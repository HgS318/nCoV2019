#coding:utf-8
import requests
import pymongo
import time
import json
import random
import pandas as pd

# 伪装请求头
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'referer': 'https://news.qq.com/zt2020/page/feiyan.htm?from=timeline&isappinstalled=0'
}
requests.packages.urllib3.disable_warnings()


class MongoDBPipeline(object):

    def __init__(self):
        self.clinet = pymongo.MongoClient("localhost", 27017)
        # self.clinet = pymongo.MongoClient("106.12.56.213", 27017)
        db = self.clinet["nCoV_pTrack"]
        self.db = db

    def insert_data(self, tb_name, new_dict, db=None):
        tb = self.db[tb_name]
        if db is not None:
            tb = self.clinet[db][tb_name]
        tb.insert_one(new_dict)

    def insert_many(self, tb_name, new_data, db=None):
        tb = self.db[tb_name]
        if db is not None:
            tb = self.clinet[db][tb_name]
        new_dict = None
        if isinstance(new_data, list):
            new_dict = dict()
            for _data in new_data:
                new_dict[_data['_id']] = _data
        tb.insert_many(new_dict)

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


def query_patent_track(citycode, page, size=100):
    query_url = "https://iflow-api.uc.cn/feiyan/track?page={}&size={}&citycode={}".\
        format(str(page), str(size), citycode)
    try:
        res = requests.get(query_url, verify=False, headers=headers, timeout=60000)
        obj = res.json()
        tracks = obj['data']['trackes']
        if len(tracks) < 1:
            return None
        return tracks
    except:
        print("error in city: %s, page: %d" %(citycode, page))
        return None


def get_save_city_tracks(city, mongo, tb, df, size=100):
    if 'citycode' not in city:
        return
    try:
        sure_cnt = int(city['sure_cnt'])
    except:
        sure_cnt = 1000000
    for page in range(0, sure_cnt):
        tracks = query_patent_track(city['citycode'], page, size=size)
        if tracks is None:
            break
        # 保存进DataFrame （csv准备）
        for track in tracks:
            try:
                df.loc[len(df)] = track
            except:
                print("add to csv DataFrame error: " + str(track))
            try:
                if 'id' in track:
                    track['_id'] = track['province'] + "-" + track['city'] + '-' + str(track['id'])
                else:
                    track['_id'] = track['province'] + "-" + track['city'] + '-' + str(track['index'])
            except:
                if "id" in track:
                    track['_id'] = track["id"]
            try:
                mongo.insert_data(tb, track, db="nCoV_pTrack")
            except:
                print("insert mongo error: " + str(track))
        # 写入mongodb
        # mongo.insert_many(tb, tracks, db="nCoV_pTrack")
        time.sleep(random.randint(1, 4))
        if len(tracks) < size:
            print("city of %s collected..." %city['citycode'])
            break


pipeline = MongoDBPipeline()
time_str = time.strftime("%m%d-%H%M", time.localtime())
tb_name = time_str
csv_path = "tracks_" + time_str + ".csv"

pre_url = "https://iflow-api.uc.cn/feiyan/track?page=0&size=10&city=1&citycode=340800"
requests.adapters.DEFAULT_RETRIES = 5
pre_res = requests.get(pre_url, verify=False, headers=headers, timeout=60000)
pre_json = pre_res.json()
cities = pre_json['data']['cities']
for city in cities:
    try:
        _id = city['one_level_area'] + "_" + city['two_level_area']
        city['_id'] = _id
    except:
        print("error in pre_processing:" + str(city))
# 各市疫情总体信息存储在MongoDb中
pipeline.insert_data("cities", {"_id": time_str, "cities": cities}, db="nCoV_pTrack")
df = pd.DataFrame(columns=['id', 'province', 'city', 'index', 'source',
                           'base_info', 'detail_info'])
# 开始抓取每个市的患者轨迹数据
for city in cities:
    get_save_city_tracks(city, pipeline, tb_name, df, size=100)

df.to_csv(csv_path, encoding='utf-8', header=True, index=False)
