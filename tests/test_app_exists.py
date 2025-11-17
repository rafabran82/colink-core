# Updated COLINK test: verify FastAPI app loads correctly

from colink_core.api.main import app

def test_app_exists():
    assert app is not None
