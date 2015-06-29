FROM hsn2/base

# Configure the database
RUN apt-get update && apt-get install -y --no-install-recommends hsn2-file-feeder hsn2-url-feeder

COPY start.sh /start.sh

ENTRYPOINT ["/start.sh"]