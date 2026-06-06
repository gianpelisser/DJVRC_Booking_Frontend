from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.core.api import api_get, api_post
from app.core.decorators import login_required

bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.get("/")
@login_required
def list_bookings():
    status_filter = request.args.get("status", "")
    params = {"per_page": 20}
    if status_filter:
        params["status"] = status_filter

    data = api_get("/bookings/", params=params)
    bookings = data.get("data", {}).get("bookings", []) if data else []
    pagination = data.get("data", {}) if data else {}

    return render_template("bookings/list.html",
        bookings=bookings,
        pagination=pagination,
        status_filter=status_filter,
    )


@bookings_bp.get("/<int:booking_id>")
@login_required
def detail(booking_id):
    data = api_get(f"/bookings/{booking_id}")
    if not data:
        flash("Booking não encontrado.", "danger")
        return redirect(url_for("bookings.list_bookings"))
    return render_template("bookings/detail.html", booking=data.get("data", {}))


@bookings_bp.get("/new/<int:dj_id>")
@login_required
def new_booking(dj_id):
    user = session.get("user", {})
    if user.get("role") == "dj":
        flash("DJs não podem contratar outros DJs.", "warning")
        return redirect(url_for("djs.profile", dj_id=dj_id))

    dj_data = api_get(f"/djs/{dj_id}")
    if not dj_data:
        flash("DJ não encontrado.", "danger")
        return redirect(url_for("djs.list_djs"))

    return render_template("bookings/new.html", dj=dj_data.get("data", {}))


@bookings_bp.post("/new/<int:dj_id>")
@login_required
def new_booking_post(dj_id):
    form = request.form
    payload = {
        "dj_profile_id": dj_id,
        "event_name": form.get("event_name"),
        "event_date": form.get("event_date"),
        "event_time": form.get("event_time"),
        "duration_minutes": int(form.get("duration_minutes", 60) or 60),
        "platform": form.get("platform"),
        "offered_value": form.get("offered_value") or None,
        "currency": form.get("currency", "USD"),
        "description": form.get("description"),
    }

    data, status = api_post("/bookings/", payload)
    if status == 201 and data and data.get("success"):
        flash("Proposta enviada! O DJ será notificado pelo Discord.", "success")
        return redirect(url_for("bookings.list_bookings"))

    msg = data.get("message", "Erro ao enviar proposta.") if data else "Erro de conexão."
    flash(msg, "danger")

    dj_data = api_get(f"/djs/{dj_id}")
    return render_template("bookings/new.html", dj=dj_data.get("data", {}) if dj_data else {})


@bookings_bp.post("/<int:booking_id>/accept")
@login_required
def accept(booking_id):
    data, status = api_post(f"/bookings/{booking_id}/accept")
    if status == 200 and data and data.get("success"):
        flash("Proposta aceita! O evento foi criado.", "success")
    else:
        msg = data.get("message", "Erro ao aceitar.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("bookings.detail", booking_id=booking_id))


@bookings_bp.post("/<int:booking_id>/decline")
@login_required
def decline(booking_id):
    notes = request.form.get("notes", "")
    data, status = api_post(f"/bookings/{booking_id}/decline", {"notes": notes})
    if status == 200 and data and data.get("success"):
        flash("Proposta recusada.", "info")
    else:
        msg = data.get("message", "Erro ao recusar.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("bookings.list_bookings"))


@bookings_bp.post("/<int:booking_id>/cancel")
@login_required
def cancel(booking_id):
    data, status = api_post(f"/bookings/{booking_id}/cancel")
    if status == 200 and data and data.get("success"):
        flash("Booking cancelado.", "info")
    else:
        msg = data.get("message", "Erro ao cancelar.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("bookings.list_bookings"))
