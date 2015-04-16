import json
import pika
import xml.etree.ElementTree as ET

from django.conf import settings

def launch(process_path, fields):
    """Bureaucrat process launcher.

    :param process_path: path to process definition file
    :param fields: dict of workitem fields
    """

    tree = ET.parse(process_path)
    proc_elem = tree.getroot()
    assert proc_elem.tag == 'process'

    fields_elem = ET.Element('fields')
    fields_elem.text = json.dumps(fields)
    proc_elem.append(fields_elem)
    pdef = ET.tostring(proc_elem)

    parameters = pika.ConnectionParameters(host=settings.AMQP_HOST)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.basic_publish(exchange='',
                          routing_key=settings.AMQP_ROUTING_KEY,
                          body=pdef,
                          properties=pika.BasicProperties(
                              delivery_mode=2
                          ))
    connection.close()

def launch_queue(fields):
    launch(settings.VCSCOMMIT_QUEUE, fields)

def launch_notify(fields):
    launch(settings.VCSCOMMIT_NOTIFY, fields)

def launch_build(fields):
    launch(settings.VCSCOMMIT_BUILD, fields)

