import json

import types

import steel_thread as st


def make_resp(status_code=200, json_obj=None, headers=None):
    r = types.SimpleNamespace()
    r.status_code = status_code
    r.headers = headers or {}
    r.json = lambda: (json_obj or {})

    def raise_for_status():
        if status_code >= 400 and status_code != 429:
            raise Exception(f"HTTP {status_code}")

    r.raise_for_status = raise_for_status
    return r


def test_call_model_retries_on_429(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy")
    runner = st.SteelThreadTRACE()
    runner.config.retries = 3

    calls = {"n": 0}

    def fake_post(url, json=None, headers=None, timeout=None):  # noqa: A002 - overlap with json module
        calls["n"] += 1
        if calls["n"] < 3:
            return make_resp(status_code=429)
        data = {
            "choices": [
                {"message": {"content": json["messages"][0]["content"][:10] + " ..."}}
            ]
        }
        return make_resp(status_code=200, json_obj=data, headers={"x-request-id": "abc123"})

    # Avoid sleeping during test
    monkeypatch.setattr(st.time, "sleep", lambda s: None)
    monkeypatch.setattr(st.requests, "post", fake_post)

    content = runner.call_model("hello world prompt")
    assert isinstance(content, str)
    assert calls["n"] == 3  # two 429 retries then one success

