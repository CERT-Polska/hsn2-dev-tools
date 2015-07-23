FROM hsn2/base

COPY configurations /tmp/configurations

RUN /tmp/configurations/setup.sh hsn2-file-feeder python-hsn2-url-feeder

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]