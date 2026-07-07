from flask import session


def register_context(app):

    @app.context_processor
    def inject_user():
        """Injeta o usuário logado e contagem de notificações em todos os templates."""
        unread_count = 0
        if session.get("access_token"):
            try:
                from app.core.api import api_get
                data = api_get("/notifications/", params={"per_page": 1})
                if data and data.get("success"):
                    unread_count = data.get("data", {}).get("unread_count", 0)
            except Exception:
                pass
        return {
            "current_user":      session.get("user"),
            "is_logged_in":      bool(session.get("access_token")),
            "unread_notif_count": unread_count,
        }

    @app.template_filter("currency")
    def currency_filter(value, symbol="$"):
        if value is None:
            return "—"
        try:
            return f"{symbol}{float(value):.2f}"
        except (ValueError, TypeError):
            return value

    @app.template_filter("duracao")
    def duracao_filter(minutos):
        """Converte minutos para formato legível: 90 → 1h 30min, 60 → 1 hora, 45 → 45 min"""
        if not minutos:
            return "—"
        try:
            m = int(minutos)
        except (ValueError, TypeError):
            return str(minutos)
        h = m // 60
        rest = m % 60
        if h == 0:
            return f"{rest} min"
        elif rest == 0:
            return f"{h} hora" if h == 1 else f"{h} horas"
        else:
            return f"{h}h {rest}min"

    @app.template_filter("lang_name")
    def lang_name_filter(code):
        """Converte código de idioma (pt-BR, en-US) para nome amigável."""
        LANGS = {
            "pt":    "Português",
            "pt-BR": "Português (Brasil)",
            "pt-PT": "Português (Portugal)",
            "en":    "Inglês",
            "en-US": "Inglês",
            "en-GB": "Inglês (Reino Unido)",
            "es":    "Espanhol",
            "es-ES": "Espanhol",
            "es-419":"Espanhol (América Latina)",
            "fr":    "Francês",
            "de":    "Alemão",
            "it":    "Italiano",
            "ja":    "Japonês",
            "ko":    "Coreano",
            "zh":    "Chinês",
            "zh-CN": "Chinês (Simplificado)",
            "zh-TW": "Chinês (Tradicional)",
            "ru":    "Russo",
            "ar":    "Árabe",
            "hi":    "Hindi",
            "nl":    "Holandês",
            "pl":    "Polonês",
            "tr":    "Turco",
            "sv":    "Sueco",
            "no":    "Norueguês",
            "da":    "Dinamarquês",
            "fi":    "Finlandês",
        }
        if not code:
            return ""
        return LANGS.get(str(code).strip(), str(code).strip())

    @app.template_filter("date_br")
    def date_br_filter(value):
        """Converte 2025-12-31 → 31/12/2025."""
        if not value:
            return "—"
        try:
            parts = str(value).split("-")
            return f"{parts[2]}/{parts[1]}/{parts[0]}"
        except Exception:
            return value

    @app.template_filter("truncate_bio")
    def truncate_bio(value, length=120):
        if not value:
            return ""
        return value[:length] + "..." if len(value) > length else value

    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500
