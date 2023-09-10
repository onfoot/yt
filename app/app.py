from flask import Flask, request, render_template, send_from_directory, redirect
import yt_dlp
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    video_url = None
    video_path = None

    if request.method == 'POST':
        video_url = request.form['video_url']
        download_video(video_url)
        return redirect('/')
    
    video_files = list_mp4_video_files()
    formatted_video_files = [
        {'original_filename': filename, 'sanitized_title': format_filename(filename)} for filename in video_files
    ]
    return render_template('index.html', video_files=formatted_video_files)

def list_mp4_video_files():
    video_files = [f for f in os.listdir('videos') if f.endswith('.mp4')]
    return video_files

def format_filename(filename):
    # Remove the '.mp4' extension and replace underscores with spaces
    return filename.replace('_', ' ').replace('.mp4', '')


def download_video(url):
    ydl_opts = {
        'outtmpl': 'videos/%(id)s.%(ext)s',
        'format': 'bv[ext=mp4][vcodec~=\'^((he|a)vc|h26[45])\']+ba[ext=m4a]',
        #'format_sort': {'codec': 'h264'}
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        video_id = info_dict.get('id', 'video')
        video_title = info_dict.get('title', 'video')
        video_filename = f'{video_id}.mp4'
        safe_filename = f'{video_title}.mp4'.replace(':', '_').replace('?', '_').replace(' ', '_')

        ydl.download([url])

        os.rename('videos/' + video_filename, 'videos/' + safe_filename)

    return safe_filename

@app.route('/videos/<path:filename>')
def download(filename):
    return send_from_directory('videos', filename, as_attachment=False)

if __name__ == '__main__':
    if not os.path.exists('videos'):
        os.makedirs('videos')
    app.run(host='0.0.0.0', port=4999, debug=True)

