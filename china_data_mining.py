# —*— coding: utf-8 —*—
import requests
import json
import time
import pandas as pd
import pymongo


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


# 请求的URL
url = 'https://view.inews.qq.com/g2/getOnsInfo?name=disease_h5&callback=&_=%d'

# 伪装请求头
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
    'referer': 'https://news.qq.com/zt2020/page/feiyan.htm?from=timeline&isappinstalled=0'
}

tims_sec = time.time()

# 抓取数据
result_info = requests.get(url % tims_sec, headers=headers)

res_data = json.loads(result_info.text)
data = json.loads(res_data['data'])

lastUpdateTime = data['lastUpdateTime']
print('数据服务更新时间 ' + str(lastUpdateTime))

areaTree = data['areaTree']

# 创建空 dataframe
col_names = ['_id', '省', '市', '确认', '疑似', '死亡', '治愈']
col_names_p = ['_id', '省','确认', '疑似', '死亡', '治愈']
my_df = pd.DataFrame(columns=col_names)
my_df_p = pd.DataFrame(columns=col_names_p)

i = 0
pi = 0
for item in areaTree:
    if item['name'] == '中国':
        item_ps = item['children']
        for item_p in item_ps:
            province = item_p['name']
            confirm = item_p['total']['confirm']
            death = item_p['total']['dead']
            suspect = item_p['total']['suspect']
            heal = item_p['total']['heal']
            data_dict = {'_id': i, '省': province, '确认': confirm,
                         '疑似': suspect, '死亡': death, '治愈': heal}
            my_df_p.loc[len(my_df_p)] = data_dict
            pi += 1
            # print(province)
            item_cs = item_p['children']
            for item_c in item_cs:
                prefecture = item_c['name']
                # print('  ' + prefecture)
                # print('  ' + str(item_c['total']))
                confirm = item_c['total']['confirm']
                suspect = item_c['total']['suspect']
                death = item_c['total']['dead']
                heal = item_c['total']['heal']

                i += 1
                # 向df添加数据
                # data_dict = {'_id': i, '省': province, '市':prefecture, '确认': confirm, '死亡': death, '治愈': heal}
                data_dict = {'_id': i, '省': province, '市':prefecture, '确认': confirm,
                             '疑似': suspect, '死亡': death, '治愈': heal}
                my_df.loc[len(my_df)] = data_dict
                # my_df.append([data_dict], ignore_index=True)

save_name = "./data/nCoV_China_" + str(lastUpdateTime).split()[0] + "_col_" + time.strftime("%Y%m%d-%H%M", time.localtime())
# 保存数据
my_df.to_csv(save_name + ".csv", encoding='utf-8', header=True, index=False)
my_df_p.to_csv(save_name + "_p.csv", encoding='utf-8', header=True, index=False)
print(save_name + " saved.")

pipeline = MongoDBPipeline()


def dateArr2Dict(arr, field='name', sub_field=None):
    if isinstance(arr, dict):
        return arr
    dict_data = dict()
    for _obj in arr:
        _key = _obj[field]
        if sub_field is not None and sub_field in _obj:
            # _obj[sub_field] = dateArr2Dict(_obj[sub_field], field=field, sub_field=sub_field)
            sub_dict_data = dateArr2Dict(_obj[sub_field], field=field, sub_field=sub_field)
            for sub_key in sub_dict_data:
                _obj[sub_key] = sub_dict_data[sub_key]
            del _obj[sub_field]
        dict_data[_key.replace('.', '-')] = _obj
    return dict_data


try:
    data['_id'] = lastUpdateTime
    new_dict = data.copy()
    new_dict["chinaDayList"] = dateArr2Dict(new_dict["chinaDayList"], field='date')
    new_dict["chinaDayAddList"] = dateArr2Dict(new_dict["chinaDayAddList"], field='date')
    new_dict["areaTree"] = dateArr2Dict(new_dict["areaTree"], field='name', sub_field="children")
    pipeline.insert_data("RT", data, db="nCoV")
    pipeline.insert_data("RTD", new_dict, db="nCoV")
    print("Mongo inserted...")
except:
    print("Did not insert into mongo...")

