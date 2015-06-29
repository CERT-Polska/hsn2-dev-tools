FROM hsn2/base

# Configure the database
RUN apt-get update && apt-get install -y --no-install-recommends hsn2-data-store

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]