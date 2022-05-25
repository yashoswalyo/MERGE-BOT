FROM ubuntu:latest

WORKDIR /usr/src/mergebot
RUN chmod 777 /usr/src/mergebot

RUN apt-get update && apt-get install -y python3 python3-pip curl ffmpeg

RUN curl https://rclone.org/install.sh | bash

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x start.sh

CMD ["bash","start.sh"]
