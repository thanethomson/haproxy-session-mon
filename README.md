# HAProxy Session Monitor

## Overview
The HAProxy Session Monitor is a simple Python 3-based application
(using the [asyncio](https://docs.python.org/3/library/asyncio.html)
native library in Python 3.4+) that polls one or more HAProxy
instances' stats endpoints for concurrent session data on HAProxy
backends. So far, there are several possible backends for monitoring:

1. Log file (local to machine)
2. Graylog (using [GELF](http://docs.graylog.org/en/stable/pages/gelf.html))
3. [PRTG](https://www.paessler.com/prtg) (*coming soon!*)

## Requirements
Only Python 3.5+ (ideally 3.6+) is required to run this software.

## Installation
In order to install the session monitor, it is recommended that one
install it into a virtual environment:

```bash
# Where do you want to install the monitor?
> cd /path/to/some/folder

# Create a virtual environment using Python 3.6 in the current folder
> python3.6 -m venv .

# Activate the virtual environment
> source bin/activate

# Run the session monitor
> haproxysessionmon -h
```

## Running
To run the application to monitor one or more HAProxy hosts, simply
run the following:

```bash
> haproxysessionmon -c /path/to/config-file.yml
```

See the following section for details as to how to configure the
session monitor. At present, the application runs purely in the
foreground (will allow for easy Dockerisation).

## Configuration
The HAProxy Session Monitor uses [YAML](https://en.wikipedia.org/wiki/YAML)
for configuration.

### Example
```yaml
# Logging configuration
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
    logfile1:
        type: logfile
        path: /var/log/session-count.log

# The HAProxy servers to monitor
servers:
    # The ID of the following HAProxy server will be "lb-primary"
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
```

### Application Logging Configuration
The HAProxy Session Monitor itself logs different levels of information,
and the **optional** `logging` section of the configuration file allows
one to specify the following configuration options:

* `level` (optional): The Python log level to be logged. Valid options
  include `DEBUG`, `INFO`, `WARNING`, `ERROR` and `CRITICAL`.
  Default: `INFO`.
* `file` (optional): If specified, this will cause the application to
  write its logs to a local file in the file system. This must contain
  the full path to the log file, and the application must have
  write privileges to this file. Default: `None`.
* `console` (optional): If `true`, application logs will also be
  output to `stdout`. Default: `true`.

### Graylog Backend Configuration
At present, this backend (type: `gelf`) allows you to pipe statistics
to a Graylog instance via UDP using [GELF](http://docs.graylog.org/en/stable/pages/gelf.html).
The following configuration options are possible for a Graylog backend:

* `host`: The host IP address for the collector endpoint.
* `port`: The host port for the collector endpoint.
* `facility`: A unique identifier for all of the statistics collected
  on behalf of this backend.

When this data is sent to the Graylog collector endpoint, the following
important fields are sent through:

* `host`: The ID of the HAProxy server for which these stats are
  relevant (this corresponds to the ID given to the server under the
  `servers` section of the configuration file.
* `facility`: The facility specified in the configuration for this
  particular backend.
* `sessions`: The integer value representing the number of concurrent
  sessions going through the HAProxy host being monitored.
* `backend`: The name given to the HAProxy backend (as configured in
  the HAProxy server itself) for which the concurrent session count
  is relevant.

### PRTG Backend Configuration
This backend is currently still under construction, and should
be available soon.

### Log File Backend Configuration
This backend (type: `logfile`) allows you to append statistics to a log
file by way of simple logging. The following configuration options are
possible for the log file:

* `path`: The full filesystem path to the file to which to write the
  logs.

## License

**The MIT License (MIT)**

Copyright (c) 2017 Thane Thomson

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
the Software, and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

