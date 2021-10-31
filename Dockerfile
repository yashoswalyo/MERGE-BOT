FROM ubuntu:latest

WORKDIR /usr/src/mergebot
RUN chmod 777 /usr/src/mergebot

RUN apt-get -y update && apt-get -y upgrade && \
        apt-get install -y software-properties-common && \
        python3 python3-pip python3-lxml aria2 \
        p7zip-full p7zip-rar xz-utils wget curl pv jq \
        ffmpeg unzip neofetch mediainfo

RUN curl https://rclone.org/install.sh | bash

# Install Requirements Merge Bot
RUN apt-get -y update && apt-get -y upgrade && apt-get -y autoremove && apt-get -y autoclean

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["bash","start.sh"]


