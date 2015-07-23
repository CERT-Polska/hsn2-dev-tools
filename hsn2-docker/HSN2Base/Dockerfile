FROM debian:wheezy


RUN apt-get update && apt-get install wget vim procps java-wrappers openjdk-7-jre jsvc --no-install-recommends -y && echo "deb http://172.17.42.1:8080/hsn2/ experimental main" > /etc/apt/sources.list.d/hsn2.list && wget http://172.17.42.1:8080/hsn2/key.pub && apt-key add key.pub && apt-get update
