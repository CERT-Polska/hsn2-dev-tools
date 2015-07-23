FROM hsn2/base

COPY configurations /tmp/configurations

RUN /tmp/configurations/setup.sh rabbitmq-server hsn2-framework

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]