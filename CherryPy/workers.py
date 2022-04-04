from elasticsearch import Elasticsearch, NotFoundError
from random import choice

from dc_log_helper import dc_log_schema, dc_log_update, dc_log_insert
from members_helper import *
from queue_helpers import RabbitWorker
from config_helper import ConfigHelper
from io_helpers import *
from multiplexer import Multiplexer

import credit as service

import json


class CreditWorker(RabbitWorker):
    def __init__(self, rabbit_servers, queue_names):
        super(CreditWorker, self).__init__()

        self.rabbit_servers = rabbit_servers
        self.queue_names = queue_names

        self.cfg_helper = ConfigHelper()

        es_host = choice(self.cfg_helper.get_config("DBCLUSTER")["hosts"].split(","))
        es_port = self.cfg_helper.get_config("DBCLUSTER")["port"]

        self.es = Elasticsearch([{"host": es_host, "port": es_port}], timeout=30, max_retries=10, retry_on_timeout=True)

        self.user_bf = service.UserBusinessFlowManager(self.es,
                                               rabbit_servers=self.rabbit_servers, queue_names=self.queue_names)
        self.free_bf = service.FreeBusinessFlowManager(self.es,
                                               rabbit_servers=self.rabbit_servers, queue_names=self.queue_names)
        self.admin_bf = service.AdminBusinessFlowManager(self.es,
                                                 rabbit_servers=self.rabbit_servers, queue_names=self.queue_names)
        self.synch_bf = service.SynchBusinessFlowManager(self.es,
                                                 rabbit_servers=self.rabbit_servers, queue_names=self.queue_names)
        self.internals_bf = service.InternalBusinessFlowManager(self.es,
                                                 rabbit_servers=self.rabbit_servers, queue_names=self.queue_names)

        self.multiplexer = Multiplexer()


# noinspection PyShadowingBuiltins,PyBroadException
class CreditSelectWorker(CreditWorker):
    def __init__(self, rabbit_servers, queue_names):
        super(CreditSelectWorker, self).__init__(rabbit_servers=rabbit_servers, queue_names=queue_names)

    def serve_request(self, request_body):
        request = json.loads(request_body.decode("utf-8"))
        broker_type = request["broker_type"]
        data = request["data"]
        dc_log_id = dc_log_insert(broker_type=request["broker_type"], es=self.es, schema=dc_log_schema,
                                  request=request, service_name=service.service_name)

        try:
            if data is None:
                data = {}

            data["broker_type"] = broker_type

            results = self.business_flow(data=data, request=request)

            response = create_success_response(tracking_code=request["tracking_code"],
                                               method_type=request["method"],
                                               response=results,
                                               broker_type=request["broker_type"],
                                               source=request["source"],
                                               member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except PermissionError:
            response = create_error_response(status=701, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="PERMISSION DENIED",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except UserInputError as e:
            response = create_error_response(status=e.error_code, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error=str(e),
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except NotFoundError:
            response = create_error_response(status=601, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Entry Not Found",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except Exception:
            response = create_error_response(status=401, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Exception",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        return json.dumps(response)

    def business_flow(self, data, request):
        member = get_club_member(request=request, rabbitserver=self.rabbit_servers["CLUBMEMBER"],
                                 queue_name=self.queue_names["CLUBMEMBER"]["select"])
        source = request["source"]

        if self.multiplexer.is_admin(source=source, member_category=member["_source"]["category"]):
            return self.admin_bf.select_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_member(source=source, member_category=member["_source"]["category"]):
            return self.user_bf.select_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_free(source=source, member_category=member["_source"]["category"]):
            return self.free_bf.select_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_internal(source=source, member_category=member["_source"]["category"]):
            return self.internals_bf.select_business_flow(data=data, request=request, member=member)
        else:
            raise PermissionError()


# noinspection PyShadowingBuiltins,PyBroadException
class CreditInsertWorker(CreditWorker):
    def __init__(self, rabbit_servers, queue_names):
        super(CreditInsertWorker, self).__init__(rabbit_servers=rabbit_servers, queue_names=queue_names)

    def serve_request(self, request_body):
        # print(request_body.decode("utf-8"))
        request = json.loads(request_body.decode("utf-8"))
        broker_type = request["broker_type"]
        data = request["data"]
        dc_log_id = dc_log_insert(broker_type=request["broker_type"], es=self.es, schema=dc_log_schema,
                                  request=request, service_name=service.service_name)
        try:
            if data is None:
                raise RequiredFieldError("data")

            data["broker_type"] = broker_type

            result = self.business_flow(data=data, request=request)

            response = create_success_response(tracking_code=request["tracking_code"],
                                               method_type=request["method"],
                                               response=result,
                                               broker_type=request["broker_type"],
                                               source=request["source"],
                                               member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except PermissionError:
            response = create_error_response(status=701, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="PERMISSION DENIED",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except UserInputError as e:
            response = create_error_response(status=e.error_code, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error=str(e),
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except NotFoundError:
            response = create_error_response(status=601, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Entry Not Found",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except Exception:
            response = create_error_response(status=401, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Exception",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        return json.dumps(response)

    def business_flow(self, data, request):
        member = get_club_member(request=request, rabbitserver=self.rabbit_servers["CLUBMEMBER"],
                                 queue_name=self.queue_names["CLUBMEMBER"]["select"])
        source = request["source"]

        if self.multiplexer.is_admin(source=source, member_category=member["_source"]["category"]):
            return self.admin_bf.insert_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_member(source=source, member_category=member["_source"]["category"]):
            return self.user_bf.insert_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_free(source=source, member_category=member["_source"]["category"]):
            return self.free_bf.insert_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_internal(source=source, member_category=member["_source"]["category"]):
            return self.internals_bf.insert_business_flow(data=data, request=request, member=member)
        else:
            raise PermissionError()


# noinspection PyBroadException,PyShadowingBuiltins
class CreditDeleteWorker(CreditWorker):
    def __init__(self, rabbit_servers, queue_names):
        super(CreditDeleteWorker, self).__init__(rabbit_servers=rabbit_servers, queue_names=queue_names)

    def serve_request(self, request_body):
        # print(request_body.decode("utf-8"))
        request = json.loads(request_body.decode("utf-8"))
        data = request["data"]
        broker_type = request["broker_type"]
        dc_log_id = dc_log_insert(broker_type=request["broker_type"], es=self.es, schema=dc_log_schema,
                                  request=request, service_name=service.service_name)
        try:
            if data is None:
                raise RequiredFieldError("data")

            if "_id" not in data.keys():
                raise RequiredFieldError("_id")

            data["broker_type"] = broker_type

            result = self.business_flow(data=data, request=request)

            response = create_success_response(tracking_code=request["tracking_code"],
                                               method_type=request["method"],
                                               response=result,
                                               broker_type=request["broker_type"],
                                               source=request["source"],
                                               member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except PermissionError:
            response = create_error_response(status=701, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="PERMISSION DENIED",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except UserInputError as e:
            response = create_error_response(status=e.error_code, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error=str(e),
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except NotFoundError:
            response = create_error_response(status=601, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Entry Not Found",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except Exception:
            response = create_error_response(status=401, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Exception",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        return json.dumps(response)

    def business_flow(self, data, request):
        member = get_club_member(request=request, rabbitserver=self.rabbit_servers["CLUBMEMBER"],
                                 queue_name=self.queue_names["CLUBMEMBER"]["select"])
        source = request["source"]

        if self.multiplexer.is_admin(source=source, member_category=member["_source"]["category"]):
            return self.admin_bf.delete_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_member(source=source, member_category=member["_source"]["category"]):
            return self.user_bf.delete_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_free(source=source, member_category=member["_source"]["category"]):
            return self.free_bf.delete_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_internal(source=source, member_category=member["_source"]["category"]):
            return self.internals_bf.delete_business_flow(data=data, request=request, member=member)
        else:
            raise PermissionError()


# noinspection PyBroadException,PyShadowingBuiltins
class CreditUpdateWorker(CreditWorker):
    def __init__(self, rabbit_servers, queue_names):
        super(CreditUpdateWorker, self).__init__(rabbit_servers=rabbit_servers, queue_names=queue_names)

    def serve_request(self, request_body):
        # print(request_body.decode("utf-8"))
        request = json.loads(request_body.decode("utf-8"))
        broker_type = request["broker_type"]
        data = request["data"]
        dc_log_id = dc_log_insert(broker_type=request["broker_type"], es=self.es, schema=dc_log_schema,
                                  request=request, service_name=service.service_name)
        try:
            if data is None:
                raise RequiredFieldError("data")

            data["broker_type"] = broker_type

            if "_id" not in data.keys():
                raise RequiredFieldError("_id")

            result = self.business_flow(data=data, request=request)

            response = create_success_response(tracking_code=request["tracking_code"],
                                               method_type=request["method"],
                                               response=result,
                                               broker_type=request["broker_type"],
                                               source=request["source"],
                                               member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except PermissionError:
            response = create_error_response(status=701, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="PERMISSION DENIED",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except UserInputError as e:
            response = create_error_response(status=e.error_code, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error=str(e),
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except NotFoundError:
            response = create_error_response(status=601, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Entry Not Found",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except Exception:
            response = create_error_response(status=401, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Exception",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        return json.dumps(response)

    def business_flow(self, data, request):
        member = get_club_member(request=request, rabbitserver=self.rabbit_servers["CLUBMEMBER"],
                                 queue_name=self.queue_names["CLUBMEMBER"]["select"])
        source = request["source"]

        if self.multiplexer.is_admin(source=source, member_category=member["_source"]["category"]):
            return self.admin_bf.update_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_member(source=source, member_category=member["_source"]["category"]):
            return self.user_bf.update_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_free(source=source, member_category=member["_source"]["category"]):
            return self.free_bf.update_business_flow(data=data, request=request, member=member)
        elif self.multiplexer.is_internal(source=source, member_category=member["_source"]["category"]):
            return self.internals_bf.update_business_flow(data=data, request=request, member=member)
        else:
            raise PermissionError()


# noinspection PyBroadException,PyShadowingBuiltins
class CreditSynchWorker(CreditWorker):
    def __init__(self, rabbit_servers, queue_names):
        super(CreditSynchWorker, self).__init__(rabbit_servers=rabbit_servers, queue_names=queue_names)

    def serve_request(self, request_body):
        # print(request_body.decode("utf-8"))
        request = json.loads(request_body.decode("utf-8"))
        broker_type = request["broker_type"]
        data = request["data"]
        dc_log_id = dc_log_insert(broker_type=request["broker_type"], es=self.es, schema=dc_log_schema,
                                  request=request, service_name=service.service_name)
        try:
            if data is None:
                raise RequiredFieldError("data")

            data["broker_type"] = broker_type

            result = self.business_flow(data=data, request=request)

            response = create_success_response(tracking_code=request["tracking_code"],
                                               method_type=request["method"],
                                               response=result,
                                               broker_type=request["broker_type"],
                                               source=request["source"],
                                               member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except PermissionError:
            response = create_error_response(status=701, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="PERMISSION DENIED",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except UserInputError as e:
            response = create_error_response(status=e.error_code, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error=str(e),
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except NotFoundError:
            response = create_error_response(status=601, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Entry Not Found",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        except Exception:
            response = create_error_response(status=401, tracking_code=request["tracking_code"],
                                             method_type=request["method"], error="Exception",
                                             broker_type=request["broker_type"],
                                             source=request["source"],
                                             member_id=request["member_id"])
            dc_log_update(broker_type=response["broker_type"], es=self.es,
                          response=response, _id=dc_log_id, service_name=service.service_name)

        return json.dumps(response)

    def business_flow(self, data, request):
        return self.synch_bf.synch_business_flow(data=data, request=request)
