FROM python:3-alpine

WORKDIR app
COPY . /app

RUN pip install pipenv && pipenv install --system

