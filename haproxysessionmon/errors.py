# -*- coding: utf-8 -*-

__all__ = [
    "ConfigError"
]


class ConfigError(Exception):

    def __init__(self, msg, traceback=None):
        super(ConfigError, self).__init__(msg)
        self.msg = msg
        self.traceback = traceback

    def __str__(self):
        return (
            "Error while attempting to parse configuration file: {}".format(self.msg) +
            ("\n{}".format(self.traceback) if self.traceback is not None else "")
        )
