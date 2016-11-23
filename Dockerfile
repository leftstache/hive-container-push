FROM python:3

WORKDIR /app
ADD requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

ADD container_push /app/container_push/
CMD python /app/container_push/main.py