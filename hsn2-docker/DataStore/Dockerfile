FROM hsn2/base

COPY configurations /tmp/configurations

RUN /tmp/configurations/setup.sh hsn2-data-store

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]