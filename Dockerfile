FROM python:3.10.12-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app

ADD . /app
RUN pip install --upgrade pip

ENV TG_BOT_TOKEN $TG_BOT_TOKEN
RUN apt-get update && apt-get install -y git
RUN apt-get -y install libgl1-mesa-glx && apt-get clean
RUN apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6
RUN pip install -r requirements.txt