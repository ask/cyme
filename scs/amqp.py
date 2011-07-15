from __future__ import absolute_import
from __future__ import with_statement

from functools import partial

from celery import current_app as celery
from kombu import Exchange, Queue, Consumer, Producer
from kombu.utils import gen_unique_id

from scs.thread import gThread


class AMQAgent(gThread):
    create_exchange = "srs.create.%s"
    query_exchange = "srs.agent.query-instances"

    def __init__(self, id):
        self.id = id
        create_name = self.create_exchange % (self.id, )
        self._create = Queue(gen_unique_id(),
                             Exchange(create_name, "fanout",
                                      auto_delete=True),
                             auto_delete=True)
        self._query = Queue(self.id,
                            Exchange(self.query_exchange, "fanout",
                                     auto_delete=True),
                            auto_delete=True)
        super(AMQAgent, self).__init__()


    def on_create(self, body, message):
        print("GOT CREATE MESSAGE")
        message.ack()

    def on_query(self, body, message):
        print("GOT QUERY MESSAGE")
        message.ack()

    def on_connection_error(self, exc, interval):
        self.error("Broker connection error: %r. "
                   "Trying again in %s seconds." % (exc, interval, ))

    def run(self):
        with celery.broker_connection() as conn:
            conn.ensure_connection(self.on_connection_error,
                                   celery.conf.BROKER_CONNECTION_MAX_RETRIES)
            with conn.channel() as channel:
                C = partial(Consumer, channel)
                consumers = [C(self._create, callbacks=[self.on_create]),
                             C(self._query, callbacks=[self.on_query])]
                [consumer.consume() for consumer in consumers]
                while 1:
                    conn.drain_events()
