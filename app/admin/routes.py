from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.core.api import api_get, api_post, api_delete
from app.core.decorators import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.get("/")
@admin_required
def dashboard():
    data = api_get("/admin/dashboard")
    stats = data.get("data", {}) if data else {}
    return render_template("admin/dashboard.html", stats=stats)


@admin_bp.get("/users")
@admin_required
def users():
    params = {k: v for k, v in request.args.items() if v}
    params.setdefault("per_page", "30")
    data = api_get("/admin/users", params=params)
    users_list = data.get("data", {}).get("users", []) if data else []
    pagination = data.get("data", {}) if data else {}
    return render_template("admin/users.html",
        users=users_list, pagination=pagination, filters=request.args
    )


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


@admin_bp.get("/djs")
@admin_required
def djs():
    approved = request.args.get("approved", "")
    params = {"per_page": "30"}
    if approved != "":
        params["approved"] = approved
    data = api_get("/admin/djs", params=params)
    djs_list = data.get("data", {}).get("djs", []) if data else []
    pagination = data.get("data", {}) if data else {}
    return render_template("admin/djs.html",
        djs=djs_list, pagination=pagination, approved_filter=approved
    )


@admin_bp.post("/djs/<int:dj_id>/approve")
@admin_required
def approve_dj(dj_id):
    api_post(f"/admin/djs/{dj_id}/approve")
    flash("DJ aprovado!", "success")
    return redirect(url_for("admin.djs", approved="false"))


@admin_bp.post("/djs/<int:dj_id>/reject")
@admin_required
def reject_dj(dj_id):
    api_post(f"/admin/djs/{dj_id}/reject")
    flash("DJ rejeitado.", "warning")
    return redirect(url_for("admin.djs", approved="false"))


@admin_bp.get("/audit-logs")
@admin_required
def audit_logs():
    params = {"per_page": "50", "page": request.args.get("page", "1")}
    data = api_get("/admin/audit-logs", params=params)
    logs = data.get("data", {}).get("logs", []) if data else []
    pagination = data.get("data", {}) if data else {}
    return render_template("admin/audit_logs.html", logs=logs, pagination=pagination)
