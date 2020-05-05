FROM ohmnilabs/ohmnidev:latest

WORKDIR /home/ohmnidev/ohmni-follows-me

RUN apt-get update
COPY . .
RUN sh install.sh
RUN cp ./plugins/followingMePlugin.js /data/data/com.ohmnilabs.telebot_rtc/files/plugins/
CMD ["python3", "main.py", "--ohmni", "start"]