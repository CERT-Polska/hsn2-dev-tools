FROM hsn2/base

COPY configurations /tmp/configurations

RUN /tmp/configurations/setup.sh hsn2-webclient

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]