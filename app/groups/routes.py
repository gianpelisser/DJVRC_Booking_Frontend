from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.core.api import api_get, api_post, api_put, api_delete
from app.core.decorators import login_required

groups_bp = Blueprint("groups", __name__)


@groups_bp.get("/")
@login_required
def list_groups():
    data = api_get("/groups/")
    groups = data.get("data", []) if data and data.get("success") else []
    return render_template("groups/list.html", groups=groups)


@groups_bp.post("/")
@login_required
def create_group():
    form = request.form
    payload = {
        "name":        form.get("name", "").strip(),
        "description": form.get("description", "").strip() or None,
        "discord_url": form.get("discord_url", "").strip() or None,
        "vrchat_url":  form.get("vrchat_url", "").strip() or None,
        "website_url": form.get("website_url", "").strip() or None,
    }
    data, status = api_post("/groups/", payload)
    if status in (200, 201) and data and data.get("success"):
        flash("Grupo criado!", "success")
    else:
        msg = data.get("message", "Erro ao criar grupo.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("groups.list_groups"))


@groups_bp.post("/<int:group_id>/update")
@login_required
def update_group(group_id):
    form = request.form
    payload = {
        "name":        form.get("name", "").strip(),
        "description": form.get("description", "").strip() or None,
        "discord_url": form.get("discord_url", "").strip() or None,
        "vrchat_url":  form.get("vrchat_url", "").strip() or None,
        "website_url": form.get("website_url", "").strip() or None,
    }
    data, status = api_put(f"/groups/{group_id}", payload)
    if status == 200 and data and data.get("success"):
        flash("Grupo atualizado!", "success")
    else:
        msg = data.get("message", "Erro ao atualizar.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("groups.list_groups"))


@groups_bp.post("/<int:group_id>/delete")
@login_required
def delete_group(group_id):
    data, status = api_delete(f"/groups/{group_id}")
    if status == 200 and data and data.get("success"):
        flash("Grupo removido.", "success")
    else:
        msg = data.get("message", "Erro ao remover grupo.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("groups.list_groups"))
