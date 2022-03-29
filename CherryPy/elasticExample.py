from errno import ENOEXEC
from elasticsearch import Elasticsearch
import json
import base64
import pandas as pd
es = Elasticsearch("http://192.168.231.73:9200/")
username = 'mgh27'
query_body = {
    'query': {
        'match':{
            'username' : username
        }
    }
}
res = es.search(index='toobors-profile', body=query_body)
id = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_id']['username']

print(id)
# x = pd.concat(map(pd.DataFrame.from_dict, res), axis=1)['hits']
# print ("total hits:", len(res["hits"]["hits"]))
# print(x)