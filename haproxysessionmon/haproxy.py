# -*- coding: utf-8 -*-

import io
import csv
from collections import namedtuple
import asyncio
from aiohttp import BasicAuth

import logging
logger = logging.getLogger(__name__)

__all__ = [
    "HAProxyServerMonitor"
]

ProxyMetrics = namedtuple("ProxyMetrics", [
    "server_id",
    "endpoint",
    "backend",
    "sessions"
])


class HAProxyServerMonitor(object):
    """For representing a single HAProxy server, from which we'll be pulling statistics."""

    def __init__(self, id, stats_csv_endpoint, backends, auth_creds=None, update_interval=10.0):
        """Constructor.

        Args:
            id: A short, descriptive name/title for this HAProxy instance.
            stats_csv_endpoint: A URL to the HAProxy endpoint to monitor.
            backends: A list containing one or more backends to which this server's stats are to be
                sent once retrieved.
            auth_creds: An optional 2-tuple containing the username/password combination for accessing this
                HAProxy instance (using HTTP Basic Authentication).
            update_interval: The interval, in seconds, between each attempt to poll the HAProxy instance
                for stats.
        """
        self.id = id
        self.stats_csv_endpoint = stats_csv_endpoint
        self.backends = backends
        self.update_interval = update_interval
        self.must_stop = False
        self.auth = BasicAuth(auth_creds[0], password=auth_creds[1]) if auth_creds is not None else None

        logger.debug("Configured HAProxy server {} with endpoint {}".format(self.id, self.stats_csv_endpoint))

    async def fetch_stats(self, client):
        logger.debug("Fetching stats for {}".format(self.id))
        result = []
        async with client.get(self.stats_csv_endpoint, auth=self.auth) as response:
            if response.status == 200:
                result = self.parse_csv_stats(await response.text())
            else:
                logger.error("Failed to fetch stats from {} ({}): response {}\n{}".format(
                    self.stats_csv_endpoint,
                    self.id,
                    response.status,
                    await response.text()
                ))

        return result

    async def poll_for_stats(self, client):
        while not self.must_stop:
            await self.track_stats(await self.fetch_stats(client))
            await asyncio.sleep(self.update_interval)

    async def track_stats(self, stats):
        metrics_stored = 0
        for backend in self.backends:
            metrics_stored += await backend.store_stats(stats)
        return metrics_stored

    def stop(self):
        # graceful attempt to stop this process
        self.must_stop = True

    def parse_csv_stats(self, csv_data):
        reader = csv.DictReader(io.StringIO(csv_data))
        stats = []
        for row in reader:
            if '# pxname' in row and 'svname' in row and 'rate' in row and row['svname'] == "BACKEND":
                stats.append(ProxyMetrics(
                    server_id=self.id,
                    endpoint=self.stats_csv_endpoint,
                    backend=row['# pxname'],
                    sessions=int(row['rate'])
                ))
        return stats
