from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.core.api import api_get, api_post
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
    page = request.args.get("page", 1, type=int)
    data = api_get("/admin/users", params={"page": page, "per_page": 20})
    users_list = []
    pagination = {}
    if data and data.get("success"):
        users_list = data["data"].get("users", [])
        pagination = data["data"]
    return render_template("admin/users.html", users=users_list, pagination=pagination)


@admin_bp.post("/users/<int:user_id>/suspend")
@admin_required
def suspend_user(user_id):
    api_post(f"/admin/users/{user_id}/suspend")
    flash("Usuário suspenso.", "warning")
    return redirect(url_for("admin.users"))


@admin_bp.post("/users/<int:user_id>/activate")
@admin_required
def activate_user(user_id):
    api_post(f"/admin/users/{user_id}/activate")
    flash("Usuário ativado.", "success")
    return redirect(url_for("admin.users"))


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
