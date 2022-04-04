import pika
from pika.exchange_type import ExchangeType
import json
from elasticsearch import Elasticsearch


def on_message_recive(oh, method, properties, body, id):
  data = json.loads(body)
  amount = data['amount']
  user_id = data['user_id']
  update_query_body = {
         "script" : {
              "source": "ctx._source.amount = params.amount",
              "lang": "painless",
              "params" : {
                "amount": amount
              }
        }
      }
  result = es.update(index='toobors-profile', id=user_id, body=update_query_body)



def update_amount_rabbitmq():
  connection_parameters = pika.ConnectionParameters('localhost')
  connection = pika.BlockingConnection(connection_parameters)
  channel = connection.channel()
  channel.exchange_declare(exchange='amount-update', exchange_type=ExchangeType.fanout)
  queue = channel.queue_declare(queue='Profile', exclusive=True)
  channel.queue_bind(exchange='amount-update', queue=queue.method.queue)
  channel.basic_consume(queue=queue.method.queue, auto_ack=True, on_message_callback=on_message_recive)
  channel.start_consuming()


if __name__ == '__main__':
    # elasticsearch coonection 
    es = Elasticsearch("http://192.168.231.73:9200/")
    update_amount_rabbitmq()