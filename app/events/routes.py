from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.core.api import api_get, api_put
from app.core.decorators import login_required

events_bp = Blueprint("events", __name__)


@events_bp.get("/")
@login_required
def list_events():
    status_filter = request.args.get("status", "")
    params = {"per_page": 20}
    if status_filter:
        params["status"] = status_filter

    data = api_get("/events/", params=params)
    events = data.get("data", {}).get("events", []) if data else []
    pagination = data.get("data", {}) if data else {}

    return render_template("events/list.html",
        events=events, pagination=pagination, status_filter=status_filter
    )


@events_bp.get("/<int:event_id>")
@login_required
def detail(event_id):
    data = api_get(f"/events/{event_id}")
    if not data:
        flash("Evento não encontrado.", "danger")
        return redirect(url_for("events.list_events"))
    return render_template("events/detail.html", event=data.get("data", {}))


@events_bp.post("/<int:event_id>/update-status")
@login_required
def update_status(event_id):
    status = request.form.get("status")
    stream_url = request.form.get("stream_url", "")
    payload = {"status": status}
    if stream_url:
        payload["stream_url"] = stream_url

    data, code = api_put(f"/events/{event_id}", payload)
    if code == 200 and data and data.get("success"):
        flash("Evento atualizado.", "success")
    else:
        flash("Erro ao atualizar evento.", "danger")
    return redirect(url_for("events.detail", event_id=event_id))
