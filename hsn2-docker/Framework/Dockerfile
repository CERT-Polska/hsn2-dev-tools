FROM hsn2/base

# Configure the database
RUN apt-get update && apt-get install -y --no-install-recommends rabbitmq-server hsn2-framework

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]