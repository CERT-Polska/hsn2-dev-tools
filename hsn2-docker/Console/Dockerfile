FROM hsn2/base

COPY data /tmp/data

# Configure the database
RUN apt-get update && apt-get install -y --no-install-recommends python-hsn2-console hsn2-unicorn && sed -i -e "s/127.0.0.1/framework/g" /etc/hsn2/console.conf

ENTRYPOINT ["/bin/bash"]