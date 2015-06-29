#!/bin/bash

sed -i -e "s/--connector=127.0.0.1/--connector=framework/g" /etc/init.d/hsn2-thug
sed -i -e "s/--datastore=localhost/--datastore=datastore/g" /etc/init.d/hsn2-thug

/etc/init.d/hsn2-thug start

while true; do sleep 1; done