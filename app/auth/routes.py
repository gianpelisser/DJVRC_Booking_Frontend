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
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    data, status = api_post("/auth/login", {"email": email, "password": password})

    if status == 200 and data and data.get("success"):
        session.permanent = True
        session["access_token"] = data["data"]["access_token"]
        session["refresh_token"] = data["data"]["refresh_token"]
        session["user"] = data["data"]["user"]
        flash("Bem-vindo de volta!", "success")
        return redirect(url_for("index"))

    msg = data.get("message", "Erro ao fazer login.") if data else "Erro de conexão com a API."
    flash(msg, "danger")
    return render_template("auth/login.html", email=email)


@auth_bp.get("/register")
def register():
    if session.get("access_token"):
        return redirect(url_for("index"))
    return render_template("auth/register.html")


@auth_bp.post("/register")
def register_post():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    role = request.form.get("role", "contractor")

    data, status = api_post("/auth/register", {
        "username": username,
        "email": email,
        "password": password,
        "role": role,
    })

    if status == 201 and data and data.get("success"):
        flash("Cadastro realizado! Verifique seu e-mail para ativar a conta.", "success")
        return redirect(url_for("auth.login"))

    msg = data.get("message", "Erro ao cadastrar.") if data else "Erro de conexão com a API."
    flash(msg, "danger")
    return render_template("auth/register.html", username=username, email=email, role=role)


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


# ─── Discord OAuth ─────────────────────────────────────────────────────────────

@auth_bp.get("/discord")
def discord_login():
    cfg = current_app.config
    params = {
        "client_id": cfg["DISCORD_CLIENT_ID"],
        "redirect_uri": cfg["DISCORD_REDIRECT_URI"],
        "response_type": "code",
        "scope": "identify email",
    }
    url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
    return redirect(url)


@auth_bp.get("/discord/callback")
def discord_callback():
    code = request.args.get("code")
    if not code:
        flash("Autenticação Discord cancelada.", "warning")
        return redirect(url_for("auth.login"))

    # Passa o code original para a API via GET (como o Discord faria)
    # A API troca o code por token internamente usando suas próprias credenciais.
    # IMPORTANTE: o DISCORD_REDIRECT_URI no .env da API deve apontar para
    # http://localhost:3000/auth/discord/callback (mesmo redirect do frontend).
    data = api_get(f"/auth/discord/callback", params={"code": code})
    status = 200 if data and data.get("success") else 400

    if status == 200 and data and data.get("success"):
        session.permanent = True
        session["access_token"] = data["data"]["access_token"]
        session["refresh_token"] = data["data"]["refresh_token"]
        session["user"] = data["data"]["user"]
        flash("Login com Discord realizado!", "success")
        return redirect(url_for("index"))

    msg = data.get("message", "Erro no login com Discord.") if data else "Erro de conexão."
    flash(msg, "danger")
    return redirect(url_for("auth.login"))
