"""Smoke test of the Streamlit start page (no backend needed)."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_start_page_renders_and_reports_unreachable_backend() -> None:
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()
    assert not at.exception
    assert at.title[0].value == "AI Proficiency Assessment"
    assert at.button[0].label == "Start assessment"


def test_start_with_backend_down_shows_error(monkeypatch) -> None:
    monkeypatch.setenv("BACKEND_URL", "http://127.0.0.1:9")
    at = AppTest.from_file(APP, default_timeout=20)
    at.run()
    at.button[0].click().run()
    assert at.error and "Cannot reach" in at.error[0].value
