from flask import Flask, render_template

from .config import Config
from .extensions import db, migrate, login_manager, mail


def create_app():

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # --------------------------------------------------
    # Basic security headers
    # --------------------------------------------------

    @app.after_request
    def add_security_headers(response):

        response.headers.setdefault(
            "X-Content-Type-Options",
            "nosniff"
        )

        response.headers.setdefault(
            "X-Frame-Options",
            "SAMEORIGIN"
        )

        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin"
        )

        response.headers.setdefault(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()"
        )

        # HSTS should only be sent when the application is
        # actually served over HTTPS.
        if (
            app.config.get("APP_ENV") == "production"
            and app.config.get("SESSION_COOKIE_SECURE")
        ):
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains"
            )

        return response

    # Import User model
    from .models.user import User
    from .models.service_category import ServiceCategory
    from .models.service import Service
    from .models.professional_profile import ProfessionalProfile
    from .models.service_request import ServiceRequest

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    # Import and register authentication blueprint
    from .routes.auth import auth
    app.register_blueprint(auth)

    # Import and register dashboard blueprint
    from .routes.dashboard import dashboard
    app.register_blueprint(dashboard)

    from .routes.services import services
    app.register_blueprint(services)

    from .routes.admin import admin
    app.register_blueprint(admin)

    # Home route
    @app.route("/")
    def home():
        return render_template("home.html")

    # Custom error pages
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app
