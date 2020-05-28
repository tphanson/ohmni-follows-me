#!/bin/bash

# Config to exit shell on any error
set -e

echo "*** Note that this script should only be run on Ohmni!"
currentversion=`cat latestversion`
read -p "Please enter docker version (press Enter to use default version $currentversion): " version
if [ -z "$version"  ]
then
    version=$currentversion
fi

# Pull docker image
docker rm ofm
docker run -it --privileged -v /data/data/com.ohmnilabs.telebot_rtc/files:/app -v /data:/data -v /dev:/dev --name ofm ohmnilabsvn/following_me:$version