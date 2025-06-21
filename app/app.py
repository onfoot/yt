from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import yt_dlp
import os
import threading

VIDEO_EXTENSION = ".mp4"

downloads_in_progress = {}

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route('/', methods=['GET'])
def index():
    video_files = list_mp4_video_files()
    formatted_video_files = [
        {
            'original_filename': filename,
            'sanitized_title': format_filename(filename)
        } for filename in video_files
    ]
    return render_template('index.html', video_files=formatted_video_files)

@app.route('/downloads', methods=['GET'])
def downloads():
    return jsonify(downloads_in_progress)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    video_url = data['url']
    threading.Thread(target=download_video, args=(video_url,)).start()
    return jsonify({'status': 'started'})

def list_mp4_video_files():
    files = [f for f in os.listdir('videos') if f.endswith(VIDEO_EXTENSION)]
    update_times = [os.path.getmtime(os.path.join('videos', f)) for f in files]
    files = [f for _, f in sorted(zip(update_times, files), reverse=True)]
    return files

def format_filename(filename):
    return filename.replace('_', ' ').replace(VIDEO_EXTENSION, '')

def yt_progress_hook(url, d):
    socketio.emit('download_progress', {'url': url, 'status': d['status'], 'progress': d.get('_percent_str', '0%')})

def create_progress_hook(url):
    def progress_hook(d):
        yt_progress_hook(url, d)
    return progress_hook

def download_video(url):
    ydl_opts = {
        'outtmpl': 'videos/%(id)s.%(ext)s',
        'format': 'bv[ext=mp4][vcodec~=\'^((he|a)vc|h26[45])\']+ba[ext=m4a]',
        'postprocessors': [
            {
                'already_have_subtitle': False,
                'key': 'FFmpegEmbedSubtitle'
            },
            {
                'add_chapters': True,
                'add_infojson': 'if_exists',
                'add_metadata': True,
                'key': 'FFmpegMetadata'},
            {
                'already_have_thumbnail': False, 'key': 'EmbedThumbnail'
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
        'progress_hooks': [create_progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            downloads_in_progress[url] = 'started'
            info_dict = ydl.extract_info(url, download=False)
            video_id = info_dict.get('id', 'video')
            video_title = info_dict.get('title', 'video')
            video_filename = f'{video_id}{VIDEO_EXTENSION}'
            safe_filename = f'{video_title}{VIDEO_EXTENSION}'.replace(':', '_').replace('?', '_').replace(' ', '_').replace('#', '_').replace('/', '_')
            ydl.download([url])
            os.rename('videos/' + video_filename, 'videos/' + safe_filename)
            downloads_in_progress[url] = 'completed'
            socketio.emit('download_complete', {'url': url})
    except Exception as e:
        downloads_in_progress[url] = f'error {str(e)}'
        socketio.emit('download_error', {'url': url, 'error': str(e)})

@app.route('/play', methods=['GET'])
def play():
    filename = request.args.get('file', default=None, type=str)
    formatted_video_file = {
            'original_filename': filename,
            'sanitized_title': format_filename(filename)
    }
    return render_template('play.html', video_file=formatted_video_file)

@app.route('/delete', methods=['POST', 'DELETE'])
def delete():
    filename = request.args.get('file', default=None, type=str)
    filename = os.path.normpath('videos/{filename}'.format(filename=filename))
    if filename.startswith('videos/'):
        os.remove(filename)
    return '{filename}', 200

if __name__ == '__main__':
    if not os.path.exists('videos'):
        os.makedirs('videos')

    socketio.run(app, host='0.0.0.0', port=4999, allow_unsafe_werkzeug=True)
    
