FROM debian:wheezy

# Configure the database
RUN apt-get update && apt-get install wget vim procps java-wrappers openjdk-7-jre jsvc --no-install-recommends -y && echo "deb http://193.59.205.82:8080/hsn2/ experimental main" > /etc/apt/sources.list.d/hsn2.list && wget http://193.59.205.82:8080/hsn2/key.pub && apt-key add key.pub && apt-get update