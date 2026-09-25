from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from ..models.professional_profile import ProfessionalProfile
from ..models.notification import Notification
from ..utils.email import send_email
from flask import current_app
from ..extensions import db, limiter
from ..models.user import User
from datetime import datetime


auth = Blueprint("auth", __name__, url_prefix="/auth")

def generate_verification_token(user):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    return serializer.dumps(
        user.email,
        salt="email-verification"
    )


def verify_email_token(token, max_age=86400):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    try:
        email = serializer.loads(
            token,
            salt="email-verification",
            max_age=max_age
        )

    except (SignatureExpired, BadSignature):
        return None

    return User.query.filter_by(
        email=email
    ).first()


@auth.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour", methods=["POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        role = request.form.get("role", "user")

        # Validate required fields
        if not name or not email or not password:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("auth.register"))

        # Check password confirmation
        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for("auth.register"))

        # Password length
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("auth.register"))

        # Validate role
        if role not in ["user", "professional"]:
            flash("Invalid account type.", "error")
            return redirect(url_for("auth.register"))

        # Check whether email already exists
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("An account with this email already exists.", "error")
            return redirect(url_for("auth.register"))

        # Create new user
        user = User(
            name=name,
            email=email,
            phone=phone,
            role=role
        )

        # Hash password
        user.set_password(password)

        # Save user
        db.session.add(user)
        db.session.flush()

        # Only professionals need a professional profile
        # and admin notification
        if role == "professional":

            professional_profile = ProfessionalProfile(
                user_id=user.id,
                bio=None,
                experience=None,
                location=None,
                is_verified=False
            )

            db.session.add(professional_profile)

            # Notify all admins
            admins = User.query.filter_by(
                role="admin"
            ).all()

            for admin in admins:

                notification = Notification(
                    user_id=admin.id,
                    title="New Professional Registration",
                    message=(
                        f"{user.name} has registered as a new professional."
                    ),
                    notification_type="new_professional_registration",
                    professional_user_id=user.id
                )

                db.session.add(notification)

                # Send email to admin
                if admin.email:

                    send_email(
                        recipient=admin.email,
                        subject="AllYourHelp - New Professional Registration",
                        body=(
                            f"Hello {admin.name},\n\n"
                            f"{user.name} has registered as a new professional "
                            "on AllYourHelp.\n\n"
                            "You can log in to your AllYourHelp admin account "
                            "to review the professional account.\n\n"
                            "Regards,\n"
                            "AllYourHelp Team"
                        )
                    )

        db.session.commit()

        # Generate email verification token
        serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"]
        )

        verification_token = serializer.dumps(
            user.email,
            salt="email-verification"
        )

        verification_link = url_for(
            "auth.verify_email",
            token=verification_token,
            _external=True
        )

        send_email(
            recipient=user.email,
            subject="AllYourHelp - Verify Your Email",
            body=(
                f"Hello {user.name},\n\n"

                "Welcome to AllYourHelp!\n\n"

                "Please verify your email address by clicking "
                "the link below:\n\n"

                f"{verification_link}\n\n"

                "This verification link will expire in 24 hours.\n\n"

                "If you did not create this account, "
                "you can safely ignore this email.\n\n"

                "Regards,\n"
                "AllYourHelp Team"
            )
        )
        if role == "professional":
            if user.email:
                send_email(
                    recipient=user.email,
                    subject="Welcome to AllYourHelp - Professional Account",
                    body=(
                        f"Hello {user.name},\n\n"
                        "Welcome to AllYourHelp!\n\n"
                        "Your professional account has been created "
                        "successfully. Your professional profile is currently "
                        "waiting for verification.\n\n"
                        "Regards,\n"
                        "AllYourHelp Team"
                    )
                )

        # Registration message
        flash(
            "Registration successful! Please check your email to verify your account.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth.route("/verify-email/<token>")
def verify_email(token):

    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    try:
        email = serializer.loads(
            token,
            salt="email-verification",
            max_age=86400
        )
    except Exception:
        flash(
            "This verification link is invalid or has expired.",
            "error"
        )
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()

    if not user:
        flash(
            "The account associated with this verification link was not found.",
            "error"
        )
        return redirect(url_for("auth.login"))

    if user.email_verified:
        flash(
            "Your email is already verified. You can log in.",
            "info"
        )
        return redirect(url_for("auth.login"))

    user.email_verified = True
    user.email_verified_at = datetime.utcnow()

    db.session.commit()

    flash(
        "Your email has been verified successfully. You can now log in.",
        "success"
    )

    return redirect(url_for("auth.login"))

@auth.route("/resend-verification", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def resend_verification():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()

        if not email:
            flash(
                "Please enter your email address.",
                "error"
            )
            return redirect(url_for("auth.resend_verification"))

        user = User.query.filter_by(email=email).first()

        # Do not reveal whether an account exists
        if not user:
            flash(
                "If an account exists with this email, "
                "a verification email has been sent.",
                "info"
            )
            return redirect(url_for("auth.login"))

        # Already verified
        if user.email_verified:
            flash(
                "Your email is already verified. You can log in.",
                "info"
            )
            return redirect(url_for("auth.login"))

        # Generate a new verification token
        serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"]
        )

        verification_token = serializer.dumps(
            user.email,
            salt="email-verification"
        )

        verification_link = url_for(
            "auth.verify_email",
            token=verification_token,
            _external=True
        )

        # Send verification email
        if user.email:
            send_email(
                recipient=user.email,
                subject="Verify your AllYourHelp email",
                body=(
                    f"Hello {user.name},\n\n"
                    "You requested a new email verification link "
                    "for your AllYourHelp account.\n\n"
                    "Please verify your email address by clicking "
                    "the link below:\n\n"
                    f"{verification_link}\n\n"
                    "This verification link will expire in 24 hours.\n\n"
                    "If you did not request this email, you can "
                    "safely ignore it.\n\n"
                    "Regards,\n"
                    "AllYourHelp Team"
                )
            )

        flash(
            "A new verification email has been sent. "
            "Please check your inbox.",
            "success"
        )

        return redirect(url_for("auth.login"))

    return render_template("auth/resend_verification.html")

@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            if not user.is_active:

                flash(
                    "Your account has been deactivated.",
                    "error"
                )

                return redirect(
                    url_for("auth.login")
                )

            if not user.email_verified:
                flash(
                    "Please verify your email address before logging in.",
                    "error"
                )

                return render_template(
                    "auth/login.html",
                    verification_required=True,
                    verification_email=user.email
                )

            login_user(user)

            flash(
                "Login successful!",
                "success"
            )

    # Keep your existing role-based redirect here

            if user.role == "admin":
                return redirect(url_for("admin.dashboard"))

            return redirect(
                url_for("dashboard.user_dashboard")
            )

        flash("Invalid email or password.", "error")

    return render_template("auth/login.html")

@auth.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not email:

            flash(
                "Please enter your email address.",
                "error"
            )

            return redirect(
                url_for("auth.forgot_password")
            )

        user = User.query.filter_by(
            email=email
        ).first()

        # Always show the same message whether
        # the account exists or not.
        if user:

            token = generate_reset_token(user)

            reset_url = url_for(
                "auth.reset_password",
                token=token,
                _external=True
            )

            send_email(
                recipient=user.email,
                subject="AllYourHelp - Password Reset",
                body=(
                    f"Hello {user.name},\n\n"

                    "We received a request to reset "
                    "your AllYourHelp password.\n\n"

                    "Click the link below to create "
                    "a new password:\n\n"

                    f"{reset_url}\n\n"

                    "This link will expire in 1 hour.\n\n"

                    "If you did not request a password reset, "
                    "you can safely ignore this email.\n\n"

                    "Regards,\n"
                    "AllYourHelp Team"
                )
            )

        flash(
            "If an account exists with that email, "
            "a password reset link has been sent.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/forgot_password.html"
    )

@auth.route("/reset-password/<token>", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def reset_password(token):

    user = verify_reset_token(token)

    if not user:

        flash(
            "This password reset link is invalid or has expired.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "POST":

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if not password:

            flash(
                "Please enter a new password.",
                "error"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        if len(password) < 8:

            flash(
                "Password must be at least 8 characters long.",
                "error"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        if user.check_password(password):

            flash(
                "Your new password must be different "
                "from your current password.",
                "error"
            )

            return redirect(
                url_for(
                    "auth.reset_password",
                    token=token
                )
            )

        user.set_password(password)

        db.session.commit()

        flash(
            "Your password has been reset successfully. "
            "You can now log in.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/reset_password.html",
        token=token
    )


@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash("You have been logged out.", "success")

    return redirect(url_for("home"))
def generate_reset_token(user):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    return serializer.dumps(
        user.email,
        salt="password-reset"
    )


def verify_reset_token(token, max_age=3600):
    serializer = URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"]
    )

    try:
        email = serializer.loads(
            token,
            salt="password-reset",
            max_age=max_age
        )

    except (SignatureExpired, BadSignature):
        return None

    return User.query.filter_by(email=email).first()