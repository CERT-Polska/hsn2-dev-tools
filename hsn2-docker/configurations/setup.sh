#!/bin/bash -e

#PACKAGES=$2

apt-get update

find /tmp/configurations/selections -exec debconf-set-selections {} \;

apt-get update
apt-get install  --no-install-recommends -y $@ 

#$(grep -vE "^\s*#" /tmp/configurations/$PACKAGES  | tr "\n" " ")
