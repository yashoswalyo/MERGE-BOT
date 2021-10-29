FROM python:latest

ENV VIRTUAL_ENV "/venv"
RUN python -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y ffmpeg
RUN python -m pip install --upgrade pip

WORKDIR /usr/src/app

COPY . .

RUN pip install -U -r requirements.txt

CMD [ "python", "bot.py" ]
