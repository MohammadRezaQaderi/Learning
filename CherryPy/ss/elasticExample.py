from elasticsearch import Elasticsearch
import pandas as pd
es = Elasticsearch("http://192.168.231.73:9200/")
exist_query_body = {
    'query': {
        'match':{
            'user_id' : 'mgh27'
        }
    }
}
res = es.search(index='toobors-orders', body=exist_query_body)
amount = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_source']['amount']
print(amount)