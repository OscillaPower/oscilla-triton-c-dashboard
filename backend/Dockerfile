# Use a base Python image
FROM python:3.10-slim

# giving user name. which is not executed by docker
MAINTAINER CanaryRequestCronJob

# Creating Working Dir
WORKDIR /app

# Requirements for matplotlib
RUN apt-get update && apt-get install -y python3 python3-pip cron

# Requirements for sqlite
RUN apt-get install -y sqlite3 libsqlite3-dev

RUN pip3 install --upgrade setuptools
# RUN /usr/local/bin/python3 -m pip install --upgrade pip

COPY requirements.txt /tmp/
RUN pip3 install --requirement /tmp/requirements.txt
COPY . /tmp/

# `cron`
RUN touch /var/log/cron.log

# Copying the crontab file
COPY crontab /etc/cron.d/crontab

# Copy runner scripts from current dir to `app` in docker container
ADD . /crontab
ADD *.py /app/

# run the crontab file
RUN crontab /etc/cron.d/crontab

# Executing crontab command
CMD cron && tail -f /var/log/cron.log
