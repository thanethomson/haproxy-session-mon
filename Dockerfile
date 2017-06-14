FROM python:3.6-alpine
LABEL maintainer "Thane Thomson <connect@thanethomson.com>"

# Add gcc/build deps
RUN apk add --update alpine-sdk

# Set up our default configuration path
ENV HAPROXYSM_CONFIG_PATH /etc/haproxysessionmon/
RUN mkdir -p ${HAPROXYSM_CONFIG_PATH}

WORKDIR /usr/src/app
COPY . .
RUN python setup.py install

# No need for the build deps during execution
RUN apk del --purge alpine-sdk

# Default configuration file path
ENV HAPROXYSM_CONFIG_FILE ${HAPROXYSM_CONFIG_PATH}config.yml
VOLUME ${HAPROXYSM_CONFIG_PATH}

CMD [ "haproxysessionmon" ]
