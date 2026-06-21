"""Tests for the prior-art guard hook (run as a subprocess against a temp git repo)."""
import json
import os
import subprocess
import sys
import textwrap

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUARD = os.path.join(REPO, "plugins", "railguards", "hooks", "prior-art-guard.py")


def _git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, check=True,
                   capture_output=True, text=True)


@pytest.fixture
def project(tmp_path):
    """A throwaway git repo with one existing data-source impl + a railguards config."""
    repo = tmp_path
    _git(repo, "init")
    src = repo / "src"
    src.mkdir()
    (src / "weather.py").write_text(textwrap.dedent("""
        import requests
        def fetch_weather(city):
            return requests.get("https://api.weather.example.com/" + city).json()
    """))
    (repo / "railguards.config.json").write_text(json.dumps({
        "prior_art": {
            "watch_dirs": ["/src/"],
            "known_sources": ["weather"],
            "domain_url_fragments": ["weather.example.com"],
        }
    }))
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=x@x", "-c", "user.name=x", "commit", "-m", "init")
    return repo


def _run(repo, payload):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(repo)}
    p = subprocess.run([sys.executable, GUARD], input=json.dumps(payload),
                       capture_output=True, text=True, env=env)
    return p.returncode, p.stderr


def _edit(repo, name, content):
    return {"tool_name": "Edit",
            "tool_input": {"file_path": str(repo / "src" / name), "new_string": content}}


def test_blocks_duplicate_data_source(project):
    code, err = _run(project, _edit(project, "forecast.py",
        'import requests\ndef fetch_weather_again(c):\n    return requests.get("https://api.weather.example.com/"+c).json()\n'))
    assert code == 2
    assert "weather.py" in err
    assert "prior-art-checked" in err.lower()


def test_passes_plain_logic_edit(project):
    code, err = _run(project, _edit(project, "util.py", "def add(a, b):\n    return a + b\n"))
    assert code == 0
    assert err.strip() == ""


def test_passes_with_ack(project):
    code, _ = _run(project, _edit(project, "forecast.py",
        '# prior-art-checked: distinct endpoint, reuse not viable\nimport requests\ndef fetch_weather_again(c):\n    return requests.get("https://api.weather.example.com/"+c).json()\n'))
    assert code == 0


def test_ignores_unwatched_dir(project):
    code, _ = _run(project, {"tool_name": "Edit", "tool_input": {
        "file_path": str(project / "docs" / "notes.py"),
        "new_string": 'import requests\ndef fetch_weather_x(c):\n    return requests.get("https://api.weather.example.com/"+c).json()\n'}})
    assert code == 0  # /docs/ not in watch_dirs


def test_non_edit_tool_is_ignored(project):
    code, _ = _run(project, {"tool_name": "Bash", "tool_input": {"command": "ls"}})
    assert code == 0
