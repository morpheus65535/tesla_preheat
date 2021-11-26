[Tesla-Preheat](http://github.com/morpheus65535/tesla_preheat) is a simple scheduler to preheat your Tesla car using the Tesla API.


## Usage

You must provide a valid anti-captcha.com APIKEY to solve the reCaptcha implemented by Tesla. You should bind a volume to store the cached token outside the container.

Here are some example snippets to help you get started creating a container.

### docker

```
docker create \
  --name=tesla_preheat \
  -e TZ=America/Toronto \
  -v /your/container/config/:/tesla/config/ \
  --restart unless-stopped \
  morpheus65535/tesla_preheat
```


### docker-compose

Compatible with docker-compose v2 schemas.

```
---
version: "2.1"
services:
  tesla_preheat:
    image: morpheus65535/tesla_preheat
    container_name: tesla_preheat
    environment:
      - TZ=America/Toronto
    volumes:
      - /your/container/config/:/tesla/config/
    restart: unless-stopped
```

## Parameters

| Parameter | Function |
| :----: | --- |
| `-e TZ=America/Toronto` | Specify a timezone to use EG America/Toronto, this is required for Tesla_preheat |
