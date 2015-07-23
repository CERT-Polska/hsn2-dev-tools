#!/bin/bash

/etc/init.d/hsn2-file-feeder start
/etc/init.d/hsn2-url-feeder start

while true; do sleep 1; done