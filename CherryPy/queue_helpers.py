import uuid
from random import choice
import pika

rabbit_ports = [5672, 5673, 5674, 5675, 5676, 5677, 5678, 5679, 5680, 5681]


class RpcClient(object):

    def __init__(self, rabbit_server_host, server_queue_name, virtual_host, username=None, password=None):
        self.server_queue = server_queue_name
        if username is not None and password is not None:
            credentials = pika.PlainCredentials(username=username, password=password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600, connection_attempts=10, retry_delay=2,
                                          credentials=credentials, virtual_host=virtual_host))
        else:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          connection_attempts=10, retry_delay=2,
                                          blocked_connection_timeout=3600, virtual_host=virtual_host))

        self.channel = self.connection.channel()
        self.response = None
        self.corr_id = None
        result = self.channel.queue_declare(queue='', durable=False, auto_delete=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(self.callback_queue, self.on_response, True)

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body
            # print("received reply: ", body)

    def call(self, body, delivery_mode=1):
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key=self.server_queue,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                delivery_mode=delivery_mode,
            ),
            body=body)
        while self.response is None:
            self.connection.process_data_events()
        self.channel.queue_delete(self.callback_queue)
        self.connection.close()
        return self.response


class RpcServer:
    def __init__(self, rabbit_server_host, queue_name, worker, virtual_host, auto_ack=False, durable=False,
                 instantiate_worker=True, auto_delete=False, username=None, password=None):
        self.instantiate_worker = instantiate_worker
        self.queue_name = queue_name
        if username is not None and password is not None:
            credentials = pika.PlainCredentials(username=username, password=password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600, connection_attempts=10, retry_delay=2,
                                          credentials=credentials, virtual_host=virtual_host))
        else:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          connection_attempts=10, retry_delay=2,
                                          blocked_connection_timeout=3600, virtual_host=virtual_host))

        self.channel = self.connection.channel()
        res = self.channel.queue_declare(queue=queue_name, durable=durable, auto_delete=auto_delete)
        self.queue_name = res.method.queue
        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(self.queue_name, self.on_request, auto_ack=auto_ack)
        self.callback_queue = res.method.queue
        self.worker = worker

    def start_consuming(self):
        self.channel.start_consuming()

    def on_request(self, ch, method, props, body):
        #
        if self.instantiate_worker:
            worker = self.worker()
        else:
            worker = self.worker
        response = worker.serve_request(request_body=body)
        #
        ch.basic_publish(exchange='',
                         routing_key=props.reply_to,
                         properties=pika.BasicProperties(correlation_id=props.correlation_id),
                         body=str(response))
        ch.basic_ack(delivery_tag=method.delivery_tag)
        # print("replied message: ", response, ", callback_queue: ", props.reply_to, ", corr_id: ",
        # props.correlation_id)


class DirectClient:
    def __init__(self, rabbit_server_host, server_queue_name, virtual_host, username=None, password=None):
        self.server_queue_name = server_queue_name
        if username is not None and password is not None:
            credentials = pika.PlainCredentials(username=username, password=password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600, connection_attempts=10, retry_delay=2,
                                          credentials=credentials, virtual_host=virtual_host))
        else:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          connection_attempts=10, retry_delay=2,
                                          blocked_connection_timeout=3600, virtual_host=virtual_host))

        self.channel = self.connection.channel()

    def call(self, body, delivery_mode=1):
        self.channel.basic_publish(exchange="",
                                   routing_key=self.server_queue_name,
                                   properties=pika.BasicProperties(
                                       delivery_mode=delivery_mode,
                                   ),
                                   body=body)


class DirectServer:
    def __init__(self, rabbit_server_host, queue_name, worker, virtual_host, instantiate_worker=True, durable=False,
                 auto_delete=False, username=None, password=None, auto_ack=False):
        self.instantiate = instantiate_worker
        if username is not None and password is not None:
            credentials = pika.PlainCredentials(username=username, password=password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600, connection_attempts=10, retry_delay=2,
                                          credentials=credentials, virtual_host=virtual_host))
        else:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          connection_attempts=10, retry_delay=2,
                                          blocked_connection_timeout=3600, virtual_host=virtual_host))

        self.channel = self.connection.channel()
        res = self.channel.queue_declare(queue=queue_name, durable=durable, auto_delete=auto_delete)
        self.queue_name = res.method.queue

        self.worker = worker
        self.channel.basic_qos(prefetch_count=1)

        self.channel.basic_consume(queue=self.queue_name,
                                   auto_ack=auto_ack,
                                   on_message_callback=self.on_request)

    def start_consuming(self):
        self.channel.start_consuming()

    def on_request(self, ch, method, properties, body):
        if self.instantiate:
            worker = self.worker()
        else:
            worker = self.worker

        worker.serve_request(request_body=body)

        ch.basic_ack(delivery_tag=method.delivery_tag)


class TopicServer:
    def __init__(self, rabbit_server_host, exchange_name, worker, binding_keys,
                 queue_name="", instantiate_worker=True, username=None, password=None):
        self.instantiate = instantiate_worker
        self.exchange_name = exchange_name
        if username is not None and password is not None:
            credentials = pika.PlainCredentials(username=username, password=password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600,
                                          credentials=credentials))
        else:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600))

        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='topic')

        result = self.channel.queue_declare(queue_name, exclusive=False)
        queue_name = result.method.queue

        self.binding_keys = binding_keys
        for binding_key in self.binding_keys:
            self.channel.queue_bind(exchange=self.exchange_name, queue=queue_name, routing_key=binding_key)

        self.worker = worker
        self.channel.basic_qos(prefetch_count=1)

        self.channel.basic_consume(queue=queue_name,
                                   auto_ack=True,
                                   on_message_callback=self.on_request)

    def start_consuming(self):
        self.channel.start_consuming()

    def on_request(self, ch, method, properties, body):
        if self.instantiate:
            worker = self.worker()
        else:
            worker = self.worker

        worker.serve_request(request_body=body)


class TopicClient:
    def __init__(self, rabbit_server_host, exchange, username=None, password=None):
        self.exchange = exchange
        if username is not None and password is not None:
            credentials = pika.PlainCredentials(username=username, password=password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600,
                                          credentials=credentials))
        else:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600))

        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=self.exchange, exchange_type='topic')

    def call(self, body, routing_key):
        self.channel.basic_publish(
            exchange=self.exchange, routing_key=routing_key, body=body)


class FanoutServer:
    def __init__(self, rabbit_server_host, exchange_name, worker,
                 queue_name="", instantiate_worker=True, username=None, password=None):
        self.instantiate = instantiate_worker
        self.exchange_name = exchange_name
        if username is not None and password is not None:
            credentials = pika.PlainCredentials(username=username, password=password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600,
                                          credentials=credentials))
        else:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600))

        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange_name, exchange_type='fanout')

        result = self.channel.queue_declare(queue_name, exclusive=False)
        queue_name = result.method.queue

        self.channel.queue_bind(exchange=self.exchange_name, queue=queue_name)

        self.worker = worker
        self.channel.basic_qos(prefetch_count=1)

        self.channel.basic_consume(queue=queue_name,
                                   auto_ack=True,
                                   on_message_callback=self.on_request)

    def start_consuming(self):
        self.channel.start_consuming()

    def on_request(self, ch, method, properties, body):
        if self.instantiate:
            worker = self.worker()
        else:
            worker = self.worker

        worker.serve_request(request_body=body)


class FanoutClient:
    def __init__(self, rabbit_server_host, exchange, username=None, password=None):
        self.exchange = exchange
        if username is not None and password is not None:
            credentials = pika.PlainCredentials(username=username, password=password)
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600,
                                          credentials=credentials))
        else:
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(host=rabbit_server_host, port=choice(rabbit_ports), heartbeat=3600,
                                          blocked_connection_timeout=3600))

        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange=self.exchange, exchange_type='fanout')

    def call(self, body):
        self.channel.basic_publish(
            exchange=self.exchange, routing_key='', body=body)


class RabbitWorker:
    def serve_request(self, request_body):
        pass
