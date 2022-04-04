import json
from elasticsearch import Elasticsearch
from datetime import datetime
import pandas as pd
import pika
from pika.exchange_type import ExchangeType


# elasticsearch coonection 
es = Elasticsearch("http://192.168.231.73:9200/")


START_TIME = '08:00:00'
END_TIME = '18:10:00'
NOW_PRICE = 100
# check that in time for trades
def check_time_for_trading():
    if  datetime.now().strftime("%H:%M:%S") > START_TIME and datetime.now().strftime("%H:%M:%S") < END_TIME:
        return True
    else: return False  

def amount_rabbitmq(message):
    connection_parameters = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()
    channel.exchange_declare(exchange='amount-update', exchange_type=ExchangeType.fanout)
    channel.basic_publish(exchange='amount-update', routing_key='', body=message)
    connection.close()


# the orders class that handle users orders
class Orders(object):
    
    # this call when the user buy symbol
    def buy_symbol(self, user_id, symbol, volume, price):
        if check_time_for_trading():
            buy_cost = int(volume) * int(price)
            exist_query_body = {
                'query': {
                    'match':{
                        'user_id' : user_id
                    }
                }
            }
            res = es.search(index='toobors-orders', body=exist_query_body)
            amount = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_source']['amount']
            if amount >= buy_cost :
                amount -= buy_cost 
                insert_query_body = {
                    "user_id": user_id,
                    "amount": amount,
                    'symbol': symbol,
                    'volume': volume,
                    'price': price,
                    'buyed': True,
                    'buy_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                es.index(index='toobors-orders', document=insert_query_body)

                # TODO here we should send the message to profile and portfolio to update the amount
                data = {
                    'user_id': user_id,
                    'amount': amount,
                }
                message = json.dumps(data)
                amount_rabbitmq(message=message)
                return "your order was added"
            else:
                return "your sallery is not enough for by this volum of this symbol"
        else:
            return "the time is out of range to can trading"
    
    # this call when the users want to sell a symbol
    def sell_symbol(self , id, user_id):
        if check_time_for_trading():
            exist_query_body = {
                'query': {
                    'match':{
                        '_id' : id
                    }
                }
            }
            res = es.search(index='toobors-orders', body=exist_query_body)
            amount = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_source']['amount']
            volume = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_source']['volume']
            symbol = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_source']['symbol']
            sell_come = int(volume) * NOW_PRICE
            amount += sell_come
            insert_query_body = {
                    "user_id": user_id,
                    "amount": amount,
                    'symbol': symbol,
                    'volume': volume,
                    'price': NOW_PRICE,
                    'buyed': False,
                    'buy_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            es.index(index='toobors-orders', document=insert_query_body)
            # TODO we should say new amount to profile and portfolio
            data = {
                'user_id': user_id,
                'amount': amount,
            }
            message = json.dump(data)
            amount_rabbitmq(amount=message)
            return "selled out"
        else:
            return "the time is out of range to can trading"
  