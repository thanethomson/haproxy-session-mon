# -*- coding: utf-8 -*-

import unittest

from haproxysessionmon.config import *
from haproxysessionmon.errors import *


CASE_MISSING_BASE_FIELDS1 = """logging:
    level: DEBUG
"""

CASE_MISSING_BASE_FIELDS2 = """logging:
    level: DEBUG

backends:
    - this-will-be-ignored
"""

CASE_INVALID_BACKENDS_FIELD = """logging:
    level: DEBUG

backends:
    - this-should-be-a-dictionary

servers:
    - this-will-be-ignored
"""

CASE_INVALID_SERVERS_FIELD = """logging:
    level: DEBUG

backends:
    backend1:
        type: gelf

servers:
    - this-should-be-a-dictionary
"""

CASE_INVALID_LOGGING_CONFIG = """logging:
    level: some-unknown-level

backends:
    backend1:
        type: gelf

servers:
    server1:
        endpoint: some-endpoint
"""

CASE_INVALID_BACKEND_CONFIG = """backends:
    backend1:
        type: some-unrecognised-backend

servers:
    server1:
        endpoint: "http://server1:8080/haproxy?stats;csv"
        update-interval: 10
        backends:
            - backend1
"""

CASE_SIMPLE_VALID_CONFIG = """backends:
    backend1:
        type: gelf
        host: logbroker.local
        port: 12201
        facility: test

servers:
    server1:
        endpoint: "http://server1:8080/haproxy?stats;csv"
        update-interval: 10
        backends:
            - backend1
"""

CASE_INVALID_GELF_CONFIG = """backends:
    backend1:
        type: gelf

servers:
    server1:
        endpoint: "http://server1:8080/haproxy?stats;csv"
        update-interval: 10
        backends:
            - backend1
"""

CASE_INVALID_PRTG_CONFIG = """backends:
    backend1:
        type: prtg

servers:
    server1:
        endpoint: "http://server1:8080/haproxy?stats;csv"
        update-interval: 10
        backends:
            - backend1
"""

CASE_INVALID_LOGFILE_CONFIG = """backends:
    backend1:
        type: logfile

servers:
    server1:
        endpoint: "http://server1:8080/haproxy?stats;csv"
        update-interval: 10
        backends:
            - backend1
"""

CASE_VALID_COMPLEX_CONFIG = """# Logging configuration
logging:
    # Other possible options: INFO, WARNING, ERROR, CRITICAL
    level: DEBUG
    # Full path to the output file to which to log (leave this option
    # out completely to avoid logging to a file)
    file: /var/log/haproxysessionmon.log
    # Should logging also go to the console?
    console: true

# Backend configuration for storage of monitoring data
backends:
    graylog1:
        type: gelf
        host: logbroker1.local
        port: 12201
        facility: haproxysm
    graylog2:
        type: gelf
        host: logbroker2.local
        port: 12201
        facility: haproxysm-secondary
    prtg1:
        type: prtg
        base-url: https://prtg.local/probe/
        gid: 1234
        key: some-key
    logfile1:
        type: logfile
        path: /var/log/session-count.log

# The HAProxy servers to monitor
servers:
    lb-primary:
        # Full URL to the CSV endpoint to poll
        endpoint: "http://lb-primary:8080/haproxy?stats;csv"
        # Number of seconds between endpoint polling operations
        update-interval: 10
        # If this HAProxy instance requires basic authentication
        username: admin
        password: admin
        # To which backends should monitoring data be sent?
        backends:
            - graylog1
            - prtg1
    lb-secondary:
        endpoint: "http://lb-secondary:8080/haproxy?stats;csv"
        update-interval: 60
        backends:
            - graylog2
            - logfile1
"""


class TestConfig(unittest.TestCase):

    def test_broken_yaml(self):
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config("some-non-yaml-data")

    def test_missing_base_fields(self):
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_MISSING_BASE_FIELDS1)
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_MISSING_BASE_FIELDS2)

    def test_invalid_base_fields(self):
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_INVALID_BACKENDS_FIELD)
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_INVALID_SERVERS_FIELD)

    def test_logging_validation(self):
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_INVALID_LOGGING_CONFIG)

        # check the default logging config
        config = load_haproxysessionmon_config(CASE_SIMPLE_VALID_CONFIG)
        self.assertEqual(CONFIG_DEFAULTS['logging'], config['logging'])

    def test_backend_validation(self):
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_INVALID_BACKEND_CONFIG)

    def test_gelf_backend_validation(self):
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_INVALID_GELF_CONFIG)

    def test_prtg_backend_validation(self):
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_INVALID_PRTG_CONFIG)

    def test_logfile_backend_validation(self):
        with self.assertRaises(ConfigError):
            load_haproxysessionmon_config(CASE_INVALID_LOGFILE_CONFIG)

    def test_complex_config_validation(self):
        config = load_haproxysessionmon_config(CASE_VALID_COMPLEX_CONFIG)
        self.assertIn('logging', config)
        self.assertIn('backends', config)
        self.assertIn('servers', config)
