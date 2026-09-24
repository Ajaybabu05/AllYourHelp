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

    # Import User model
    from .models.user import User
    from .models.service_category import ServiceCategory
    from .models.service import Service
    from .models.professional_profile import ProfessionalProfile
    from .models.service_request import ServiceRequest

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))


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


    return app