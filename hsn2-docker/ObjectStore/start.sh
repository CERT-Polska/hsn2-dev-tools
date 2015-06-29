#!/bin/bash

sed -i -e "s/-connector 127.0.0.1/-connector framework/g" /etc/init.d/hsn2-object-store-mongodb
/etc/init.d/mongodb start
/etc/init.d/hsn2-object-store-mongodb start

while true; do sleep 1; done