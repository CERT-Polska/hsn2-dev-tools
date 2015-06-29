#!/bin/bash

rabbitmq-plugins enable rabbitmq_management
/etc/init.d/rabbitmq-server start
/etc/init.d/hsn2-framework start

while true; do sleep 1; done