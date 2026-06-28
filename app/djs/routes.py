import logging
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.core.api import api_get, api_post, api_put
from app.core.decorators import login_required, dj_required

log = logging.getLogger("djvrc.djs")
djs_bp = Blueprint("djs", __name__)


@djs_bp.get("/")
def list_djs():
    params = {k: v for k, v in request.args.items() if v}
    params.setdefault("per_page", "16")
    data         = api_get("/djs/", params=params)
    genres_data  = api_get("/djs/genres")
    formats_data = api_get("/djs/presentation-formats")
    djs        = data.get("data", {}).get("djs", []) if data else []
    pagination = data.get("data", {}) if data else {}
    genres     = genres_data.get("data", []) if genres_data else []
    formats    = formats_data.get("data", []) if formats_data else []
    return render_template("djs/list.html",
        djs=djs, pagination=pagination,
        genres=genres, formats=formats, filters=request.args,
    )


@djs_bp.get("/<int:dj_id>")
def profile(dj_id):
    data = api_get(f"/djs/{dj_id}")
    if not data or not data.get("success"):
        me_data = api_get("/djs/me")
        if me_data and me_data.get("success"):
            dj = me_data.get("data", {})
            if dj.get("id") == dj_id:
                agenda_data = api_get(f"/djs/{dj_id}/agenda")
                agenda = agenda_data.get("data", []) if agenda_data and agenda_data.get("success") else []
                return render_template("djs/profile.html", dj=dj, is_owner=True,
                                       pending=not dj.get("is_approved"), agenda=agenda,
                                       is_logged_in=bool(session.get("access_token")),
                                       current_user=session.get("user"))
        flash("DJ nao encontrado.", "danger")
        return redirect(url_for("djs.list_djs"))

    dj = data.get("data", {})
    agenda_data = api_get(f"/djs/{dj_id}/agenda")
    agenda = agenda_data.get("data", []) if agenda_data and agenda_data.get("success") else []
    return render_template("djs/profile.html", dj=dj, is_owner=False, agenda=agenda,
                           is_logged_in=bool(session.get("access_token")),
                           current_user=session.get("user"))


@djs_bp.get("/<int:dj_id>/agenda")
def dj_agenda(dj_id):
    """Página de agenda completa do DJ."""
    dj_data = api_get(f"/djs/{dj_id}")
    if not dj_data or not dj_data.get("success"):
        flash("DJ não encontrado.", "danger")
        return redirect(url_for("djs.list_djs"))
    dj = dj_data["data"]
    agenda_data = api_get(f"/djs/{dj_id}/agenda")
    agenda = agenda_data.get("data", []) if agenda_data and agenda_data.get("success") else []
    return render_template("djs/agenda.html", dj=dj, agenda=agenda)


@djs_bp.get("/me/public")
@dj_required
def view_my_public_profile():
    """Redireciona o DJ para seu proprio perfil publico (aprovado ou nao)."""
    data = api_get("/djs/me")
    if not data or not data.get("success"):
        flash("Crie seu perfil DJ primeiro.", "warning")
        return redirect(url_for("djs.my_profile"))
    dj_id = data.get("data", {}).get("id")
    if not dj_id:
        flash("Perfil DJ não encontrado.", "warning")
        return redirect(url_for("djs.my_profile"))
    return redirect(url_for("djs.profile", dj_id=dj_id))


@djs_bp.get("/me/profile")
@dj_required
def my_profile():
    data         = api_get("/djs/me")
    genres_data  = api_get("/djs/genres")
    formats_data = api_get("/djs/presentation-formats")
    profile  = data.get("data", {}) if (data and data.get("success")) else {}
    genres   = genres_data.get("data", []) if genres_data else []
    formats  = formats_data.get("data", []) if formats_data else []
    # Pré-preenche discord_tag com dados do usuário se perfil novo
    user = session.get("user", {})
    if not profile.get("social", {}).get("discord") and user.get("discord_username"):
        if not profile.get("social"):
            profile["social"] = {}
        profile["social"]["discord"] = user.get("discord_display_name") or user.get("discord_username")

    return render_template("djs/edit_profile.html",
        profile=profile, genres=genres, formats=formats,
    )


@djs_bp.post("/me/profile")
@dj_required
def my_profile_post():
    form = request.form
    genre_ids  = [int(x) for x in form.getlist("genre_ids") if x.isdigit()]
    format_ids = [int(x) for x in form.getlist("presentation_format_ids") if x.isdigit()]
    languages  = [l for l in form.getlist("languages") if l]

    payload = {
        "artist_name":             form.get("artist_name", "").strip(),
        "real_name":               form.get("real_name", "").strip() or None,
        "bio":                     form.get("bio", "").strip() or None,
        "country":                 form.get("country", "").strip() or None,
        "timezone":                form.get("timezone", "").strip() or None,
        "languages":               languages,
        "discord_tag":             form.get("discord_tag", "").strip() or None,
        "twitch_url":              form.get("twitch_url", "").strip() or None,
        "youtube_url":             form.get("youtube_url", "").strip() or None,
        "vrchat_username":         form.get("vrchat_username", "").strip() or None,
        "website_url":             form.get("website_url", "").strip() or None,
        "experience_years":        int(form.get("experience_years", 0) or 0),
        "equipment":               form.get("equipment", "").strip() or None,
        "event_experience":        form.get("event_experience", "").strip() or None,
        "hourly_rate":             form.get("hourly_rate") or None,
        "event_rate":              form.get("event_rate") or None,
        "minimum_rate":            form.get("minimum_rate") or None,
        "currency":                form.get("currency", "USD"),
        "negotiable":              form.get("negotiable") == "on",
        "request_quote":           form.get("request_quote") == "on",
        "avatar_url":              form.get("avatar_url", "").strip() or None,
        "banner_url":              form.get("banner_url", "").strip() or None,
        "logo_url":                form.get("logo_url", "").strip() or None,
        "genre_ids":               genre_ids,
        "presentation_format_ids": format_ids,
    }

    # Se usuário tem Discord vinculado, usar dados reais em vez do campo manual
    user = session.get("user", {})
    if user.get("discord_username"):
        payload["discord_tag"] = user["discord_username"]

    if not payload["artist_name"]:
        flash("Nome artistico é obrigatorio.", "danger")
        return redirect(url_for("djs.my_profile"))

    existing = api_get("/djs/me")
    has_profile = existing and existing.get("success") and existing.get("data")

    if has_profile:
        data, status = api_put("/djs/me", payload)
    else:
        data, status = api_post("/djs/", payload)

    if status in (200, 201) and data and data.get("success"):
        flash("Perfil salvo com sucesso!", "success")
    else:
        msg = data.get("message", "Erro ao salvar perfil.") if data else "Erro de conexao."
        flash(msg, "danger")

    return redirect(url_for("djs.my_profile"))


@djs_bp.get("/me/availability")
@dj_required
def availability():
    # Carrega disponibilidade salva para preencher a tela
    data = api_get("/djs/me")
    avail = []
    if data and data.get("success"):
        avail = data.get("data", {}).get("availability", [])
    return render_template("djs/availability.html", availability=avail)


@djs_bp.post("/me/availability")
@dj_required
def availability_post():
    entries  = []
    weekdays = request.form.getlist("weekday[]")
    starts   = request.form.getlist("start_time[]")
    ends     = request.form.getlist("end_time[]")
    blocked  = request.form.getlist("blocked_date[]")

    for i, wd in enumerate(weekdays):
        if wd:
            entries.append({
                "weekday":    int(wd),
                "start_time": starts[i] if i < len(starts) else None,
                "end_time":   ends[i]   if i < len(ends)   else None,
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


# ─── Minha Agenda (DJ logado) ─────────────────────────────────────────────────

@djs_bp.get("/me/agenda")
@dj_required
def my_agenda():
    """Página de gerenciamento da agenda do DJ."""
    data = api_get("/djs/me/agenda")
    agenda = data.get("data", []) if data and data.get("success") else []
    # Busca o id do perfil para link para agenda pública
    profile_data = api_get("/djs/me")
    dj_id = profile_data["data"]["id"] if profile_data and profile_data.get("success") else None
    return render_template("djs/my_agenda.html", agenda=agenda, dj_id=dj_id)


@djs_bp.post("/me/agenda")
@dj_required
def add_agenda_entry():
    form = request.form
    payload = {
        "event_name":       form.get("event_name", "").strip(),
        "event_date":       form.get("event_date", ""),
        "event_time":       form.get("event_time", ""),
        "duration_minutes": int(form.get("duration_minutes", 60) or 60),
        "platform":         form.get("platform", "").strip() or None,
        "description":      form.get("description", "").strip() or None,
        "is_private":       bool(form.get("is_private")),
    }
    data, status = api_post("/djs/me/agenda", payload)
    if status in (200, 201) and data and data.get("success"):
        flash("Evento adicionado à agenda!", "success")
    else:
        msg = data.get("message", "Erro ao adicionar.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("djs.my_agenda"))


@djs_bp.post("/me/agenda/<int:entry_id>/delete")
@dj_required
def delete_agenda_entry(entry_id):
    from app.core.api import api_delete
    data, status = api_delete(f"/djs/me/agenda/{entry_id}")
    if status == 200:
        flash("Evento removido.", "success")
    else:
        msg = data.get("message", "Erro ao remover.") if data else "Erro de conexão."
        flash(msg, "danger")
    return redirect(url_for("djs.my_agenda"))


@djs_bp.post("/me/agenda/<int:entry_id>/toggle-private")
@dj_required
def toggle_agenda_privacy(entry_id):
    from app.core.api import api_put
    # Busca estado atual e inverte
    data = api_get("/djs/me/agenda")
    entries = data.get("data", []) if data and data.get("success") else []
    entry = next((e for e in entries if e["id"] == entry_id), None)
    is_private = not entry.get("is_private", False) if entry else True
    api_put(f"/djs/me/agenda/{entry_id}", {"is_private": is_private})
    flash("Visibilidade alterada.", "success")
    return redirect(url_for("djs.my_agenda"))
