FROM hsn2/base

# Configure the database
RUN apt-get update && apt-get install -y --no-install-recommends hsn2-object-store-mongodb

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]