# tests/test_app.py
import json
import pytest
import requests

import app

# — Dummy para simular arquivos Streamlit —
class DummyFile:
    def __init__(self, name, content, ctype):
        self.name = name
        self._content = content
        self.type = ctype

    def getvalue(self):
        return self._content

# — test parse_urls —————————————————————————————————————————————
def test_parse_urls_empty():
    assert app.parse_urls("") == []

def test_parse_urls_strip_and_blank_lines():
    text = "  http://a.com  \n\n  http://b.com\n "
    assert app.parse_urls(text) == ["http://a.com", "http://b.com"]

# — test build_files_payload ———————————————————————————————————————
def test_build_files_payload_single():
    f = DummyFile("doc.pdf", b"conteudo", "application/pdf")
    payload = app.build_files_payload([f])
    assert isinstance(payload, list) and len(payload) == 1
    key, (filename, data, ctype) = payload[0]
    assert key == "files"
    assert filename == "doc.pdf"
    assert data == b"conteudo"
    assert ctype == "application/pdf"

def test_build_files_payload_empty():
    assert app.build_files_payload([]) == []

# — Helpers para simular respostas HTTP —————————————————————————————
class DummyResponse:
    def __init__(self, json_data=None, status_code=200):
        self._json = {} if json_data is None else json_data
        self.status_code = status_code

    def raise_for_status(self):
        if not (200 <= self.status_code < 300):
            raise requests.HTTPError(f"Status {self.status_code}")

    def json(self):
        return self._json

# — test fetch_status ————————————————————————————————————————————
def test_fetch_status_success(monkeypatch):
    monkeypatch.setattr(requests, "get", lambda url: DummyResponse({"status":"ok","progress":77}, 200))
    assert app.fetch_status() == {"status":"ok","progress":77}

def test_fetch_status_failure(monkeypatch):
    # faz o requests.get levantar exceção
    def bad_get(url):
        raise requests.RequestException("falha de rede")
    monkeypatch.setattr(requests, "get", bad_get)
    assert app.fetch_status() == {"status":"unknown","progress":0}

# — test start_processing ——————————————————————————————————————————
def test_start_processing_ready(monkeypatch):
    # 1) mock do POST inicial
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: DummyResponse({}, 200))

    # 2) sequencia de estados: processing → ready
    states = [
        {"status":"processing","progress":10},
        {"status":"processing","progress":50},
        {"status":"ready","progress":100},
    ]
    monkeypatch.setattr(app, "fetch_status", lambda: states.pop(0))

    # 3) sleep fake para não atrasar o teste
    result = app.start_processing(urls=["u"], uploaded_files=[], sleep=lambda _: None)
    assert result is True

def test_start_processing_server_error(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: DummyResponse({}, 200))
    # servidor responde status 'error'
    monkeypatch.setattr(app, "fetch_status", lambda: {"status":"error","message":"falhou"})
    with pytest.raises(RuntimeError) as exc:
        app.start_processing([], [], sleep=lambda _: None)
    assert "falhou" in str(exc.value)

# — test query_api ———————————————————————————————————————————————
def test_query_api_success(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: DummyResponse({"answer":"resposta"}, 200))
    assert app.query_api("pergunta", k=5) == "resposta"

def test_query_api_empty_answer(monkeypatch):
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: DummyResponse({}, 200))
    with pytest.raises(ValueError) as exc:
        app.query_api("x")  # k=3 por default
    assert "Resposta vazia" in str(exc.value)

def test_query_api_http_error(monkeypatch):
    # retorna 400 para fazer raise_for_status()
    monkeypatch.setattr(requests, "post", lambda *args, **kwargs: DummyResponse({}, 400))
    with pytest.raises(requests.HTTPError):
        app.query_api("erro")

