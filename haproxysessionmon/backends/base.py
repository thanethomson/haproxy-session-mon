# -*- coding: utf-8 -*-

__all__ = [
    "StorageBackend"
]


class StorageBackend(object):
    """Base class for storage backends."""

    async def store_stats(self, stats):
        raise NotImplementedError
