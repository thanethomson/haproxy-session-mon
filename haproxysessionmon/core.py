# -*- coding: utf-8 -*-

import asyncio
import aiohttp
import signal
import functools
import sys
import os

from haproxysessionmon import __version__ as VERSION
from haproxysessionmon.config import *
from haproxysessionmon.errors import *
from haproxysessionmon.haproxy import *
from haproxysessionmon.backends import *

from colorlog import ColoredFormatter
import logging
logger = logging.getLogger(__name__)


async def run_monitors(monitors, loop):
    async with aiohttp.ClientSession(loop=loop) as client:
        await asyncio.gather(
            *[monitor.poll_for_stats(client) for monitor in monitors.values()]
        )


def configure_logging(to_file=None, to_console=True, level="DEBUG"):
    handlers = []
    if to_console:
        handler = logging.StreamHandler()
        handler.setFormatter(ColoredFormatter(
            "%(log_color)s%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s"
        ))
        handlers.append(handler)

    if to_file is not None:
        handler = logging.FileHandler(to_file, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s"))
        handlers.append(handler)

    logging.basicConfig(
        level=getattr(logging, level),
        handlers=handlers
    )


def configure_signal_handling(loop):
    for signame in ['SIGINT', 'SIGTERM']:
        loop.add_signal_handler(
            getattr(signal, signame),
            functools.partial(signal_handler, loop, signame)
        )


def signal_handler(loop, signame):
    logger.debug("Got signal {}".format(signame))
    loop.stop()


def create_monitors(config, loop):
    """Creates the HAProxy server monitors from the given configuration object."""
    backends = dict()
    monitors = dict()

    for backend_id, backend_config in config['backends'].items():
        logger.debug("Creating backend {} ({})".format(backend_id, backend_config['type']))
        if backend_config['type'] == CONFIG_BACKEND_TYPE_GELF:
            backends[backend_id] = GraylogBackend(
                (backend_config['host'], backend_config['port']),
                loop,
                facility=backend_config['facility']
            )
        elif backend_config['type'] == CONFIG_BACKEND_TYPE_LOGFILE:
            backends[backend_id] = LogfileBackend(
                backend_config['filename']
            )
        else:
            logger.warning("Backend currently not supported, skipping: {}".format(backend_config['type']))

    for monitor_id, server_config in config['servers'].items():
        logger.debug("Creating monitor for server at {}".format(server_config['endpoint']))
        monitors[monitor_id] = HAProxyServerMonitor(
            monitor_id,
            server_config['endpoint'],
            backends=[backends[b] for b in server_config['backends']],
            auth_creds=(server_config['username'], server_config['password']) if 'username' in server_config else None,
            update_interval=server_config['update-interval']
        )

    return monitors


def main():
    import argparse

    parser = argparse.ArgumentParser(description="HAProxy Session Monitor")
    parser.add_argument(
        "-c", "--config",
        help="Full path to the configuration file to use."
    )
    parser.add_argument(
        "-v", "--version",
        required=False,
        action="store_true",
        help="Display the version of the application and exit."
    )
    args = parser.parse_args()

    if args.version:
        print("HAProxy Session Monitor v{}".format(VERSION))
        sys.exit(0)

    config_file = os.environ.get("HAPROXYSM_CONFIG_FILE", args.config)

    if not config_file:
        print("A configuration file is required for the HAProxy Session Monitor application to work.")
        sys.exit(1)

    try:
        config = load_haproxysessionmon_config_from_file(config_file)
    except ConfigError as e:
        print(e)
        sys.exit(2)

    configure_logging(
        to_file=config['logging']['file'],
        to_console=config['logging']['console'],
        level=config['logging']['level']
    )
    logger.debug("Loaded configuration from file: {}".format(config_file))
    loop = asyncio.get_event_loop()
    configure_signal_handling(loop)
    monitors = create_monitors(config, loop)

    try:
        logger.info("Starting up {} monitor(s)".format(len(monitors)))
        loop.run_until_complete(run_monitors(monitors, loop))
    finally:
        logger.info("Shutting down event loop")
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()


if __name__ == "__main__":
    main()
