from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app.core.api import api_post, api_get
from urllib.parse import urlencode

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/login")
def login():
    if session.get("access_token"):
        return redirect(url_for("index"))
    return render_template("auth/login.html", register_config=_get_register_config())


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
    return render_template("auth/login.html", email=email, register_config=_get_register_config())


@auth_bp.get("/register")
def register():
    if session.get("access_token"):
        return redirect(url_for("index"))
    # Dados pre-preenchidos vindos do Discord (query params)
    prefill = {
        "discord_id":           request.args.get("discord_id", ""),
        "discord_username":     request.args.get("discord_username", ""),
        "discord_display_name": request.args.get("discord_display_name", ""),
        "discord_avatar":       request.args.get("discord_avatar", ""),
        "google_id":            request.args.get("google_id", ""),
        "google_name":          request.args.get("google_name", ""),
        "google_avatar":        request.args.get("google_avatar", ""),
        "email":                request.args.get("email", ""),
        "username":             request.args.get("username", ""),
    }
    return render_template("auth/register.html", prefill=prefill, register_config=_get_register_config())


@auth_bp.post("/register")
def register_post():
    form     = request.form
    username = form.get("username", "").strip()
    email    = form.get("email", "").strip()
    password = form.get("password", "")
    is_dj    = form.get("is_dj") == "on"

    # Dados do Discord (hidden fields, presentes se veio pelo OAuth)
    discord_id           = form.get("discord_id", "").strip()
    discord_username     = form.get("discord_username", "").strip()
    discord_display_name = form.get("discord_display_name", "").strip()
    discord_avatar       = form.get("discord_avatar", "").strip()
    google_id     = form.get("google_id", "").strip()
    google_name   = form.get("google_name", "").strip()
    google_avatar = form.get("google_avatar", "").strip()

    payload = {
        "username":         username,
        "email":            email,
        "is_dj":            is_dj,
        "discord_id":           discord_id or None,
        "discord_username":     discord_username or None,
        "discord_display_name": discord_display_name or None,
        "discord_avatar":       discord_avatar or None,
        "google_id":     google_id or None,
        "google_name":   google_name or None,
        "google_avatar": google_avatar or None,
    }
    if not discord_id:
        payload["password"] = password

    data, status = api_post("/auth/register", payload)

    if status == 201 and data and data.get("success"):
        # OAuth (Discord ou Google) — já vem verificado, loga direto
        if data["data"].get("access_token"):
            _save_session(data["data"])
            flash("Conta criada! Bem-vindo ao DJ VRC Booking!", "success")
            return redirect(url_for("index"))

        # Cadastro por email — precisa verificar
        flash("Cadastro realizado! Verifique seu e-mail para ativar a conta.", "success")
        return redirect(url_for("auth.login"))

    msg = data.get("message", "Erro ao cadastrar.") if data else "Erro de conexao com a API."
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
        register_config=_get_register_config(),
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
            "discord_id":           d.get("discord_id", ""),
            "discord_username":     d.get("discord_username", ""),
            "discord_display_name": d.get("discord_display_name", ""),
            "discord_avatar":       d.get("discord_avatar", ""),
            "email":                d.get("email", ""),
            "username":             d.get("suggested_username", ""),
        })
        flash("Quase la! Complete seu cadastro para continuar.", "info")
        return redirect(url_for("auth.register") + "?" + params)

    flash("Resposta inesperada da API.", "danger")
    return redirect(url_for("auth.login"))


# --- Google OAuth ---

@auth_bp.get("/google")
def google_login():
    data = api_get("/auth/google")
    if not data or not data.get("success"):
        flash("Login com Google não disponível.", "danger")
        return redirect(url_for("auth.login"))
    return redirect(data["data"]["redirect_url"])


@auth_bp.get("/google/callback")
def google_callback():
    from urllib.parse import urlencode
    code  = request.args.get("code", "")
    error_param = request.args.get("error")
    if error_param:
        flash("Autorização cancelada.", "warning")
        return redirect(url_for("auth.login"))

    data = api_get(f"/auth/google/callback?code={code}")
    if not data or not data.get("success"):
        flash("Falha ao autenticar com Google.", "danger")
        return redirect(url_for("auth.login"))

    d      = data["data"]
    action = d.get("action")

    if action == "login":
        session["access_token"]  = d["access_token"]
        session["refresh_token"] = d["refresh_token"]
        session["user"]          = d["user"]
        flash(f"Bem-vindo, {d['user']['username']}!", "success")
        return redirect(url_for("account.dashboard"))

    # action == "register"
    params = urlencode({
        "google_id":     d.get("google_id", ""),
        "google_name":   d.get("google_name", ""),
        "google_avatar": d.get("google_avatar", ""),
        "email":         d.get("email", ""),
        "username":      d.get("suggested_username", ""),
    })
    return redirect(url_for("auth.register") + "?" + params)


# --- Contato ---

@auth_bp.get("/contact")
def contact():
    return render_template("auth/contact.html")


@auth_bp.post("/contact")
def contact_post():
    form    = request.form
    nome    = form.get("name", "").strip()
    email   = form.get("email", "").strip()
    assunto = form.get("subject", "").strip()
    msg     = form.get("message", "").strip()

    if not nome or not email or not assunto or not msg:
        flash("Por favor preencha todos os campos.", "danger")
        return render_template("auth/contact.html",
                               prefill={"name": nome, "email": email,
                                        "subject": assunto, "message": msg})

    data, status = api_post("/auth/contact",
                            {"name": nome, "email": email,
                             "subject": assunto, "message": msg})

    if status == 200 and data and data.get("success"):
        flash("Mensagem enviada! Responderemos em breve no seu e-mail.", "success")
        return redirect(url_for("auth.contact"))

    msg_err = data.get("message", "Erro ao enviar.") if data else "Erro de conexão."
    flash(msg_err, "danger")
    return render_template("auth/contact.html",
                           prefill={"name": nome, "email": email,
                                    "subject": assunto, "message": msg})


# --- Legal pages ---

@auth_bp.get("/privacy")
def privacy():
    return render_template("legal/privacy.html")


@auth_bp.get("/terms")
def terms():
    return render_template("legal/terms.html")


# --- Register Config Helper ---

def _get_register_config():
    """Busca na API quais métodos de cadastro estão ativos."""
    data = api_get("/auth/register-config")
    if data and data.get("success"):
        return data.get("data", {})
    # Fallback: todos ativos
    return {"email_enabled": True, "discord_enabled": True, "google_enabled": False}


# --- Helpers ---

def _save_session(data: dict) -> None:
    session.permanent = True
    session["access_token"]  = data.get("access_token")
    session["refresh_token"] = data.get("refresh_token")
    session["user"]          = data.get("user")
