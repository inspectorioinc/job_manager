FROM python:3-slim

WORKDIR app
COPY . /app

RUN pip install pipenv && pipenv install --system

