[Tesla-Preheat](http://github.com/morpheus65535/tesla_preheat) is a simple scheduler to preheat your Tesla car using the Tesla API.


## Usage

You must provide a valid anti-captcha.com APIKEY to solve the reCaptcha implemented by Tesla. You should bind a volume to store the cached token outside the container.

Here are some example snippets to help you get started creating a container.

### docker

```
docker create \
  --name=tesla_preheat \
  -e TZ=America/Toronto \
  -e EMAIL=my_tesla_email \
  -e PASSWORD=my_tesla_password \
  -e ANTI_CAPTCHA_APIKEY=my_anti_captcha_com_apikey \
  -e CABIN_PREHEAT_ENABLED=1 \
  -e MAX_DEFROST=1 \
  -e DRIVER_TEMP=22 \
  -e PASSENGER_TEMP=22 \
  -e DRIVER_SEAT_TEMP=2 \
  -e DRIVER_SEAT_ENABLED=1 \
  -e PREHEAT_DAY_OF_WEEK=0,1,2,3,4 \
  -e PREHEAT_HOUR=7 \
  -e PREHEAT_MINUTE=0 \
  -e PREHEAT_DURATION=15 \
  -v /your/config/path/cache.json:/tesla/cache.json \
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
      - EMAIL=my_tesla_email
      - PASSWORD=my_tesla_password
      - ANTI_CAPTCHA_APIKEY=my_anti_captcha_com_apikey
      - CABIN_PREHEAT_ENABLED=1
      - MAX_DEFROST=1
      - DRIVER_TEMP=22
      - PASSENGER_TEMP=22
      - DRIVER_SEAT_TEMP=2
      - DRIVER_SEAT_ENABLED=1
      - PREHEAT_DAY_OF_WEEK=0,1,2,3,4
      - PREHEAT_HOUR=7
      - PREHEAT_MINUTE=0
      - PREHEAT_DURATION=15
    volumes:
      - /your/config/path/cache.json:/tesla/cache.json
    restart: unless-stopped
```

## Parameters

| Parameter | Function |
| :----: | --- |
| `-e TZ=America/Toronto` | Specify a timezone to use EG America/Toronto, this is required for Tesla_preheat |
| `-e EMAIL=elon@tesla.com` | Email used for your Tesla account, this is required for Tesla_preheat |
| `-e PASSWORD=starship` | Password used for your Tesla account, this is required for Tesla_preheat |
| `-e ANTI_CAPTCHA_APIKEY=1c9e6fb13a88daa75470bf2cd73d6154` | APIKEY from your anti-captcha.com account, this is required for Tesla_preheat |
| `-e PREHEAT_DAY_OF_WEEK=0,1,2,3,4` | Comma separated list of integer representation of days of the week from Monday(0) to Sunday(6) |
| `-e PREHEAT_HOUR=7` | Integer representation of hour of the day (0-23) to start preheating your Tesla |
| `-e PREHEAT_MINUTE=0` | Integer representation of minute of the hour (0-59) to start preheating your Tesla |
| `-e PREHEAT_DURATION=15` | Duration of the preheating cycle in minutes (ie: 15 minutes) |
| `-e DRIVER_TEMP=21` | Integer representation of temperature in celcius for the driver side vent heater (does not support decimal) |
| `-e PASSENGER_TEMP=21` | Integer representation of temperature in celcius for the passenger side vent heater (does not support decimal) |
| `-e CABIN_PREHEAT_ENABLED=1` | Enable/disable vent heater (1 for enabled, 0 for disabled) |
| `-e MAX_DEFROST=1` | Enable/disable maximum defrost (1 for enabled, 0 for disabled) |
| `-e DRIVER_SEAT_TEMP=2` | Driver heating seat level (0 for disabled, from 1 to 3 to heat) |
| `-e DRIVER_SEAT_ENABLED=1` | Enable/disable driver heating seat (1 for enabled, 0 for disabled) |
| `-e PASSENGER_SEAT_TEMP=0` | Passenger heating seat level (0 for disabled, from 1 to 3 to heat) |
| `-e PASSENGER_SEAT_ENABLED=0` | Enable/disable passenger heating seat (1 for enabled, 0 for disabled) |
| `-e REAR_DRIVER_SIDE_SEAT_TEMP=0` | Rear driver side heating seat level (0 for disabled, from 1 to 3 to heat) |
| `-e REAR_DRIVER_SIDE_SEAT_ENABLED=0` | Enable/disable rear driver side heating seat (1 for enabled, 0 for disabled) |
| `-e REAR_CENTER_SEAT_TEMP=0` | Rear passenger side heating seat level (0 for disabled, from 1 to 3 to heat) |
| `-e REAR_CENTER_SEAT_ENABLED=0` | Enable/disable rear center heating seat (1 for enabled, 0 for disabled) |
| `-e REAR_PASSENGER_SIDE_SEAT_TEMP=0` | Rear center heating seat level (0 for disabled, from 1 to 3 to heat) |
| `-e REAR_PASSENGER_SIDE_SEAT_ENABLED=0` | Enable/disable rear passenger side heating seat (1 for enabled, 0 for disabled) |
