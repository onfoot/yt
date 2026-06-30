import os
import threading
import yt_dlp

from flask import Blueprint, request, render_template, jsonify

from . import socketio
from .utils import list_mp4_video_files, format_filename, safe_filename, video_directory, VIDEO_EXTENSION

bp = Blueprint('main', __name__)

downloads_in_progress = {}


@bp.route('/', methods=['GET'])
def index():
    video_files = list_mp4_video_files()
    formatted_video_files = [
        {
            'original_filename': filename,
            'sanitized_title': format_filename(filename)
        } for filename in video_files
    ]
    return render_template('index.html', video_files=formatted_video_files)


@bp.route('/downloads', methods=['GET'])
def downloads():
    return jsonify(downloads_in_progress)


@bp.route('/download', methods=['POST'])
def download():
    data = request.get_json(silent=True) or {}
    video_url = data.get('url')
    if not video_url:
        return jsonify({'error': 'url is required'}), 400

    threading.Thread(target=download_video, args=(video_url,)).start()
    return jsonify({'status': 'started'})


def yt_progress_hook(url, d):
    socketio.emit('download_progress', {
        'url': url,
        'status': d['status'],
        'progress': d.get('_percent_str', '0%')
    })


def create_progress_hook(url):
    def progress_hook(d):
        yt_progress_hook(url, d)
    return progress_hook


def download_video(url):
    directory = video_directory()
    ydl_opts = {
        'outtmpl': os.path.join(directory, '%(id)s.%(ext)s'),
        'format': "bv[ext=mp4][vcodec~='^((he|a)vc|h26[45])']+ba[ext=m4a]",
        'postprocessors': [
            {
                'already_have_subtitle': False,
                'key': 'FFmpegEmbedSubtitle'
            },
            {
                'add_chapters': True,
                'add_infojson': 'if_exists',
                'add_metadata': True,
                'key': 'FFmpegMetadata'
            },
            {
                'already_have_thumbnail': False,
                'key': 'EmbedThumbnail'
            },
            {
                'key': 'FFmpegConcat',
                'only_multi_video': True,
                'when': 'playlist'
            }
        ],
        'subtitlesformat': 'ass',
        'writesubtitles': True,
        'writethumbnail': True,
        'updatetime': False,
        'js_runtimes': ['node'],
        'progress_hooks': [create_progress_hook(url)],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            downloads_in_progress[url] = 'started'
            info_dict = ydl.extract_info(url, download=False)
            video_id = info_dict.get('id', 'video')
            video_title = info_dict.get('title', 'video')
            video_filename = f'{video_id}{VIDEO_EXTENSION}'
            safe_name = safe_filename(video_title)
            ydl.download([url])
            os.rename(os.path.join(directory, video_filename), os.path.join(directory, safe_name))
            downloads_in_progress[url] = 'completed'
            socketio.emit('download_complete', {'url': url})
    except Exception as e:
        downloads_in_progress[url] = f'error {str(e)}'
        socketio.emit('download_error', {'url': url, 'error': str(e)})


@bp.route('/play', methods=['GET'])
def play():
    filename = request.args.get('file', default=None, type=str)
    formatted_video_file = {
        'original_filename': filename,
        'sanitized_title': format_filename(filename)
    }
    return render_template('play.html', video_file=formatted_video_file)


@bp.route('/delete', methods=['POST', 'DELETE'])
def delete():
    requested_name = request.args.get('file', default=None, type=str)
    if not requested_name:
        return 'file is required', 400

    videos_root = os.path.realpath(video_directory())
    resolved_file = os.path.realpath(os.path.join(videos_root, requested_name))

    if os.path.commonpath([videos_root, resolved_file]) != videos_root:
        return 'invalid file', 400

    if not os.path.exists(resolved_file):
        return 'file not found', 404

    os.remove(resolved_file)
    return requested_name, 200
