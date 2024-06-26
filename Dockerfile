FROM python:3-alpine

RUN apk add ffmpeg

WORKDIR /app

COPY app/requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

EXPOSE 4999

ENV NAME Video downloader

CMD ["/bin/sh", "-c", "pip install -U yt-dlp && python app.py"]
