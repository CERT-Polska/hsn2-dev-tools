#!/bin/bash

sed -i -e "s/-connector 127.0.0.1/-connector framework/g" /etc/init.d/hsn2-reporter
sed -i -e "s@--dataStore http://localhost:8080@--dataStore http://datastore:8080@g" /etc/init.d/hsn2-reporter

/etc/init.d/couchdb start
/etc/init.d/hsn2-reporter start

while true; do sleep 1; done