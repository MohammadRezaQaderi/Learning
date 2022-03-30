from asyncio.windows_events import NULL
from elasticsearch import Elasticsearch

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
        }
    }
}

# create the database index for profile 
print("creating 'tooBors-order' index...")
es.indices.create(index = 'toobors-order', mappings= request_body['mappings'], settings=request_body["settings"])

# make the first index for test
es.index(index='toobors-order', document={
  "user_id": "mgh27",
  "amount": 10000000
})