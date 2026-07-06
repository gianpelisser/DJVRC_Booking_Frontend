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
    """Atualiza username, e-mail, apelido ou senha."""
    form     = request.form
    payload  = {}

    username     = form.get("username", "").strip()
    email        = form.get("email", "").strip()
    password     = form.get("password", "").strip()
    display_name = form.get("display_name", "").strip()
    timezone     = form.get("timezone", "").strip()

    if username:
        payload["username"] = username
    if email:
        payload["email"] = email
    if password:
        payload["password"] = password
    # display_name pode ser vazio (limpar apelido)
    payload["display_name"] = display_name or None
    if timezone:
        payload["timezone"] = timezone

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


@account_bp.post("/notifications")
@login_required
def update_notifications():
    """Atualiza preferências de notificação Discord."""
    form = request.form
    payload = {
        "notify_discord_dm":      form.get("notify_discord_dm") == "on",
        "notify_discord_webhook": form.get("notify_discord_webhook") == "on",
        "webhook_url":            form.get("webhook_url", "").strip() or None,
    }
    data, status = api_put("/auth/notifications", payload)
    if status == 200 and data and data.get("success"):
        session["user"] = data["data"]
    flash("Preferências de notificação salvas!", "success")
    return redirect(url_for("account.dashboard"))

@account_bp.post("/link/discord/manual")
@login_required
def link_discord_manual():
    from app.core.api import api_post
    form = request.form
    data, status = api_post("/auth/link/discord/manual", {
        "discord_id":       form.get("discord_id", "").strip(),
        "discord_username": form.get("discord_username", "").strip(),
    })
    if status == 200 and data and data.get("success"):
        session["user"] = data["data"]
        flash("Discord vinculado com sucesso!", "success")
    else:
        msg = data.get("message", "Erro ao vincular.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("account.dashboard"))


@account_bp.post("/unlink/discord")
@login_required
def unlink_discord():
    from app.core.api import api_post
    data, status = api_post("/auth/unlink/discord")
    if status == 200 and data and data.get("success"):
        u = session.get("user", {})
        u.pop("discord_id", None)
        u.pop("discord_username", None)
        u.pop("discord_display_name", None)
        u.pop("discord_avatar", None)
        session["user"] = u
        flash("Discord desvinculado.", "success")
    else:
        msg = data.get("message", "Erro.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("account.dashboard"))


@account_bp.post("/unlink/google")
@login_required
def unlink_google():
    from app.core.api import api_post
    data, status = api_post("/auth/unlink/google")
    if status == 200 and data and data.get("success"):
        u = session.get("user", {})
        u.pop("google_id", None)
        u.pop("google_name", None)
        u.pop("google_avatar", None)
        session["user"] = u
        flash("Google desvinculado.", "success")
    else:
        msg = data.get("message", "Erro.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("account.dashboard"))





@account_bp.post("/delete")
@login_required
def delete_account():
    """Exclui a conta permanentemente."""
    confirm = request.form.get("confirm", "").strip()
    if confirm != "EXCLUIR":
        flash("Digite EXCLUIR para confirmar a exclusão.", "danger")
        return redirect(url_for("account.dashboard"))

    from app.core.api import _headers, _url
    import requests as req
    resp = req.delete(
        _url("/auth/me"),
        headers=_headers(),
        json={"confirm": "EXCLUIR"},
        timeout=10,
    )
    try:
        data = resp.json() if resp.content else {}
    except Exception:
        data = {}

    if resp.status_code == 200 and data.get("success"):
        session.clear()
        flash("Sua conta foi excluída permanentemente.", "info")
        return redirect(url_for("index"))
    else:
        msg = data.get("message", "Erro ao excluir conta.") if data else "Erro de conexão."
        flash(msg, "danger")
        return redirect(url_for("account.dashboard"))


@account_bp.post("/delete-dj-profile")
@login_required
def delete_dj_profile():
    """Remove o perfil DJ mantendo a conta de usuário."""
    from app.core.api import _headers, _url
    import requests as req
    resp = req.delete(_url("/djs/me"), headers=_headers(), timeout=10)
    try:
        data = resp.json() if resp.content else {}
    except Exception:
        data = {}

    if resp.status_code == 200 and data.get("success"):
        u = session.get("user", {})
        u["is_dj"] = False
        session["user"] = u
        flash("Perfil de DJ excluído. Sua conta de usuário foi mantida.", "success")
    else:
        msg = data.get("message", "Erro ao excluir perfil DJ.")
        flash(msg, "danger")
    return redirect(url_for("account.dashboard"))
