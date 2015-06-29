#!/bin/bash

sed -i -e "s/-connector 127.0.0.1/-connector framework/g" /etc/init.d/hsn2-webclient
sed -i -e "s@--dataStore http://localhost:8080@--dataStore http://datastore:8080@g" /etc/init.d/hsn2-webclient

/etc/init.d/hsn2-webclient start

while true; do sleep 1; done