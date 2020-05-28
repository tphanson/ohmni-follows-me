# [Ohmni] Following Me

## Quick start

```
wget https://raw.githubusercontent.com/tphanson/ohmni-follows-me/master/scripts/install.sh -P /tmp && chmod +x /temp/install.sh && sh install.sh
```

## Docker

### Usage guides

Follow this step-by-step [tutorial](https://docs.google.com/document/d/1ibkJVjdmrauHGQ0eP4HKzEVfYO_O8CrFDh9kXa5Ijmo/edit?usp=sharing)

### Build docker image

```
sh scripts/build.sh
```

### Run docker image 

```
docker run -it --privileged -v /data/data/com.ohmnilabs.telebot_rtc/files:/app -v /data:/data -v /dev:/dev --name ofm ohmnilabsvn/following_me:<version>
```