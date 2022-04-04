# !/usr/bin/env python

# pylint: disable=invalid-name

"""
CherryPy-based webservice daemon with background threads
CherryPy-based webservice daemon with background threads
"""

from __future__ import print_function

import threading

import cherrypy
from cherrypy.process import plugins
import cherrypy_cors
from marshmallow import Schema, fields

from communication_helpers import *
from config_helper import ConfigHelper
from io_helpers import RequiredFieldError

from walrus import *


from role_checker import RoleChecker

"""
redis & RabbitMQ param
"""


########################### Exceptions

class InvalidConfigException(Exception):
    def __init__(self, param, value):
        super(InvalidConfigException, self).__init__("UNDEFINED PARAM %s: %s" % (param, value))


class InvalidInputException(Exception):
    def __init__(self, param, value):
        super(InvalidInputException, self).__init__("INVALID INPUT %s: %s" % (param, value))


class PermissionDeniedException(Exception):
    def __init__(self):
        super(PermissionDeniedException, self).__init__("PERMISSION DENIED")


class NotAuthenticatedException(InvalidInputException):
    def __init__(self):
        super(NotAuthenticatedException, self).__init__("API_KEY", "Not Authenticated")


class NotAuthorizedException(InvalidInputException):
    def __init__(self):
        super(NotAuthorizedException, self).__init__("token", "Not Authorized")


########################### background bus process
class NodeSchema(Schema):
    """
    Marshmallow schema for nodes object
    """
    name = fields.String(required=True)


def worker():
    """Background Timer that runs the hello() function every 5 seconds
    TODO: this needs to be fixed/optimized. I don't like creating the thread
    repeatedly.
    """

    # while True:
    #     t = threading.Timer(5.0, hello)
    #     t.start()
    #     t.join()


class MyBackgroundThread(plugins.SimplePlugin):
    """CherryPy plugin to create a background worker thread"""

    def __init__(self, bus):
        super(MyBackgroundThread, self).__init__(bus)

        self.t = None

    def start(self):
        """Plugin entrypoint"""

        self.t = threading.Thread(target=worker)
        self.t.daemon = True
        self.t.start()

    # Start at a higher priority that "Daemonize" (which we're not using
    # yet but may in the future)
    start.priority = 85


######################################## Api
# noinspection PyShadowingNames
def authenticate(ip, api_key):
    cfg_helper = ConfigHelper()
    if not cfg_helper.has_name("DB_API", api_key):
        return None
    valid_ips = cfg_helper.get_config("DB_API")[api_key].split(",")[1:-1]
    service_name = cfg_helper.get_config("DB_API")[api_key + "_service"]

    if ip in valid_ips or "10.200.200" in ip:
        return service_name
    else:
        return None


# noinspection PyShadowingNames
def authorize(api_key, token, member_id):
    permitted_methods = None

    if api_key == token and member_id is None:  # CLIENT IS AN INTERNAL SERVICE
        return "SERVICE", "CLUB .*"

    member_type = None

    if member_id is None:
        raise RequiredFieldError("member_id")

    if token is None:
        raise RequiredFieldError("token")

    cfg_helper = ConfigHelper()

    redis_host = cfg_helper.get_config("DB_API")["redis_host"]
    redis_port = cfg_helper.get_config("DB_API")["redis_port"]
    redis_db_number = cfg_helper.get_config("DB_API")["redis_db_number"]

    cache_db = Database(redis_host, redis_port, redis_db_number)
    cache = cache_db.cache("authorization_cache")

    cache_record = cache.get(member_id)
    cache_token = None
    if cache_record is not None:
        cache_record = json.loads(cache_record)
        cache_token = cache_record["token"]
        member_type = cache_record["member_type"]
        permitted_methods = cache_record["permitted_methods"]

    if cache_token is None or token != cache_token:
        return None, None
    else:
        return member_type, permitted_methods


# noinspection PyShadowingNames
def execute_request(index, method_type, method, order_data, ip, api_key, token, member_id):
    role_checker = RoleChecker()
    cfg_helper = ConfigHelper()
    config_key = index.upper()

    if config_key not in cfg_helper.config.keys():
        raise InvalidInputException("TABLE", index)

    source = authenticate(ip, api_key)
    if source is None:
        raise NotAuthenticatedException()

    member_type, permitted_methods = authorize(api_key=api_key, token=token, member_id=member_id)
    if member_type is None:
        raise NotAuthorizedException()

    if "," + source + "," not in cfg_helper.get_config(config_key)[method_type + "_permitted_sources"]:
        raise PermissionDeniedException()

    if source == "ADMIN":
        if not role_checker.check_role(member_permitted_methods=permitted_methods,
                                             service_name=config_key, method_name=method):
            raise PermissionDeniedException()

    order_data = api_input_preprocess(order_data)

    tracking_code = str(uuid.uuid4())
    size = 1000 if "size" not in order_data else order_data["size"]
    from_ = 0 if "from" not in order_data else order_data["from"]
    sort_by = [{"DC_CREATE_TIME": "desc"}] if "sort_by" not in order_data or len(
        order_data["sort_by"].keys()) == 0 else [order_data["sort_by"]]

    request = {"broker_type": cfg_helper.get_config("DEFAULT")["broker_type"], "source": source,
               "method": method, "ip": ip, "api_key": api_key, "size": size, "from": from_,
               "tracking_code": tracking_code, "member_id": member_id, "member_type": member_type,
               "sort_by": sort_by}
    queue_name = cfg_helper.get_config(config_key)[method_type + "_queue_name_prefix"]
    rabbit_type = cfg_helper.get_config(config_key)[method_type + "_rabbit_type"]
    rabbitserver = cfg_helper.get_config("RABBIT")["rabbitserver"]
    rabbit_virtual_host = cfg_helper.get_config("RABBIT")["virtual_host"]
    rabbit_user = cfg_helper.get_config("RABBIT")["user"]
    rabbit_pass = cfg_helper.get_config("RABBIT")["pass"]
    if rabbit_type == "rpc":
        response = send_rpc_message(rabbitserver=rabbitserver, queue_name=queue_name, body=order_data["data"],
                                    request=request, method=method, source=source, from_=int(from_), size=int(size),
                                    rabbit_username=rabbit_user, rabbit_password=rabbit_pass, sort_by=sort_by,
                                    virtual_host=rabbit_virtual_host
                                    )

    elif rabbit_type == "direct":
        response = send_direct_message(rabbitserver=rabbitserver, queue_name=queue_name, body=order_data["data"],
                                       virtual_host=rabbit_virtual_host,
                                       request=request, method=method, source=source, from_=int(from_), size=int(size),
                                       username=rabbit_user, password=rabbit_pass, sort_by=sort_by)
    else:
        raise InvalidConfigException(index + ".rabbit_type",
                                     cfg_helper.get_config(index)["rabbit_type"])

    response = clear_response(response)

    return response, tracking_code


# noinspection PyBroadException
class NodesController(object): \
        # pylint: disable=too-few-public-methods

    """Controller for  webservice APIs"""

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def login(self): \
            # pylint: disable=no-self-use
        """
        Handler for /GradDB/V1/login (POST)
        """
        method_type = "login"
        try:
            # lock = db.lock('api_Lock', 1000)
            order_data = cherrypy.request.json

            api_key = order_data["api_key"]
            ip = cherrypy.request.remote.ip

            index = "clubmember"
            method = order_data["method_type"]

            order_data["data"]["DC_CREATE_TIME"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")

            if "data" not in order_data.keys():
                raise RequiredFieldError("data")

            cfg_helper = ConfigHelper()
            config_key = index.upper()
            if config_key not in cfg_helper.config.keys():
                raise InvalidInputException("TABLE", index)

            source = authenticate(ip, api_key)
            if source is None:
                raise NotAuthenticatedException()

            if "," + source + "," not in cfg_helper.get_config(config_key)[method_type + "_permitted_sources"]:
                raise PermissionDeniedException

            tracking_code = str(uuid.uuid4())
            size = 1000 if "size" not in order_data else order_data["size"]
            from_ = 0 if "from" not in order_data else order_data["from"]
            request = {"broker_type": cfg_helper.get_config("DEFAULT")["broker_type"], "source": source,
                       "method": method, "ip": ip, "api_key": api_key, "size": size, "from": from_,
                       "tracking_code": tracking_code,
                       "member_id": None
                       }
            queue_name = cfg_helper.get_config(config_key)[method_type + "_queue_name_prefix"]
            rabbit_type = cfg_helper.get_config(config_key)[method_type + "_rabbit_type"]
            rabbitserver = cfg_helper.get_config("RABBIT")["rabbitserver"]
            rabbit_virtual_host = cfg_helper.get_config("RABBIT")["virtual_host"]
            rabbit_user = cfg_helper.get_config("RABBIT")["user"]
            rabbit_pass = cfg_helper.get_config("RABBIT")["pass"]
            if rabbit_type == "rpc":
                response = send_rpc_message(rabbitserver=rabbitserver, queue_name=queue_name, body=order_data["data"],
                                            request=request, method=method, source=source,
                                            rabbit_username=rabbit_user, rabbit_password=rabbit_pass,
                                            virtual_host=rabbit_virtual_host)

            elif rabbit_type == "direct":
                response = send_direct_message(rabbitserver=rabbitserver, queue_name=queue_name,
                                               body=order_data["data"], virtual_host=rabbit_virtual_host,
                                               request=request, method=method, source=source,
                                               username=rabbit_user, password=rabbit_pass
                                               )
            else:
                raise InvalidConfigException(index + ".rabbit_type",
                                             cfg_helper.get_config(index)["rabbit_type"])

            response = clear_response(response)

            if method == "login" and response["is_successful"] is True:
                token = response["data"]["token"]
                member_id = response["data"]["member_id"]
                ttl = response["data"]["ttl"]
                member_type = response["data"]["member_type"]
                permitted_methods = response["data"]["member_permitted_methods"]

                redis_host = cfg_helper.get_config("DB_API")["redis_host"]
                redis_port = cfg_helper.get_config("DB_API")["redis_port"]
                redis_db_number = cfg_helper.get_config("DB_API")["redis_db_number"]

                free_member_id = cfg_helper.get_config("CLUBMEMBER")["free_member_id"]
                free_token = cfg_helper.get_config("CLUBMEMBER")["free_token"]
                free_ttl = cfg_helper.get_config("CLUBMEMBER")["free_ttl"]

                cache_db = Database(redis_host, redis_port, redis_db_number)
                _cache = cache_db.cache("authorization_cache")
                cache_token = _cache.get(member_id)
                if cache_token is None:
                    _cache.set(member_id, json.dumps({"token": token, "member_type": member_type,
                                                      "permitted_methods": permitted_methods}), ttl)
                else:
                    cache_token = json.loads(cache_token)
                    response["data"]["token"] = cache_token["token"]
                    # response["data"]["token"] = free_token
                    _cache.set(member_id, json.dumps(
                        {"token": response["data"]["token"], "member_type": cache_token["member_type"],
                         "permitted_methods": permitted_methods}), ttl)

                _cache.set(free_member_id, json.dumps({"token": free_token, "member_type": "FREE",
                                                       "permitted_methods": "CLUB"}), free_ttl)
            return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                    "response": response}
        except NotAuthenticatedException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except NotAuthorizedException as e:
            return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except PermissionDeniedException as e:
            return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except RequiredFieldError as e:
            return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except InvalidInputException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}

        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def logout(self): \
            # pylint: disable=no-self-use
        """
        Handler for /GradDB/V1/login (POST)
        """
        method_type = "logout"
        try:
            # lock = db.lock('api_Lock', 1000)
            order_data = cherrypy.request.json

            api_key = order_data["api_key"]
            ip = cherrypy.request.remote.ip
            token = order_data["token"]
            member_id = order_data["member_id"]

            index = "clubmember"
            method = order_data["method_type"]

            order_data["data"]["DC_CREATE_TIME"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")

            if "data" not in order_data.keys():
                raise RequiredFieldError("data")

            cfg_helper = ConfigHelper()
            config_key = index.upper()
            if config_key not in cfg_helper.config.keys():
                raise InvalidInputException("TABLE", index)

            response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                      order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                      member_id=member_id)

            if method == "logout" and response["is_successful"] is True:
                member_id = member_id
                ttl = 1

                redis_host = cfg_helper.get_config("DB_API")["redis_host"]
                redis_port = cfg_helper.get_config("DB_API")["redis_port"]
                redis_db_number = cfg_helper.get_config("DB_API")["redis_db_number"]

                cache_db = Database(redis_host, redis_port, redis_db_number)
                _cache = cache_db.cache("authorization_cache")
                cache_token = _cache.get(member_id)
                if cache_token is None:
                    pass
                else:
                    _cache.set(member_id, json.dumps(
                        {"token": None, "member_type": None,
                         "permitted_methods": None}), ttl)

            return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                    "response": response}
        except NotAuthenticatedException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except NotAuthorizedException as e:
            return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except PermissionDeniedException as e:
            return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except RequiredFieldError as e:
            return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except InvalidInputException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}

        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index_insert(self): \
            # pylint: disable=no-self-use
        """
        Handler for /GradDB/V1/insert_request (POST)
        """
        method_type = "insert"
        try:
            # lock = db.lock('api_Lock', 1000)
            order_data = cherrypy.request.json

            api_key = order_data["api_key"]
            ip = cherrypy.request.remote.ip
            token = order_data["token"]
            member_id = order_data["member_id"]

            index = order_data["table"]
            if "method_type" in order_data:
                method = order_data["method_type"]
                if method.upper() in ["UPDATE", "SELECT", "DELETE"]:
                    raise PermissionDeniedException()
            else:
                method = "insert"

            if "data" not in order_data.keys():
                raise RequiredFieldError("data")

            order_data["data"]["DC_CREATE_TIME"] = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S.%f")

            response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                      order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                      member_id=member_id)

            return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                    "response": response}
        except NotAuthenticatedException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except NotAuthorizedException as e:
            return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except PermissionDeniedException as e:
            return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except RequiredFieldError as e:
            return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except InvalidInputException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}
        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index_delete(self): \
            # pylint: disable=no-self-use
        """
        Handler for /GradDB/V1/delete_request (POST)
        """
        method_type = "delete"
        try:
            # lock = db.lock('api_Lock', 1000)
            order_data = cherrypy.request.json

            api_key = order_data["api_key"]
            ip = cherrypy.request.remote.ip
            token = order_data["token"]
            member_id = order_data["member_id"]

            index = order_data["table"]
            if "method_type" in order_data:
                method = order_data["method_type"]
                if method.upper() in ["UPDATE", "SELECT", "INSERT"]:
                    raise PermissionDeniedException()
            else:
                method = "delete"

            response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                      order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                      member_id=member_id)

            return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                    "response": response}
        except NotAuthenticatedException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except NotAuthorizedException as e:
            return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except PermissionDeniedException as e:
            return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except InvalidInputException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}
        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index_update(self): \
            # pylint: disable=no-self-use
        """
        Handler for /GradDB/V1/update_request (POST)
        """
        method_type = "update"
        try:
            # lock = db.lock('api_Lock', 1000)
            order_data = cherrypy.request.json

            api_key = order_data["api_key"]
            ip = cherrypy.request.remote.ip
            token = order_data["token"]
            member_id = order_data["member_id"]

            index = order_data["table"]
            if "method_type" in order_data:
                method = order_data["method_type"]
                if method.upper() in ["INSERT", "SELECT", "DELETE"]:
                    raise PermissionDeniedException()
            else:
                method = "update"

            response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                      order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                      member_id=member_id)

            return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                    "response": response}
        except NotAuthenticatedException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except NotAuthorizedException as e:
            return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except PermissionDeniedException as e:
            return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except RequiredFieldError as e:
            return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except InvalidInputException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except KeyError as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}
        except:
            return {"status": 500, "tracking_code": None, "method_type": None, "error": "General Error"}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def index_select(self): \
            # pylint: disable=no-self-use
        """
        Handler for /GradDB/V1/select_request (POST)
        """
        method_type = "select"
        try:
            # lock = db.lock('api_Lock', 1000)
            order_data = cherrypy.request.json

            api_key = order_data["api_key"]
            ip = cherrypy.request.remote.ip
            token = order_data["token"]
            member_id = order_data["member_id"]

            index = order_data["table"]
            if "method_type" in order_data:
                method = order_data["method_type"]
                if method.upper() in ["UPDATE", "INSERT", "DELETE"]:
                    raise PermissionDeniedException()
            else:
                method = "select"

            response, tracking_code = execute_request(index=index, method_type=method_type, method=method,
                                                      order_data=order_data, ip=ip, api_key=api_key, token=token,
                                                      member_id=member_id)

            return {"status": 200, "tracking_code": tracking_code, "method_type": method_type,
                    "response": response}

        except NotAuthenticatedException as e:
            return {"status": 401, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except NotAuthorizedException as e:
            return {"status": 405, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except PermissionDeniedException as e:
            return {"status": 403, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except RequiredFieldError as e:
            return {"status": e.error_code, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except InvalidInputException as e:
            return {"status": 400, "tracking_code": None, "method_type": method_type, "error": str(e)}
        except KeyError as e:
            return {"status": 400, "tracking_code": None, "method_type": method_type,
                    "error": "key %s is not passed" % str(e)}
        except:
            return {"status": 500, "tracking_code": None, "method_type": None}


####################################### bad request response
def jsonify_error(status, message): \
        # pylint: disable=unused-argument

    """JSONify all CherryPy error responses (created by raising the
    cherrypy.HTTPError exception)
    """

    cherrypy.response.headers['Content-Type'] = 'application/json'
    response_body = message

    cherrypy.response.status = status

    return response_body


def cors():
    if cherrypy.request.method == 'OPTIONS':
        # preflign request
        # see http://www.w3.org/TR/cors/#cross-origin-request-with-preflight-0
        cherrypy.response.headers['Access-Control-Allow-Methods'] = 'POST'
        cherrypy.response.headers['Access-Control-Allow-Headers'] = 'content-type'
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'
        # tell CherryPy no avoid normal handler
        return True
    else:
        cherrypy.response.headers['Access-Control-Allow-Origin'] = '*'


if __name__ == '__main__':
    ports = list(sys.argv)
    # ports=[80,5000]

    cherrypy_cors.install()

    MyBackgroundThread(cherrypy.engine).subscribe()

    dispatcher = cherrypy.dispatch.RoutesDispatcher()

    # /DB/V1/pishkhan (POST)
    dispatcher.connect(name='auth',
                       route='/GradDB/V1/insert_request',
                       action='index_insert',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    # /DB/V1/pishkhan (POST)
    dispatcher.connect(name='auth',
                       route='/GradDB/V1/select_request',
                       action='index_select',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    # /DB/V1/pishkhan (POST)
    dispatcher.connect(name='auth',
                       route='/GradDB/V1/delete_request',
                       action='index_delete',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    # /DB/V1/pishkhan (POST)
    dispatcher.connect(name='auth',
                       route='/GradDB/V1/update_request',
                       action='index_update',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    # /DB/V1/pishkhan (POST)
    dispatcher.connect(name='auth',
                       route='/GradDB/V1/login',
                       action='login',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    # /DB/V1/pishkhan (POST)
    dispatcher.connect(name='auth',
                       route='/GradDB/V1/logout',
                       action='logout',
                       controller=NodesController(),
                       conditions={'method': ['POST']})

    config = {

        '/': {
            'request.dispatch': dispatcher,
            'error_page.default': jsonify_error,
            'cors.expose.on': True,
            # 'tools.auth_basic.on': True,
            # 'tools.auth_basic.realm': 'localhost',
            # 'tools.auth_basic.checkpassword': validate_password,
        },
    }

    cherrypy.tree.mount(root=None, config=config)

    cherrypy.config.update({
        'server.socket_host': '0.0.0.0',
        'server.socket_port': int(ports[1]),
        'server.socket_queue_size': 30000,
        'server.thread_pool': 300,
        'log.screen': False,
        'log.access_file': ''
    })
    cherrypy.log.error_log.propagate = False
    cherrypy.log.access_log.propagate = False
    cherrypy.engine.start()
    cherrypy.engine.block()
