"""
Cliente HTTP centralizado para comunicação com a API REST.
Toda chamada à API passa por aqui — nunca use requests diretamente nas rotas.
"""
import requests
from flask import current_app, session


def _headers(extra: dict = None) -> dict:
    """Monta headers com JWT da sessão se disponível."""
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    token = session.get("access_token")
    if token:
        h["Authorization"] = f"Bearer {token}"
    if extra:
        h.update(extra)
    return h


def _url(path: str) -> str:
    base = current_app.config["API_BASE_URL"].rstrip("/")
    return f"{base}{path}"


def api_get(path: str, params: dict = None) -> dict | None:
    try:
        resp = requests.get(_url(path), headers=_headers(), params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except requests.RequestException:
        return None


def api_post(path: str, data: dict = None) -> tuple[dict | None, int]:
    try:
        resp = requests.post(_url(path), headers=_headers(), json=data, timeout=10)
        return resp.json(), resp.status_code
    except requests.RequestException:
        return None, 500


def api_put(path: str, data: dict = None) -> tuple[dict | None, int]:
    try:
        resp = requests.put(_url(path), headers=_headers(), json=data, timeout=10)
        return resp.json(), resp.status_code
    except requests.RequestException:
        return None, 500


def api_delete(path: str) -> tuple[dict | None, int]:
    try:
        resp = requests.delete(_url(path), headers=_headers(), timeout=10)
        return resp.json(), resp.status_code
    except requests.RequestException:
        return None, 500


def refresh_access_token() -> bool:
    """Tenta renovar o access_token usando o refresh_token da sessão."""
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return False
    try:
        resp = requests.post(
            _url("/auth/refresh"),
            headers={"Authorization": f"Bearer {refresh_token}", "Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            data = resp.json()
            session["access_token"] = data["data"]["access_token"]
            return True
    except requests.RequestException:
        pass
    return False
