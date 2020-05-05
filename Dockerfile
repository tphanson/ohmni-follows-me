FROM ohmnilabs/ohmnidev:latest

WORKDIR /home/ohmnidev/ohmni-follows-me

RUN apt-get update
COPY . .
COPY ./plugins/followingMePlugin /data/data/com.ohmnilabs.telebot_rtc/files/plugins/
RUN sh install.sh
CMD [ "python3", "main.py", "--ohmni", "start" ]