#!/bin/bash

# Pull docker image
docker rm ofm
docker run -d --network="host" -v /data/data/com.ohmnilabs.telebot_rtc/files:/app -v /data:/data -w /home/ohmnidev/ohmni-follows-me --privileged -v /dev:/dev --security-opt seccomp:unconfined --name ofm tphanson/ohmni_follows_me:0.0.3
docker stop ofm
# Install plugins
docker cp ofm:/home/ohmnidev/ohmni-follows-me/plugins/followingMePlugin.js /data/data/com.ohmnilabs.telebot_rtc/files/plugins/

# Restart tbnode
setprop ctl.restart tb-node