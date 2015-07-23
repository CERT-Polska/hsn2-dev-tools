#!/bin/bash

/etc/init.d/mongodb start

sleep 4

/etc/init.d/hsn2-object-store-mongodb start

while true; do sleep 1; done