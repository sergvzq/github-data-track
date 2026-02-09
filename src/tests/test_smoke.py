from ghdata.config import load_settings


def test_settings_loads():
    settings = load_settings()
    assert hasattr(settings, "github_token")
