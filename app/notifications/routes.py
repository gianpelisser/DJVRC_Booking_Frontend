from flask import Blueprint, render_template, redirect, url_for, request
from app.core.api import api_get, api_post
from app.core.decorators import login_required

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("/")
@login_required
def list_notifications():
    page   = request.args.get("page", 1, type=int)
    unread = request.args.get("unread", "")
    params = {"page": page, "per_page": 20}
    if unread:
        params["unread"] = "true"

    data = api_get("/notifications/", params=params)
    notifications = []
    pagination    = {}
    unread_count  = 0

    if data and data.get("success"):
        d             = data.get("data", {})
        notifications = d.get("notifications", [])
        unread_count  = d.get("unread_count", 0)
        pagination    = d

    return render_template("notifications/list.html",
        notifications=notifications,
        pagination=pagination,
        unread_count=unread_count,
        filter_unread=bool(unread),
    )


@notifications_bp.post("/<int:notif_id>/read")
@login_required
def mark_read(notif_id):
    api_post(f"/notifications/{notif_id}/read")
    return redirect(request.referrer or url_for("notifications.list_notifications"))


@notifications_bp.post("/<int:notif_id>/unread")
@login_required
def mark_unread(notif_id):
    api_post(f"/notifications/{notif_id}/unread")
    return redirect(request.referrer or url_for("notifications.list_notifications"))


@notifications_bp.post("/read-all")
@login_required
def read_all():
    api_post("/notifications/read-all")
    return redirect(url_for("notifications.list_notifications"))


@notifications_bp.post("/<int:notif_id>/delete")
@login_required
def delete_notification(notif_id):
    from app.core.api import _headers, _url
    import requests as req
    req.delete(_url(f"/notifications/{notif_id}"), headers=_headers(), timeout=10)
    return redirect(request.referrer or url_for("notifications.list_notifications"))


@notifications_bp.post("/delete-all")
@login_required
def delete_all():
    from app.core.api import _headers, _url
    import requests as req
    req.delete(_url("/notifications/delete-all"), headers=_headers(), timeout=10)
    return redirect(url_for("notifications.list_notifications"))
