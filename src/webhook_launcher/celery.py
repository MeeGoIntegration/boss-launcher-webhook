from __future__ import absolute_import

import pika
import json

from celery import Celery
from celery.signals import task_success

app = Celery('bureaucrat',
             broker='amqp://localhost',
             include=['webhook_launcher.tasks'])

app.conf.update(
    CELERY_IGNORE_RESULT=True,
    CELERY_TASK_SERIALIZER='json'
)

@task_success.connect
def handle_task_success(sender=None, **kwargs):
    """Report task results back to workflow engine."""

    parameters = pika.ConnectionParameters(host="localhost")
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.basic_publish(exchange='',
                          routing_key='bureaucrat_msgs',
                          body=json.dumps(kwargs["result"]),
                          properties=pika.BasicProperties(
                              delivery_mode=2,
                              content_type='application/x-bureaucrat-workitem'
                          ))
    connection.close()

if __name__ == '__main__':
    app.start()
