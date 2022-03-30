import base64
import pandas as pd
from elasticsearch import Elasticsearch
import cherrypy
import re


# The Defualt Value for DataBase
defualt_schema = {
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


# Class of Profiles that Can Authentication and Dashboard API and coonect to DB
class Profile(object):
    
    # DashBoards
    @cherrypy.expose
    def index(self):
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
      if db_password == encode_password:
        return f'You are Loged in {username}'
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
        "image": defualt_schema['image'],
        "isPublic": defualt_schema['isPublic'],
        "isActivate": defualt_schema['isActivate'],
        "users":defualt_schema['users'],
        "follower":defualt_schema['follower'],
        "scores": defualt_schema['scores']
      }
      es.index(index='toobors-profile', document=insert_query_body)
      return f'Congregation your account is make, you can login by {username} username'

    # Logout
    @cherrypy.expose
    def logout(self, username):
      return 'you are loged out'

    # change password
    @cherrypy.expose
    def change_password(self, username, password, new_password):
      return 'your password was changed'
    
    # activate the team by useing the username
    @cherrypy.expose
    def switch_on_team(self, username):
      query_body = {
       'query': {
          'match':{
            'username' : username
          }
        }
      }
      res = es.search(index='toobors-profile', body=query_body)
      id = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_id']['username']
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
      return f"the team is Activated {username}"

    #  deactivate team by using the username
    @cherrypy.expose
    def switch_off_team(self, username):
      query_body = {
       'query': {
          'match':{
            'username' : username
          }
        }
      }
      res = es.search(index='toobors-profile', body=query_body)
      id = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_id']['username']
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
      return f"the team is Deactivate {username}"

    # Add the Users To Teams by get the username and set the email, name, address and number
    @cherrypy.expose
    def add_user(self, username, email, name, address, number):
      if not check_email_format(email):
        return "The format of the email is not OK :)"
      query_body = {
       'query': {
          'match':{
            'username' : username
          }
        }
      }
      res = es.search(index='toobors-profile', body=query_body)
      id = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_id']['username']
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
    def edit_user(self, username, email, name, address, number):
      query_body = {
       'query': {
          'match':{
            'username' : username
          }
        }
      }
      res = es.search(index='toobors-profile', body=query_body)
      id = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_id']['username']
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
    def remove_user(self, username, email):
      query_body = {
       'query': {
          'match':{
            'username' : username
          }
        }
      }
      res = es.search(index='toobors-profile', body=query_body)
      id = pd.concat(map(pd.DataFrame.from_dict, res["hits"]["hits"]))['_id']['username']
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
      print(result)
      print(id)
      return 'the user removed from team'
    
    # set the scores from the portfolio
    # we need to use the rabbitmq to messaged to the portfolio
    @cherrypy.expose
    def set_scores(self, id):
      return 'the score seted'

    
    # add to followers 
    @cherrypy.expose
    def follow(self, username, following_id):
      return 'the user followed by you'
if __name__ == '__main__':
  es = Elasticsearch("http://192.168.231.73:9200/")
  cherrypy.quickstart(Profile())