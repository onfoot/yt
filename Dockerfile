FROM python:3.11

RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

EXPOSE 4999

ENV NAME Video downloader

CMD ["python", "app.py"]

