from flask import Flask, render_template, request
from flask_wtf.csrf import generate_csrf

from .config import Config
from .extensions import db, migrate, login_manager, mail, csrf


def create_app():

    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize database and other extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # --------------------------------------------------
    # CSRF protection
    #
    # Existing AllYourHelp forms are protected using a
    # signed CSRF token stored in a secure cookie and
    # supplied to Flask-WTF through the request header.
    # This lets us protect the existing forms without
    # changing their business logic.
    # --------------------------------------------------

    @app.before_request
    def add_csrf_header_from_cookie():

        if request.method in {"POST", "PUT", "PATCH", "DELETE"}:

            csrf_cookie = request.cookies.get(
                "XSRF-TOKEN"
            )

            if csrf_cookie and not request.headers.get(
                "X-CSRFToken"
            ):

                request.environ[
                    "HTTP_X_CSRFTOKEN"
                ] = csrf_cookie

    csrf.init_app(app)

    @app.after_request
    def add_csrf_cookie(response):

        # Generate a token for pages that create a session
        # and expose it as a signed, HttpOnly cookie.
        token = generate_csrf()

        response.set_cookie(
            "XSRF-TOKEN",
            token,
            max_age=app.config["PERMANENT_SESSION_LIFETIME"].total_seconds(),
            secure=app.config.get(
                "SESSION_COOKIE_SECURE",
                False
            ),
            httponly=True,
            samesite="Lax"
        )

        return response

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
            return db.session.get(
                User,
                int(user_id)
            )

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
