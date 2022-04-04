from elasticsearch import Elasticsearch
from datetime import datetime
# connect to the database
es = Elasticsearch("http://192.168.231.73:9200/")


# request body for set the database 
request_body = {
    "settings" : {
        "number_of_shards": 1,
        "number_of_replicas": 1
    },
    'mappings': {
        'properties': {
            'user_id': {'type': 'keyword'},
            'amount': {'type': 'double'},
            'symbol': {'type': 'text'},
            'volume': {'type': 'double'},
            'price': {'type': 'double'},
            'buyed': {'type': 'boolean'},
            'buy_time': {'type':   'date',
                        'format': 'yyyy-MM-dd HH:mm:ss'}
        } 
    }
}

# create the database index for profile 
print("creating 'tooBors-orders' index...")
es.indices.create(index = 'toobors-orders', mappings= request_body['mappings'], settings=request_body["settings"])

# make the first index for test
es.index(index='toobors-orders', document={
  "user_id": "SS1f7n8BOq_1BB0R9j0H",
  "amount": 10000000,
  'symbol': '',
  'volume': 150,
  'price': 1000,
  'buyed': True,
  'buy_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
})