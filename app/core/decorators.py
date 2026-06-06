from functools import wraps
from flask import session, redirect, url_for, flash, abort


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("access_token"):
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("access_token"):
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        user = session.get("user", {})
        if user.get("role") != "admin":
            abort(403)
        return fn(*args, **kwargs)
    return wrapper


def dj_required(fn):
    """Requer is_dj=True na sessao (ou role admin)."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("access_token"):
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        user = session.get("user", {})
        if not user.get("is_dj") and user.get("role") != "admin":
            flash("Ative o modo DJ para acessar está página.", "warning")
            return redirect(url_for("account.dashboard"))
        return fn(*args, **kwargs)
    return wrapper


def contractor_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("access_token"):
            flash("Faça login para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return fn(*args, **kwargs)
    return wrapper
