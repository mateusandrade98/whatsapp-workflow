FROM python:3.9

COPY . /app

WORKDIR /app

COPY config/ .

RUN pip install -r requirements.txt

EXPOSE 8000

ENTRYPOINT ["python", "-u", "start.py"]