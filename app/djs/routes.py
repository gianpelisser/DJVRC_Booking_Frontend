from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.core.api import api_get, api_post, api_put
from app.core.decorators import login_required, dj_required

djs_bp = Blueprint("djs", __name__)


@djs_bp.get("/")
def list_djs():
    params = {k: v for k, v in request.args.items() if v}
    params.setdefault("per_page", "16")

    data = api_get("/djs/", params=params)
    genres_data = api_get("/djs/genres")
    formats_data = api_get("/djs/presentation-formats")

    djs = data.get("data", {}).get("djs", []) if data else []
    pagination = data.get("data", {}) if data else {}
    genres = genres_data.get("data", []) if genres_data else []
    formats = formats_data.get("data", []) if formats_data else []

    return render_template("djs/list.html",
        djs=djs,
        pagination=pagination,
        genres=genres,
        formats=formats,
        filters=request.args,
    )


@djs_bp.get("/<int:dj_id>")
def profile(dj_id):
    data = api_get(f"/djs/{dj_id}")
    if not data:
        flash("DJ não encontrado.", "danger")
        return redirect(url_for("djs.list_djs"))
    dj = data.get("data", {})
    return render_template("djs/profile.html", dj=dj)


@djs_bp.get("/me/profile")
@dj_required
def my_profile():
    data = api_get("/djs/me")
    genres_data = api_get("/djs/genres")
    formats_data = api_get("/djs/presentation-formats")

    profile = data.get("data", {}) if data else {}
    genres = genres_data.get("data", []) if genres_data else []
    formats = formats_data.get("data", []) if formats_data else []

    return render_template("djs/edit_profile.html",
        profile=profile, genres=genres, formats=formats
    )


@djs_bp.post("/me/profile")
@dj_required
def my_profile_post():
    form = request.form

    genre_ids = [int(x) for x in form.getlist("genre_ids")]
    format_ids = [int(x) for x in form.getlist("presentation_format_ids")]
    languages = [l.strip() for l in form.get("languages", "").split(",") if l.strip()]

    payload = {
        "artist_name": form.get("artist_name"),
        "bio": form.get("bio"),
        "country": form.get("country"),
        "timezone": form.get("timezone"),
        "languages": languages,
        "discord_tag": form.get("discord_tag"),
        "twitch_url": form.get("twitch_url"),
        "youtube_url": form.get("youtube_url"),
        "vrchat_username": form.get("vrchat_username"),
        "website_url": form.get("website_url"),
        "experience_years": int(form.get("experience_years", 0) or 0),
        "equipment": form.get("equipment"),
        "event_experience": form.get("event_experience"),
        "hourly_rate": form.get("hourly_rate") or None,
        "event_rate": form.get("event_rate") or None,
        "minimum_rate": form.get("minimum_rate") or None,
        "currency": form.get("currency", "USD"),
        "negotiable": form.get("negotiable") == "on",
        "request_quote": form.get("request_quote") == "on",
        "genre_ids": genre_ids,
        "presentation_format_ids": format_ids,
    }

    # Cria ou atualiza
    existing = api_get("/djs/me")
    if existing and existing.get("data"):
        data, status = api_put("/djs/me", payload)
    else:
        data, status = api_post("/djs/", payload)

    if status in (200, 201) and data and data.get("success"):
        flash("Perfil atualizado com sucesso!", "success")
    else:
        msg = data.get("message", "Erro ao salvar perfil.") if data else "Erro de conexão."
        flash(msg, "danger")

    return redirect(url_for("djs.my_profile"))


@djs_bp.get("/me/availability")
@dj_required
def availability():
    return render_template("djs/availability.html")


@djs_bp.post("/me/availability")
@dj_required
def availability_post():
    entries = []
    weekdays = request.form.getlist("weekday[]")
    starts = request.form.getlist("start_time[]")
    ends = request.form.getlist("end_time[]")
    blocked = request.form.getlist("blocked_date[]")

    for i, wd in enumerate(weekdays):
        if wd:
            entries.append({
                "weekday": int(wd),
                "start_time": starts[i] if i < len(starts) else None,
                "end_time": ends[i] if i < len(ends) else None,
            })

    for bd in blocked:
        if bd:
            entries.append({"blocked_date": bd})

    data, status = api_post("/djs/me/availability", {"availability": entries})
    if status == 200 and data and data.get("success"):
        flash("Disponibilidade atualizada!", "success")
    else:
        flash("Erro ao atualizar disponibilidade.", "danger")

    return redirect(url_for("djs.availability"))
