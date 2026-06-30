import os
from flask import current_app
from werkzeug.utils import secure_filename

VIDEO_EXTENSION = ".mp4"


def video_directory():
    return current_app.config['VIDEOS_DIR']


def list_mp4_video_files():
    directory = video_directory()
    if not os.path.exists(directory):
        os.makedirs(directory)
    files = [f for f in os.listdir(directory) if f.endswith(VIDEO_EXTENSION)]
    update_times = [os.path.getmtime(os.path.join(directory, f)) for f in files]
    return [f for _, f in sorted(zip(update_times, files), reverse=True)]


def format_filename(filename):
    return filename.replace('_', ' ').replace(VIDEO_EXTENSION, '')


def safe_filename(title):
    base = secure_filename(title) or 'video'
    if not base.lower().endswith(VIDEO_EXTENSION):
        base = f"{base}{VIDEO_EXTENSION}"
    return base
