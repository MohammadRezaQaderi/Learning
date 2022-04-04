from random import choice

from elasticsearch import Elasticsearch

from config_helper import ConfigHelper


class BusinessFlow:
    def __init__(self, es, service_name):
        self.es = es
        self.cfg_helper = ConfigHelper()
        self.service_name = service_name.upper()

        if "index_name" in self.cfg_helper.get_config(self.service_name).keys():
            self.index_name = self.get_index_name(self.cfg_helper.get_config(self.service_name)["index_name"])
            self.doc_type = self.cfg_helper.get_config(self.service_name)["doc_type"]

    def insert_business_flow(self, data, request, member, params=None):
        pass

    def update_business_flow(self, data, request, member, params=None):
        pass

    def delete_business_flow(self, data, request, member, params=None):
        pass

    def select_business_flow(self, data, request, member, params=None):
        pass

    def synch_business_flow(self, data, request):
        pass

    def get_es_connection(self):
        es_host = choice(self.cfg_helper.get_config("DBCLUSTER")["hosts"].split(","))
        es_port = self.cfg_helper.get_config("DBCLUSTER")["port"]

        self.es = Elasticsearch([{"host": es_host, "port": es_port}], timeout=30, max_retries=10, retry_on_timeout=True)

    def get_index_name(self, raw_name):
        # return raw_name
        # TODO: after data migration the following line should be used instead of returning raw_name directly
        return self.cfg_helper.get_config("DEFAULT")["broker_type"].lower() + "-" + raw_name

    def create_index(self, raw_index_name, settings):
        settings["settings"]["number_of_shards"] = int(self.cfg_helper.get_config(self.service_name)["shards"])
        settings["settings"]["number_of_replicas"] = int(self.cfg_helper.get_config(self.service_name)["replicas"])

        self.es.indices.create(index=self.get_index_name(raw_index_name), ignore=400, body=settings,
                               include_type_name=True)


