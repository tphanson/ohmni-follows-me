FROM ohmnilabs/ohmnidev:latest

WORKDIR /home/ohmnidev/ohmni-follows-me

RUN apt-get update
COPY . .
RUN sh install.sh
CMD ["python3", "main.py", "--ohmni", "start"]