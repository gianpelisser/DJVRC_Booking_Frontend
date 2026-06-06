"""
Cliente HTTP centralizado para comunicação com a API REST.
Toda chamada à API passa por aqui — nunca use requests diretamente nas rotas.
"""
import logging
import requests
from flask import current_app, session

log = logging.getLogger("djvrc.api")


def _headers(token: str = None) -> dict:
    """Monta headers com JWT da sessão se disponível."""
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    tok = token or session.get("access_token")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    else:
        log.debug("api_call: nenhum access_token na sessão")
    return h


def _url(path: str) -> str:
    base = current_app.config["API_BASE_URL"].rstrip("/")
    return f"{base}{path}"


def _try_refresh() -> bool:
    """Tenta renovar o access_token com o refresh_token. Retorna True se ok."""
    refresh_token = session.get("refresh_token")
    if not refresh_token:
        return False
    try:
        resp = requests.post(
            _url("/auth/refresh"),
            headers={"Authorization": f"Bearer {refresh_token}",
                     "Content-Type": "application/json"},
            timeout=10,
        )
        if resp.status_code == 200:
            new_token = resp.json().get("data", {}).get("access_token")
            if new_token:
                session["access_token"] = new_token
                log.info("Token renovado com sucesso.")
                return True
    except requests.RequestException as e:
        log.warning("Falha ao renovar token: %s", e)
    return False


def api_get(path: str, params: dict = None) -> dict | None:
    try:
        resp = requests.get(_url(path), headers=_headers(), params=params, timeout=10)

        # Token expirado — tenta renovar e repetir uma vez
        if resp.status_code == 401 and _try_refresh():
            resp = requests.get(_url(path), headers=_headers(), params=params, timeout=10)

        if resp.status_code == 200:
            return resp.json()

        log.debug("api_get %s -> %d", path, resp.status_code)
        return None
    except requests.RequestException as e:
        log.warning("api_get %s erro: %s", path, e)
        return None


def api_post(path: str, data: dict = None) -> tuple[dict | None, int]:
    try:
        resp = requests.post(_url(path), headers=_headers(), json=data, timeout=10)

        if resp.status_code == 401 and _try_refresh():
            resp = requests.post(_url(path), headers=_headers(), json=data, timeout=10)

        log.debug("api_post %s -> %d", path, resp.status_code)
        return resp.json(), resp.status_code
    except requests.RequestException as e:
        log.warning("api_post %s erro: %s", path, e)
        return None, 500


def api_put(path: str, data: dict = None) -> tuple[dict | None, int]:
    try:
        resp = requests.put(_url(path), headers=_headers(), json=data, timeout=10)

        if resp.status_code == 401 and _try_refresh():
            resp = requests.put(_url(path), headers=_headers(), json=data, timeout=10)

        log.debug("api_put %s -> %d", path, resp.status_code)
        return resp.json(), resp.status_code
    except requests.RequestException as e:
        log.warning("api_put %s erro: %s", path, e)
        return None, 500


def api_delete(path: str) -> tuple[dict | None, int]:
    try:
        resp = requests.delete(_url(path), headers=_headers(), timeout=10)

        if resp.status_code == 401 and _try_refresh():
            resp = requests.delete(_url(path), headers=_headers(), timeout=10)

        return resp.json(), resp.status_code
    except requests.RequestException as e:
        log.warning("api_delete %s erro: %s", path, e)
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
