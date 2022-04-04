from elasticsearch import Elasticsearch
import cherrypy
from pika.exchange_type import ExchangeType
import pika
import json
from datetime import datetime
import pandas as pd
from walrus import *
import uuid
import base64


START_TIME = '08:00:00'
END_TIME = '18:10:00'
NOW_PRICE = 100

# The Defualt Value for DataBase
defualt_schema = {
  "amount": 10000000,
  "image": "",
  "isPublic": True,
  "isActivate": True,
  "users":[],
  "follower":[],
  "scores":{
        "Ret": 0,
        "Vol": 0,
        "Rank": 1
      }
}

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

# check the right format for the email
def check_email_format(email):
    # pass the regular expression
    # and the string into the fullmatch() method
    if(re.fullmatch(regex, email)):
        return True
    else:
        False
 
 

# Check the password format is be standards
def password_format_check(passwd):
      
    SpecialSym =['$', '@', '#', '%']
    val = True
    message = ''
    if len(passwd) < 6:
        message = 'length should be at least 6'
        val = False
          
    if len(passwd) > 20:
        message = 'length should be not be greater than 8'
        val = False
          
    if not any(char.isdigit() for char in passwd):
        message = 'Password should have at least one numeral'
        val = False
          
    if not any(char.isupper() for char in passwd):
        message = 'Password should have at least one uppercase letter'
        val = False
          
    if not any(char.islower() for char in passwd):
        message = 'Password should have at least one lowercase letter'
        val = False
          
    if not any(char in SpecialSym for char in passwd):
        message = 'Password should have at least one of the symbols $@#'
        val = False
    if val:
        return val,''
    else:
      return val, message


# check that in time for trades
def check_time_for_trading():
    date_now = datetime.now().strftime("%H:%M:%S")
    if  date_now > START_TIME and date_now < END_TIME:
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
class Server(object):
        # this call when the user buy symbol
    @cherrypy.expose
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
    @cherrypy.expose
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
        # DashBoards
    @cherrypy.expose
    def profile(self):
      return "Hello here we have the dashbords"
    
    # login for user with username and password
    @cherrypy.expose
    def login(self, username, password):
      encode_password = (base64.b64encode(password.encode('utf-8'))).decode('utf-8')
      query_body = {
       'query': {
          'match':{
            'username' : username
          }
        }
      }
      res = es.search(index='toobors-profile', body=query_body)  
      db_password = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]), axis=1)['_source']['password']
      id = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_id']['username']
      if db_password == encode_password:
        token = uuid.uuid4().hex
        hash1[token] = id
        return f'You are Loged in {username} with id {id} and token of {token} '
      else:
        return f'Excuse me its not correct Password for {username}'

    # Signup make the team account by choose uniqe username and email with passwords 
    @cherrypy.expose
    def signup(self, username, email, password, re_password):
      # check not existed username and the format of email and passwords
      exist_query_body = {
       'query': {
          'match':{
            'username' : username
          }
        }
      }
      if password != re_password:
        return f"your entered password are not match"
      val , messages = password_format_check(password)
      if not val:
        return messages
      if not check_email_format(email):
        return "The format of the email is not OK :)"
      res = es.search(index='toobors-profile', body=exist_query_body)
      if len(res["hits"]["hits"]) != 0:
        return f"the {username} is exists, please choose another one"
      encode_password = (base64.b64encode(password.encode('utf-8'))).decode('utf-8')
      insert_query_body = {
        "username": username,
        "email": email,
        "password": encode_password,
        "amount": defualt_schema['amount'],
        "image": defualt_schema['image'],
        "isPublic": defualt_schema['isPublic'],
        "isActivate": defualt_schema['isActivate'],
        "users":defualt_schema['users'],
        "follower":defualt_schema['follower'],
        "scores": defualt_schema['scores']
      }
      es.index(index='toobors-profile', document=insert_query_body)
      id = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_id']['username']
      token = uuid.uuid4().hex
      hash1[token] = id
      return f'Congregation your account is make, you can login by {username} username with id of {id} and token of {token}'

    # Logout
    @cherrypy.expose
    def logout(self, token, id):
      del hash1[token]
      return 'you are loged out'

    # change password
    @cherrypy.expose
    def change_password(self, token, id, new_password):
      return 'your password was changed'
    
    # activate the team by useing the username
    @cherrypy.expose
    def switch_on_team(self, token, id):
      active_query_body = {
         "script" : {
              "source": "ctx._source.isActivate = params.isActivate",
              "lang": "painless",
              "params" : {
                "isActivate": True
              }
        }
      }
      result = es.update(index='toobors-profile', id=id, body=active_query_body) 
      return f"the team is Activated {id}"

    #  deactivate team by using the username
    @cherrypy.expose
    def switch_off_team(self, token, id):
      deactive_query_body = {
         "script" : {
              "source": "ctx._source.isActivate = params.isActivate",
              "lang": "painless",
              "params" : {
                "isActivate": False
              }
        }
      }
      result = es.update(index='toobors-profile', id=id, body=deactive_query_body) 
      return f"the team is Deactivate {id}"

    # Add the Users To Teams by get the username and set the email, name, address and number
    @cherrypy.expose
    def add_user(self, token, id, email, name, address, number):
      if not check_email_format(email):
        return "The format of the email is not OK :)"
      update_query_body = {
         "script" : {
              "source": "ctx._source.users.add(params.users)",
              "lang": "painless",
              "params" : {
                "users":{'email': email, 'name': name, 'address': address, 'number': number}
              }
        }
      }
      result = es.update(index='toobors-profile', id=id, body=update_query_body) 
      return f"the users added : {name}"
    
    # Edit the Users Information by use them email
    @cherrypy.expose
    def edit_user(self, token, id, email, name, address, number):
      remove_query_body = {
        "script": {
          "source":"""
            for(int i = 0;i < ctx._source.users.length; i++) {
              if (ctx._source.users[i]['email'] == params.email ){
                ctx._source.users[i]['name'] = params.name;
                ctx._source.users[i]['address'] = params.address;
                ctx._source.users[i]['number'] = params.number;
              }
            }
       """,
          "lang": "painless",
          "params": {
            "email": email,
            "name": name,
            "address": address,
            "number": number
          }
        }
      }
      result = es.update(index='toobors-profile', id=id, body=remove_query_body)
      return 'the user removed from team'
    
    # Remove the user from the team by use them email
    @cherrypy.expose
    def remove_user(self, token, id, email):
      remove_query_body = {
        "script": {
          "source": """
            for(int i = 0;i < ctx._source.users.length; i++) {
              if (ctx._source.users[i]['email'] == params.email ){
                ctx._source.users.remove(i);
              }
            }
       """,
          "lang": "painless",
          "params": {
            "email": email
          }
        }
      }
      result = es.update(index='toobors-profile', id=id, body=remove_query_body)
      return 'the user removed from team'
    
    # set the scores from the portfolio
    # we need to use the rabbitmq to messaged to the portfolio
    @cherrypy.expose
    def set_scores(self, token, id):
      return 'the score seted'

    
    # add to followers 
    @cherrypy.expose
    def follow(self, token, id, following_id):
      return 'the user followed by you'

    @cherrypy.expose
    def LD(self, InstrumentID):
        x = rd1.hgetall(InstrumentID)
        print(x)
        x = { y.decode('UTF-8'): x.get(y).decode('UTF-8') for y in x.keys() }
        data = json.dumps(x)
        return data


if __name__ == '__main__':
    # elasticsearch coonection 
    es = Elasticsearch("http://192.168.231.73:9200/")
    connection_parameters = pika.ConnectionParameters('localhost')
    connection = pika.BlockingConnection(connection_parameters)
    channel = connection.channel()
    rd = Database(host="localhost", port=6379, db=0)
    hash1 = rd.Hash('Teams')
    # radis connection
    rd1 = Database(host="192.168.231.20", port=6379, db=7)
    cherrypy.quickstart(Server())