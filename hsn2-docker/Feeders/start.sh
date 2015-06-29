#!/bin/bash

sed -i -e "s/-connector 127.0.0.1/-connector framework/g" /etc/init.d/hsn2-file-feeder
sed -i -e "s/--connector=127.0.0.1/--connector=framework/g" /etc/init.d/hsn2-url-feeder
sed -i -e "s/--datastore=127.0.0.1/--datastore=datastore/g" /etc/init.d/hsn2-url-feeder

/etc/init.d/hsn2-file-feeder start
/etc/init.d/hsn2-url-feeder start

while true; do sleep 1; done