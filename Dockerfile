FROM ubuntu:latest

ENV DEBIAN_FRONTEND="noninteractive"

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
ENV DEBIAN_FRONTEND="noninteractive"
ENV TARGETPLATFORM=${TARGETPLATFORM:-linux/amd64}
ARG BUILDPLATFORM

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


