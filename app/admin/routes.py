from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.core.api import api_get, api_post, api_put, api_delete
from app.core.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


# ─── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.get("/")
@admin_required
def dashboard():
    data = api_get("/admin/dashboard")
    stats = data.get("data", {}) if data and data.get("success") else {}
    return render_template("admin/dashboard.html", stats=stats)


# ─── Usuários ─────────────────────────────────────────────────────────────────

@admin_bp.get("/users")
@admin_required
def users():
    page    = request.args.get("page", 1, type=int)
    role    = request.args.get("role", "")
    search  = request.args.get("search", "").strip()
    params  = {"page": page, "per_page": 20}
    if role:
        params["role"] = role
    if search:
        params["search"] = search

    data = api_get("/admin/users", params=params)
    users_list, pagination = [], {}
    if data and data.get("success"):
        users_list = data["data"].get("users", [])
        pagination = data["data"]

    filters = {"role": role, "search": search}
    return render_template("admin/users.html",
        users=users_list, pagination=pagination, filters=filters)


@admin_bp.get("/users/<int:user_id>")
@admin_required
def user_detail(user_id):
    data = api_get(f"/admin/users/{user_id}")
    if not data or not data.get("success"):
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("admin.users"))
    return render_template("admin/user_detail.html", user=data["data"])


@admin_bp.post("/users/<int:user_id>/suspend")
@admin_required
def suspend_user(user_id):
    api_post(f"/admin/users/{user_id}/suspend")
    flash("Usuário suspenso.", "warning")
    return redirect(request.referrer or url_for("admin.users"))


@admin_bp.post("/users/<int:user_id>/activate")
@admin_required
def activate_user(user_id):
    api_post(f"/admin/users/{user_id}/activate")
    flash("Usuário ativado.", "success")
    return redirect(request.referrer or url_for("admin.users"))


# ─── DJs ──────────────────────────────────────────────────────────────────────

@admin_bp.get("/djs")
@admin_required
def djs():
    approved = request.args.get("approved")
    params = {"per_page": 50}
    if approved is not None:
        params["approved"] = approved
    data = api_get("/admin/djs", params=params)
    djs_list = data["data"].get("djs", []) if data and data.get("success") else []
    return render_template("admin/djs.html", djs=djs_list, approved_filter=approved)


@admin_bp.post("/djs/<int:dj_id>/approve")
@admin_required
def approve_dj(dj_id):
    api_post(f"/admin/djs/{dj_id}/approve")
    flash("DJ aprovado.", "success")
    return redirect(request.referrer or url_for("admin.djs"))


@admin_bp.post("/djs/<int:dj_id>/reject")
@admin_required
def reject_dj(dj_id):
    api_post(f"/admin/djs/{dj_id}/reject")
    flash("DJ rejeitado.", "warning")
    return redirect(request.referrer or url_for("admin.djs"))


# ─── DJs em Destaque ──────────────────────────────────────────────────────────

@admin_bp.get("/featured")
@admin_required
def featured():
    data = api_get("/admin/featured")
    djs  = data.get("data", []) if data and data.get("success") else []
    return render_template("admin/featured.html", djs=djs)


@admin_bp.post("/featured/<int:dj_id>/set")
@admin_required
def set_featured(dj_id):
    days = int(request.form.get("days", 30))
    data, status = api_post(f"/admin/featured/{dj_id}", {"days": days})
    if status == 200 and data and data.get("success"):
        flash("DJ em destaque atualizado!", "success")
    else:
        flash("Erro ao atualizar destaque.", "danger")
    return redirect(url_for("admin.featured"))


@admin_bp.post("/featured/<int:dj_id>/remove")
@admin_required
def remove_featured(dj_id):
    api_post(f"/admin/featured/{dj_id}", {"days": 0})
    flash("Destaque removido.", "success")
    return redirect(url_for("admin.featured"))


# ─── Audit Logs ───────────────────────────────────────────────────────────────
""" # Audit Logs removido (Inativado)
@admin_bp.get("/audit-logs")
@admin_required
def audit_logs():
    page = request.args.get("page", 1, type=int)
    data = api_get("/admin/audit-logs", params={"page": page, "per_page": 50})
    logs = []
    pagination = {}
    if data and data.get("success"):
        logs = data["data"].get("logs", [])
        pagination = data["data"]
    return render_template("admin/audit_logs.html", logs=logs, pagination=pagination)
"""


# ─── Configurações do Site ────────────────────────────────────────────────────

@admin_bp.get("/settings")
@admin_required
def settings():
    data = api_get("/admin/site-config")
    config = data.get("data", {}) if data and data.get("success") else {}
    return render_template("admin/settings.html", config=config)


@admin_bp.post("/settings")
@admin_required
def settings_save():
    form = request.form
    payload = {
        "register_email_enabled":   "1" if form.get("register_email_enabled") else "0",
        "register_discord_enabled": "1" if form.get("register_discord_enabled") else "0",
        "register_google_enabled":  "1" if form.get("register_google_enabled") else "0",
    }
    data, status = api_put("/admin/site-config", payload)
    if status == 200 and data and data.get("success"):
        flash("Configurações salvas!", "success")
    else:
        flash("Erro ao salvar configurações.", "danger")
    return redirect(url_for("admin.settings"))


# ─── Gêneros ──────────────────────────────────────────────────────────────────

@admin_bp.get("/genres")
@admin_required
def genres():
    data    = api_get("/djs/genres")
    genres  = data.get("data", []) if data and data.get("success") else []
    formats_data = api_get("/djs/presentation-formats")
    formats = formats_data.get("data", []) if formats_data and formats_data.get("success") else []
    return render_template("admin/genres.html", genres=genres, formats=formats)


@admin_bp.post("/genres/add")
@admin_required
def add_genre():
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
    if not slug and name:
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    data, status = api_post("/admin/genres", {"name": name, "slug": slug})
    if status in (200, 201) and data and data.get("success"):
        flash(f"Gênero '{name}' adicionado!", "success")
    else:
        msg = data.get("message", "Erro ao adicionar.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("admin.genres"))


@admin_bp.post("/genres/<int:genre_id>/delete")
@admin_required
def delete_genre(genre_id):
    api_delete(f"/admin/genres/{genre_id}")
    flash("Gênero removido.", "success")
    return redirect(url_for("admin.genres"))


# ─── Formatos de Apresentação ─────────────────────────────────────────────────

@admin_bp.post("/formats/add")
@admin_required
def add_format():
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower().replace(" ", "-")
    if not slug and name:
        import re
        slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    data, status = api_post("/admin/presentation-formats", {"name": name, "slug": slug})
    if status in (200, 201) and data and data.get("success"):
        flash(f"Formato '{name}' adicionado!", "success")
    else:
        msg = data.get("message", "Erro ao adicionar.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("admin.genres"))


@admin_bp.post("/formats/<int:fmt_id>/delete")
@admin_required
def delete_format(fmt_id):
    api_delete(f"/admin/presentation-formats/{fmt_id}")
    flash("Formato removido.", "success")
    return redirect(url_for("admin.genres"))
