#!/bin/bash

/etc/init.d/couchdb start

sleep 3

/etc/init.d/hsn2-reporter start

while true; do sleep 1; done