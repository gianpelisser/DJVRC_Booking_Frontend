from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.core.api import api_post, api_get
from urllib.parse import urlencode

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    if session.get("access_token"):
        return redirect(url_for("index"))
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    data, status = api_post("/auth/login", {"email": email, "password": password})

    if status == 200 and data and data.get("success"):
        _save_session(data["data"])
        flash("Bem-vindo de volta!", "success")
        return redirect(url_for("index"))

    msg = data.get("message", "Erro ao fazer login.") if data else "Erro de conexão com a API."
    flash(msg, "danger")
    return render_template("auth/login.html", email=email)


@auth_bp.get("/register")
def register():
    if session.get("access_token"):
        return redirect(url_for("index"))
    # Dados pre-preenchidos vindos do Discord (query params)
    prefill = {
        "discord_id":       request.args.get("discord_id", ""),
        "discord_username": request.args.get("discord_username", ""),
        "discord_avatar":   request.args.get("discord_avatar", ""),
        "email":            request.args.get("email", ""),
        "username":         request.args.get("username", ""),
    }
    via_discord = bool(prefill["discord_id"])
    return render_template("auth/register.html", prefill=prefill, via_discord=via_discord)


@auth_bp.post("/register")
def register_post():
    form     = request.form
    username = form.get("username", "").strip()
    email    = form.get("email", "").strip()
    password = form.get("password", "")
    is_dj    = form.get("is_dj") == "on"

    # Dados do Discord (hidden fields, presentes se veio pelo OAuth)
    discord_id       = form.get("discord_id", "").strip()
    discord_username = form.get("discord_username", "").strip()
    discord_avatar   = form.get("discord_avatar", "").strip()

    payload = {
        "username":         username,
        "email":            email,
        "is_dj":            is_dj,
        "discord_id":       discord_id or None,
        "discord_username": discord_username or None,
        "discord_avatar":   discord_avatar or None,
    }
    if not discord_id:
        payload["password"] = password

    data, status = api_post("/auth/register", payload)

    if status == 201 and data and data.get("success"):
        # Se veio pelo Discord, a API ja retorna tokens — loga direto
        if discord_id and data["data"].get("access_token"):
            _save_session(data["data"])
            flash("Conta criada! Bem-vindo ao DJ VRC Booking!", "success")
            return redirect(url_for("index"))

        flash("Cadastro realizado! Verifique seu e-mail para ativar a conta.", "success")
        return redirect(url_for("auth.login"))

    msg = data.get("message", "Erro ao cadastrar.") if data else "Erro de conexão com a API."
    flash(msg, "danger")
    prefill = {
        "discord_id":       discord_id,
        "discord_username": discord_username,
        "discord_avatar":   discord_avatar,
        "email":            email,
        "username":         username,
    }
    return render_template("auth/register.html",
        prefill=prefill,
        via_discord=bool(discord_id),
        is_dj=is_dj,
    )


@auth_bp.post("/logout")
def logout():
    api_post("/auth/logout")
    session.clear()
    flash("Você saiu da sua conta.", "info")
    return redirect(url_for("index"))


@auth_bp.get("/verify-email/<token>")
def verify_email(token):
    data = api_get(f"/auth/verify-email/{token}")
    if data and data.get("success"):
        flash("E-mail verificado com sucesso! Faça login.", "success")
    else:
        flash("Token inválido ou expirado.", "danger")
    return redirect(url_for("auth.login"))


@auth_bp.get("/forgot-password")
def forgot_password():
    return render_template("auth/forgot_password.html")


@auth_bp.post("/forgot-password")
def forgot_password_post():
    email = request.form.get("email", "").strip()
    api_post("/auth/forgot-password", {"email": email})
    flash("Se o e-mail existir, um link foi enviado.", "info")
    return render_template("auth/forgot_password.html")


@auth_bp.get("/reset-password/<token>")
def reset_password(token):
    return render_template("auth/reset_password.html", token=token)


@auth_bp.post("/reset-password/<token>")
def reset_password_post(token):
    password = request.form.get("password", "")
    data, status = api_post(f"/auth/reset-password/{token}", {"password": password})
    if status == 200 and data and data.get("success"):
        flash("Senha redefinida com sucesso!", "success")
        return redirect(url_for("auth.login"))
    msg = data.get("message", "Erro ao redefinir senha.") if data else "Erro de conexão."
    flash(msg, "danger")
    return render_template("auth/reset_password.html", token=token)


# --- Discord OAuth ---

@auth_bp.get("/discord")
def discord_login():
    cfg = current_app.config
    params = {
        "client_id":     cfg["DISCORD_CLIENT_ID"],
        "redirect_uri":  cfg["DISCORD_REDIRECT_URI"],
        "response_type": "code",
        "scope":         "identify email",
    }
    return redirect(f"https://discord.com/api/oauth2/authorize?{urlencode(params)}")


@auth_bp.get("/discord/callback")
def discord_callback():
    code = request.args.get("code")
    if not code:
        flash("Autenticacao Discord cancelada.", "warning")
        return redirect(url_for("auth.login"))

    # Repassa o code para a API processar
    data = api_get("/auth/discord/callback", params={"code": code})

    if not data or not data.get("success"):
        msg = data.get("message", "Erro no login com Discord.") if data else "Erro de conexão."
        flash(msg, "danger")
        return redirect(url_for("auth.login"))

    action = data.get("data", {}).get("action")

    # Usuario ja existia: loga direto
    if action == "login":
        _save_session(data["data"])
        flash("Login com Discord realizado!", "success")
        return redirect(url_for("index"))

    # Usuario novo: redireciona para cadastro com dados pre-preenchidos
    if action == "register":
        d = data["data"]
        params = urlencode({
            "discord_id":       d.get("discord_id", ""),
            "discord_username": d.get("discord_username", ""),
            "discord_avatar":   d.get("discord_avatar", ""),
            "email":            d.get("email", ""),
            "username":         d.get("suggested_username", ""),
        })
        flash("Quase la! Complete seu cadastro para continuar.", "info")
        return redirect(url_for("auth.register") + "?" + params)

    flash("Resposta inesperada da API.", "danger")
    return redirect(url_for("auth.login"))


# --- Helpers ---

def _save_session(data: dict) -> None:
    session.permanent = True
    session["access_token"]  = data.get("access_token")
    session["refresh_token"] = data.get("refresh_token")
    session["user"]          = data.get("user")
