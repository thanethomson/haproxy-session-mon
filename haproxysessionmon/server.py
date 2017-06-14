# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import signal
import sys
import functools

from haproxysessionmon.haproxy import HAProxyServerMonitor
from haproxysessionmon.backends.graylog import GraylogBackend

from colorlog import ColoredFormatter
import logging
logger = logging.getLogger(__name__)


async def run_monitors(monitors, loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        await asyncio.gather(
            *[monitor.poll_for_stats(client) for monitor in monitors]
        )


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter(
        "%(log_color)s%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s"
    ))
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[handler]
    )


def signal_handler(loop, signame):
    logger.debug("Got signal {}".format(signame))
    loop.stop()


def main():
    configure_logging()
    loop = asyncio.get_event_loop()
    for signame in ['SIGINT', 'SIGTERM']:
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(signal_handler, loop, signame)
        )

    server_mon = HAProxyServerMonitor(
        "test",
        "http://localhost:8083/haproxy?stats;csv",
        [GraylogBackend(('rnd-glha-p1.dstvo.local', 12201), loop, facility="haproxy-session-mon-debug")],
        auth_creds=("admin", "admin")
    )

    try:
        loop.run_until_complete(run_monitors([server_mon], loop))
    finally:
        logger.debug("Shutting down event loop")
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()
