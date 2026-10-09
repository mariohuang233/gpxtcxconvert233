import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from web_app import create_app

@pytest.fixture
def gpx():
    return (Path(__file__).parent/'fixtures/track.gpx').read_bytes()

@pytest.fixture
def app(tmp_path):
    instance = create_app({'TESTING': True, 'DATA_DIR': tmp_path, 'SECRET_KEY': 'test-only-key',
                           'ADMIN_TOKEN': 'test-admin', 'MAX_ACTIVE_JOBS': 2})
    yield instance
    instance.extensions['janitor_stop'].set()
    instance.extensions['executor'].shutdown(wait=True, cancel_futures=True)

@pytest.fixture
def client(app):
    return app.test_client()
