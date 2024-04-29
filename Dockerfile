FROM ubuntu:24.04

WORKDIR /usr/src/mergebot
RUN chmod 777 /usr/src/mergebot

RUN apt-get -y update \
    && apt-get -y upgrade \
    && apt-get install apt-utils -y \ 
    && apt-get install -y python3-full python3-pip git wget curl pv jq ffmpeg neofetch mediainfo \
    && apt-get clean

## To enable rclone upload, uncommnet the following line; 
# RUN curl https://rclone.org/install.sh | bash

RUN python3 -m venv venv && chmod +x venv/bin/python

COPY requirements.txt .
RUN venv/bin/python -m pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["bash","start.sh"]
