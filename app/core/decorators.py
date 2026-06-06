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


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not session.get("access_token"):
                flash("Faça login para continuar.", "warning")
                return redirect(url_for("auth.login"))
            user_role = session.get("user", {}).get("role")
            if user_role not in roles:
                abort(403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    return role_required("admin")(fn)


def dj_required(fn):
    return role_required("dj", "admin")(fn)


def contractor_required(fn):
    return role_required("contractor", "admin")(fn)
