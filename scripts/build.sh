#!/bin/bash

# Config to exit shell on any error
set -e

# Convenient colors
Green='\033[1;32m'
Cyan='\033[1;36m'
Red='\033[1;31m'
NoColor='\033[0m'

# Echo safe space
echo ""

# Check workspace
dir="scripts/"
if [ -d "$dir" ]
then
    echo "${Cyan}Welcome! This is a convenient script help you to build package.${NoColor}"
else
    echo "${Red}You need to stay at root folder to run scripts correctly!${NoColor}"
    exit 1
fi

# Echo safe space
echo ""

# Read version
currentversion=`cat scripts/latestversion`
echo "The current version is ${Green}$currentversion${NoColor}"
read -p "Please enter docker version for the new build (e.g., 0.0.1): " version
if [ -z "$version"  ]
then
    echo "${Red}Invalid version!${NoColor}"
    exit 1
fi

# Generate Dockerfile
rm -rf Dockerfile

cat << EOF > Dockerfile
FROM ohmnilabs/ohmnidev:latest

WORKDIR /home/ohmnidev/ohmni-follows-me

LABEL com.ohmnilabs.app.name=ohmni_app_following_me
LABEL com.ohmnilabs.app.version=$version
LABEL com.ohmnilabs.app.cmd="docker run -dt --privileged -v /data/data/com.ohmnilabs.telebot_rtc/files:/app -v /data:/data -v /dev:/dev --name ofm ohmnilabsvn/following_me:$version"
LABEL com.ohmnilabs.app.plugin.path = "/home/ohmnidev/ohmni-follows-me/plugins"

RUN apt-get update
COPY . .
RUN sh scripts/setup.sh
EOF

# Build docker image
sudo docker build -t following_me .
sudo docker tag following_me:latest ohmnilabsvn/following_me:$version
sudo docker push ohmnilabsvn/following_me:$version

# Update version
echo $version > scripts/latestversion