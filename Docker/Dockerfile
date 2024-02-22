FROM ubuntu:20.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update
RUN apt-get install -y unzip graphviz curl musescore3 python3-pip

RUN pip install --upgrade pip

WORKDIR /app

COPY /. /app/

# Hack to get around tensorflow-io issue - https://github.com/tensorflow/io/issues/1755
RUN pip install tensorflow-io
RUN pip uninstall -y tensorflow-io

ENV PYTHONPATH="${PYTHONPATH}:/app"