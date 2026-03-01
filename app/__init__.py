import os
from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

socketio = SocketIO(cors_allowed_origins="*")


def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['VIDEOS_DIR'] = os.environ.get('VIDEOS_DIR', 'videos')

    from . import views
    app.register_blueprint(views.bp)
    socketio.init_app(app)
    return app
