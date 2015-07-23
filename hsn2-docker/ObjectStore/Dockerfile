FROM hsn2/base

COPY configurations /tmp/configurations

RUN /tmp/configurations/setup.sh hsn2-object-store-mongodb

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]