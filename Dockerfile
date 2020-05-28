FROM ohmnilabs/ohmnidev:latest

WORKDIR /home/ohmnidev/ohmni-follows-me

LABEL com.ohmnilabs.app.name=ohmni_app_following_me
LABEL com.ohmnilabs.app.version=0.0.1
LABEL com.ohmnilabs.app.cmd="docker run -dt --privileged -v /data/data/com.ohmnilabs.telebot_rtc/files:/app -v /data:/data -v /dev:/dev --name ofm ohmnilabsvn/following_me:0.0.1"
LABEL com.ohmnilabs.app.plugin.path = "/home/ohmnidev/ohmni-follows-me/plugins"

RUN apt-get update
COPY . .
RUN sh scripts/setup.sh
