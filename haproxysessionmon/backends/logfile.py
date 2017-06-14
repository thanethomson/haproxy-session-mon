# -*- coding: utf-8 -*-

from haproxysessionmon.backends.base import StorageBackend

import logging

__all__ = [
    "LogfileBackend"
]


class LogfileBackend(StorageBackend):

    def __init__(self, filename, format="%(asctime)s\t%(message)s"):
        self.handler = logging.FileHandler(filename, encoding="utf-8")
        self.handler.setFormatter(logging.Formatter(format))
        self.handler.setLevel(logging.INFO)
        self.logger = logging.getLogger("logfile-backend")
        self.logger.handlers = [self.handler]
        self.logger.info("[Logfile backend started]")
        self.logger.info("server_id\tendpoint\tbackend\tsessions")

    async def store_stats(self, stats):
        for metric in stats:
            self.logger.info("{}\t{}\t{}\t{}".format(
                metric.server_id,
                metric.endpoint,
                metric.backend,
                metric.sessions
            ))
