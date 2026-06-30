import os
from app import create_app
from app.utils import list_mp4_video_files, safe_filename, format_filename, VIDEO_EXTENSION


def test_safe_filename_simple(tmp_path):
    app = create_app()
    with app.app_context():
        name = safe_filename('Test: Video?')
    assert name == f'Test_Video{VIDEO_EXTENSION}'
    assert ':' not in name and '?' not in name and ' ' not in name


def test_safe_filename_fallback_when_name_is_empty():
    app = create_app()
    with app.app_context():
        name = safe_filename('////')
    assert name == f'video{VIDEO_EXTENSION}'


def test_list_mp4_video_files_sorted(tmp_path):
    (tmp_path / 'one.mp4').write_text('1')
    (tmp_path / 'two.mp4').write_text('2')
    os.utime(tmp_path / 'one.mp4', (1, 1))
    app = create_app()
    app.config['VIDEOS_DIR'] = str(tmp_path)
    with app.app_context():
        files = list_mp4_video_files()
    assert files == ['two.mp4', 'one.mp4']


def test_format_filename():
    assert format_filename('My_Video.mp4') == 'My Video'


def test_delete_blocks_path_traversal(tmp_path):
    app = create_app()
    app.config['VIDEOS_DIR'] = str(tmp_path)
    client = app.test_client()

    response = client.post('/delete?file=../etc/passwd')

    assert response.status_code == 400
