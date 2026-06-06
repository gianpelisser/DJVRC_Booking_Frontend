from flask import Flask
from .core.config import config_by_name


def create_app(config_name: str = "development") -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(config_by_name[config_name])

    # Blueprints
    from .auth.routes import auth_bp
    from .djs.routes import djs_bp
    from .bookings.routes import bookings_bp
    from .events.routes import events_bp
    from .admin.routes import admin_bp

    app.register_blueprint(auth_bp,     url_prefix="/auth")
    app.register_blueprint(djs_bp,      url_prefix="/djs")
    app.register_blueprint(bookings_bp, url_prefix="/bookings")
    app.register_blueprint(events_bp,   url_prefix="/events")
    app.register_blueprint(admin_bp,    url_prefix="/admin")

    # Context processors e filtros globais
    from .core.context import register_context
    register_context(app)

    # Rota raiz
    from flask import render_template
    @app.route("/")
    def index():
        from .core.api import api_get
        djs_data = api_get("/djs/?per_page=8")
        djs = djs_data.get("data", {}).get("djs", []) if djs_data else []
        return render_template("index.html", djs=djs)

    return app
