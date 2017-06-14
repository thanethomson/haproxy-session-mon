# -*- coding: utf-8 -*-

import json
from datetime import datetime
from haproxysessionmon.backends.base import StorageBackend

import logging
logger = logging.getLogger(__name__)

__all__ = [
    "GraylogBackend"
]


class GraylogBackend(StorageBackend):
    """Uses Graylog to store statistics."""

    def __init__(self, remote_addr, loop, facility="haproxy-session-mon"):
        self.remote_addr = remote_addr
        self.loop = loop
        self.facility = facility

        logger.debug("Connecting to Graylog server at {}:{}".format(*self.remote_addr))
        self.transport, self.protocol = loop.run_until_complete(loop.create_datagram_endpoint(
            lambda: GraylogProtocol(self, facility=facility),
            remote_addr=remote_addr
        ))

    async def store_stats(self, stats):
        logger.debug("Sending {} metrics to Graylog".format(len(stats)))
        sent = 0
        for metric in stats:
            try:
                self.protocol.send_metric(metric)
                sent += 1
            except Exception as e:
                logger.exception("Exception caught while attempting to log to Graylog: {}".format(e))
        return sent

    def close(self):
        self.transport.close()

    async def _reconnect(self):
        logger.warning("Reconnecting to Graylog server at {}:{}".format(*self.remote_addr))
        self.transport, self.protocol = await self.loop.create_datagram_endpoint(
            lambda: GraylogProtocol(self, facility=self.facility),
            remote_addr=self.remote_addr
        )

    def reconnect(self):
        self.loop.call_soon(self._reconnect())


class GraylogProtocol(object):
    """Our simple protocol for interacting with Graylog."""

    def __init__(self, backend, reconnect_on_failure=True, facility="haproxy-session-mon"):
        self.backend = backend
        self.transport = None
        self.facility = facility
        self.reconnect_on_failure = reconnect_on_failure

    def connection_made(self, transport):
        self.transport = transport

    def send_metric(self, metric):
        # GELF payload format, as per http://docs.graylog.org/en/stable/pages/gelf.html
        payload = {
            "version": "1.1",
            "host": metric.server_id,
            "short_message": "{} concurrent requests measured for backend \"{}\"".format(
                metric.sessions,
                metric.backend
            ),
            "timestamp": datetime.now().timestamp(),
            "level": 6,  # INFO
            "_facility": self.facility,
            "_sessions": metric.sessions,
            "_backend": metric.backend,
            "_queued_sessions": metric.queued_sessions,
            "_active_backends": metric.active_backends,
            "_http_4xx": metric.http_4xx,
            "_http_5xx": metric.http_5xx
        }
        self.transport.sendto(json.dumps(payload).encode())

    def error_received(self, exc):
        logger.exception("Error while communicating with Graylog server: {}".format(exc))
        self.close_and_reconnect()

    def connection_lost(self, exc):
        logger.exception("Connection to Graylog server lost: {}".format(exc))
        self.close_and_reconnect()

    def close_and_reconnect(self):
        self.transport.close()
        if self.reconnect_on_failure:
            self.backend.reconnect()
