FROM ohmnilabs/ohmnidev:latest

WORKDIR /home/ohmnidev

RUN apt-get update
RUN git clone https://github.com/tphanson/ohmni-follows-me.git
RUN cd ohmni-follows-me
RUN git checkout demo-2
RUN git pull origin demo-2
RUN install.sh