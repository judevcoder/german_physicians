FROM python:2.7-jessie

RUN mkdir -p /usr/src/app
WORKDIR /usr/src/app

COPY physicians/requirements.txt /usr/src/app/
COPY . /usr/src/app
RUN pip install --no-cache-dir -r requirements.txt

CMD python physicians/physicians/spiders/runspider.py