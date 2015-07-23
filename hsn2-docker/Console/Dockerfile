FROM hsn2/base

COPY data /tmp/data
COPY configurations /tmp/configurations

# Configure the database
RUN /tmp/configurations/setup.sh python-hsn2-console hsn2-unicorn

ENTRYPOINT ["/bin/bash"]