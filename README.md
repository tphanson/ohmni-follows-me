# Ohmni Follows Me

## Docker

### Usage guides

Follow this step-by-step [tutorial](https://docs.google.com/document/d/1ibkJVjdmrauHGQ0eP4HKzEVfYO_O8CrFDh9kXa5Ijmo/edit?usp=sharing)

### Build docker image

```
sudo docker build -t ohmni_follows_me .
sudo docker tag ohmni_follows_me:latest tphanson/ohmni_follows_me:<version>
sudo docker push tphanson/ohmni_follows_me:<version>
```

### Run docker image 

```
docker run --network="host" -v /data/data/com.ohmnilabs.telebot_rtc/files:/app -v /data:/data -w /home/ohmnidev/ohmni-follows-me --privileged -v /dev:/dev --security-opt seccomp:unconfined --name ofm tphanson/ohmni_follows_me:0.0.3
```

## Build your own development environment

In case you wish to build a development environment on your machine, follow this [Technical documents](./DEVELOPMENT.md)