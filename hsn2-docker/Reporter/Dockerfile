FROM hsn2/base

COPY configurations /tmp/configurations

RUN /tmp/configurations/setup.sh rabbitmq-server hsn2-framework hsn2-reporter couchdb && sed -i -e "s/;bind_address = 127.0.0.1/bind_address = 0.0.0.0/g" /etc/couchdb/local.ini

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]