from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.core.api import api_get, api_post, api_put
from app.core.decorators import login_required

account_bp = Blueprint("account", __name__)


@account_bp.get("/")
@login_required
def dashboard():
    """Painel principal do usuario — dados da conta + atalhos."""
    user = session.get("user", {})

    # Se for DJ, busca o perfil
    dj_profile = None
    if user.get("is_dj"):
        data = api_get("/djs/me")
        if data and data.get("success"):
            dj_profile = data.get("data")

    return render_template("account/dashboard.html",
        user=user,
        dj_profile=dj_profile,
    )


@account_bp.post("/update")
@login_required
def update():
    """Atualiza username, e-mail ou senha."""
    form     = request.form
    payload  = {}

    username = form.get("username", "").strip()
    email    = form.get("email", "").strip()
    password = form.get("password", "").strip()

    if username:
        payload["username"] = username
    if email:
        payload["email"] = email
    if password:
        payload["password"] = password

    if not payload:
        flash("Nenhuma alteracao enviada.", "warning")
        return redirect(url_for("account.dashboard"))

    data, status = api_put("/auth/me", payload)

    if status == 200 and data and data.get("success"):
        # Atualiza os dados da sessao
        session["user"] = data["data"]["user"]
        flash("Conta atualizada com sucesso!", "success")
    else:
        msg = data.get("message", "Erro ao atualizar.") if data else "Erro de conexao."
        flash(msg, "danger")

    return redirect(url_for("account.dashboard"))


@account_bp.post("/activate-dj")
@login_required
def activate_dj():
    """Ativa o modo DJ para a conta atual."""
    data, status = api_post("/auth/activate-dj")

    if status == 200 and data and data.get("success"):
        session["user"] = data["data"]["user"]
        flash("Modo DJ ativado! Agora crie seu perfil de DJ.", "success")
    else:
        msg = data.get("message", "Erro ao ativar modo DJ.") if data else "Erro de conexao."
        flash(msg, "danger")

    return redirect(url_for("account.dashboard"))
