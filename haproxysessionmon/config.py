# -*- coding: utf-8 -*-

import yaml
import traceback
from copy import deepcopy
from haproxysessionmon.errors import *

import logging
logger = logging.getLogger(__name__)

__all__ = [
    "load_haproxysessionmon_config",
    "load_haproxysessionmon_config_from_file",
    "CONFIG_DEFAULTS",
    "CONFIG_BACKEND_TYPE_GELF",
    "CONFIG_BACKEND_TYPE_PRTG",
    "CONFIG_BACKEND_TYPE_LOGFILE"
]

CONFIG_DEFAULTS = {
    "logging": {
        "level": "INFO",
        "file": None,
        "console": True
    },
    "servers": {
        "update-interval": 10.0
    }
}

CONFIG_LOGGING_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

CONFIG_BACKEND_TYPE_GELF = "gelf"
CONFIG_BACKEND_TYPE_PRTG = "prtg"
CONFIG_BACKEND_TYPE_LOGFILE = "logfile"
CONFIG_BACKEND_TYPES = {
    CONFIG_BACKEND_TYPE_GELF,
    CONFIG_BACKEND_TYPE_PRTG,
    CONFIG_BACKEND_TYPE_LOGFILE
}

CONFIG_BACKEND_REQUIRED_FIELDS = {
    CONFIG_BACKEND_TYPE_GELF: {"host", "port", "facility"},
    CONFIG_BACKEND_TYPE_PRTG: {"base-url", "gid", "key"},
    CONFIG_BACKEND_TYPE_LOGFILE: {"path"}
}

CONFIG_SERVER_REQUIRED_FIELDS = {"endpoint", "backends"}


def validate_logging_config(config):
    # application logging configuration
    if 'logging' in config and isinstance(config['logging'], dict):
        # configure the logging level
        if 'level' in config['logging']:
            if config['logging']['level'] not in CONFIG_LOGGING_LEVELS:
                raise ConfigError("Invalid logging level: {}".format(config['logging']['level']))
        else:
            config['logging']['level'] = CONFIG_DEFAULTS['logging']['level']

        if 'file' not in config['logging']:
            config['logging']['file'] = None
    else:
        # just use all the defaults
        config['logging'] = deepcopy(CONFIG_DEFAULTS['logging'])
    return config


def validate_gelf_backend_config(backend_name, backend_config):
    # make sure the port is an integer
    try:
        backend_config['port'] = int(backend_config['port'])
    except ValueError:
        raise ConfigError("Invalid port specified for backend \"{}\"".format(backend_name))
    return backend_config


def validate_prtg_backend_config(backend_name, backend_config):
    return backend_config


def validate_logfile_backend_config(backend_name, backend_config):
    return backend_config


CONFIG_BACKEND_VALIDATORS = {
    CONFIG_BACKEND_TYPE_GELF: validate_gelf_backend_config,
    CONFIG_BACKEND_TYPE_PRTG: validate_prtg_backend_config,
    CONFIG_BACKEND_TYPE_LOGFILE: validate_logfile_backend_config
}


def validate_backend_config(backend_name, backend_config):
    # first check required fields
    for field_name in CONFIG_BACKEND_REQUIRED_FIELDS[backend_config['type']]:
        if field_name not in backend_config:
            raise ConfigError("Missing required field \"{}\" in backend \"{}\" configuration".format(
                field_name,
                backend_name
            ))

    # now check configuration for each and every specific type
    _validate = CONFIG_BACKEND_VALIDATORS[backend_config['type']]
    return _validate(backend_name, backend_config)


def validate_backends_config(config):
    # backend configuration
    backend_ids = config['backends'].keys()
    for backend in backend_ids:
        if not isinstance(config['backends'][backend], dict) or 'type' not in config['backends'][backend]:
            raise ConfigError("Invalid configuration syntax for backend \"{}\"".format(backend))

        backend_config = config['backends'][backend]
        if backend_config['type'] not in CONFIG_BACKEND_TYPES:
            raise ConfigError("Unrecognised backend type for \"{}\": {}".format(backend, backend_config['type']))

        config['backends'][backend] = validate_backend_config(backend, backend_config)

    return config


def validate_servers_config(config):
    server_ids = config['servers'].keys()
    for server in server_ids:
        if not isinstance(config['servers'][server], dict):
            raise ConfigError("Invalid configuration format for server \"{}\"".format(server))

        server_config = deepcopy(config['servers'][server])

        # check required fields
        for field_name in CONFIG_SERVER_REQUIRED_FIELDS:
            if field_name not in server_config:
                raise ConfigError("Missing required fields \"{}\" in server config \"{}\"".format(
                    field_name,
                    server
                ))

        if 'update-interval' in server_config:
            try:
                server_config['update-interval'] = float(server_config['update-interval'])
            except ValueError:
                raise ConfigError("Field \"update-interval\" for server \"{}\" must be a numeric value".format(
                    server
                ))
        else:
            server_config['update-interval'] = CONFIG_DEFAULTS['servers']['update-interval']

        # if there are auth credentials for the server
        if 'username' in server_config:
            if 'password' not in server_config:
                raise ConfigError("Missing password for server \"{}\"".format(server))

        if 'backends' not in server_config or not isinstance(server_config['backends'], list):
            raise ConfigError("One or more backends are required for server \"{}\" configuration".format(server))

        # check the available backends
        for backend in server_config['backends']:
            if backend not in config['backends']:
                raise ConfigError("Server \"{}\" refers to unrecognised backend \"{}\"".format(
                    server,
                    backend
                ))

        config['servers'][server] = deepcopy(server_config)

    return config


def load_haproxysessionmon_config(s):
    """Loads the HAProxy Session Monitor configuration from the given string, filling in defaults
    where necessary.

    Args:
        s: The string from which to load configuration.

    Returns:
        A Python dictionary containing the configuration.
    """
    try:
        config = yaml.load(s)
    except:
        raise ConfigError("YAML data seems broken", traceback=traceback.format_exc())

    if 'backends' not in config or 'servers' not in config:
        raise ConfigError("Both the \"backends\" and \"servers\" sections are compulsory in configuration")

    if len(config['backends']) < 1 or not isinstance(config['backends'], dict):
        raise ConfigError("At least one backend needs to be configured, or invalid backend configuration syntax")

    if len(config['servers']) < 1 or not isinstance(config['servers'], dict):
        raise ConfigError("At least one HAProxy server needs to be configured, or invalid server configuration syntax")

    config = validate_logging_config(config)
    config = validate_backends_config(config)
    return validate_servers_config(config)


def load_haproxysessionmon_config_from_file(filename):
    with open(filename, "rt") as f:
        return load_haproxysessionmon_config(f.read())
