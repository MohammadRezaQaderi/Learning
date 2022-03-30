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
            'username': {'type': 'keyword'},
            'email': {'type': 'text'},
            'password': {'type': 'text'},
            'amount': {'type': 'double'},
            'imageURL': {'type': 'text'},
            'isPublic': {'type': 'boolean'},
            'isActivate': {'type': 'boolean'},
            'user': { 'type': 'nested',
                'properties': {
                    'name': { 'type': "text" },
                    'email': { 'type': "keyword"},
                    'address': { 'type': "text"},
                    'number': { 'type': "text"}
                }
            }, 
            'scores': {
                "properties": {
                    "Rank": { "type": "integer" },
                    "Ret": { "type": "double" },
                    "Vol": { "type": "double" },
                }
            },
            'follows': {'type': 'nested',
                "properties": {
                    'follower_id': {'type': 'keyword'}
                }
            }
        }
    }
}

# create the database index for profile 
print("creating 'tooBors-profile' index...")
es.indices.create(index = 'toobors-profile', mappings= request_body['mappings'], settings=request_body["settings"])

# make the first index for test
es.index(index='toobors-profile', document={
  "username": "mgh27",
  "email": "mgh27@aut.ac.ir",
  "password": "bTI3MTFnSDk5ODU=",
  "amount":10000000,
  "image": "imageURL",
  "isPublic": True,
  "isActivate": True,
  "users":[{
        "name": "MohammadrezaQader",
        "email": "m@gmail.com",
        "number": 0,
        "address": "Tehran, Tehran" 
      },{
        "name": "AhmadAsadi",
        "email": "a@gmail.com",
        "number": 1,
        "address": "Tehran, Tehran"  
  }],
  "follower":[2, 3, 4],
  "scores":{
        "Ret": 23,
        "Vol": 73,
        "Rank": 15
  }
})