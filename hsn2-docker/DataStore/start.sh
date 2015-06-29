#!/bin/bash

sed -i -e "s/-rs 127.0.0.1/-rs framework/g" /etc/init.d/hsn2-data-store
/etc/init.d/hsn2-data-store start

while true; do sleep 1; done