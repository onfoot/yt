import os
from . import create_app, socketio

app = create_app()

if __name__ == '__main__':
    video_dir = app.config['VIDEOS_DIR']
    if not os.path.exists(video_dir):
        os.makedirs(video_dir)
    socketio.run(app, host='0.0.0.0', port=4999, allow_unsafe_werkzeug=True)
