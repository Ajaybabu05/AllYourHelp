from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    abort,
    request,
    flash,
    session,
    current_app
)
from flask_login import login_required, current_user
from datetime import datetime, date
from ..models.service import Service
from ..extensions import db
from ..models.service_category import ServiceCategory
from ..models.professional_profile import ProfessionalProfile
from ..models.service_request import ServiceRequest
from ..models.availability_slot import AvailabilitySlot
from ..models.review import Review
from ..models.user import User
from ..models.professional_service_request import ProfessionalServiceRequest
from ..models.notification_preference import NotificationPreference
from ..utils.email import send_email
from ..models import Favorite
from ..models.notification import Notification
from ..models.payment import Payment
from ..utils.admin_settings import get_admin_settings
from sqlalchemy import func
import os
from werkzeug.utils import secure_filename
import razorpay


dashboard = Blueprint(
    "dashboard",
    __name__,
    url_prefix="/dashboard"
)

def create_notification(
    user_id,
    title,
    message,
    notification_type,
    booking_id=None,
    professional_service_request_id=None,
    professional_user_id=None
):
    notification = Notification(
        user_id=user_id,
        title=title,
        message=message,
        notification_type=notification_type,
        booking_id=booking_id,
        professional_service_request_id=professional_service_request_id,
        professional_user_id=professional_user_id
    )

    db.session.add(notification)

    user = db.session.get(User, user_id)

    if user and user.email:
        send_email(
            recipient=user.email,
            subject=f"AllYourHelp - {title}",
            body=(
                f"Hello {user.name},\n\n"
                f"{message}\n\n"
                "You can log in to your AllYourHelp account "
                "to view more details.\n\n"
                "Regards,\n"
                "AllYourHelp Team"
            )
        )

def create_admin_notification(
    title,
    message,
    notification_type,
    booking_id=None,
    professional_service_request_id=None,
    professional_user_id=None
):
    admins = User.query.filter_by(role="admin").all()

    for admin in admins:
        create_notification(
            user_id=admin.id,
            title=title,
            message=message,
            notification_type=notification_type,
            booking_id=booking_id,
            professional_service_request_id=professional_service_request_id,
            professional_user_id=professional_user_id
        )


@dashboard.route("/")
@login_required
def user_dashboard():

    print("CURRENT USER:", current_user.id)
    print("NAME:", current_user.name)
    print("ROLE:", repr(current_user.role))

    if current_user.role == "professional":
        return redirect(
            url_for("dashboard.professional_dashboard")
        )

    categories = ServiceCategory.query.filter_by(
        is_active=True
    ).order_by(
        ServiceCategory.name
    ).all()

    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    return render_template(
        "dashboard/user.html",
        user=current_user,
        categories=categories,
        unread_notifications=unread_notifications
    )
# ============================================================
# CUSTOMER PROFILE
# ============================================================

@dashboard.route("/profile", methods=["GET", "POST"])
@login_required
def customer_profile():

    # Only normal users can access customer profile
    if current_user.role != "user":
        abort(403)

    # Allowed image extensions
    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }

    if request.method == "POST":

        # -----------------------------------------
        # GET FORM DATA
        # -----------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        # -----------------------------------------
        # BASIC VALIDATION
        # -----------------------------------------

        if not name:
            flash(
                "Name is required.",
                "error"
            )

            return redirect(
                url_for("dashboard.customer_profile")
            )

        if not email:
            flash(
                "Email is required.",
                "error"
            )

            return redirect(
                url_for("dashboard.customer_profile")
            )

        # -----------------------------------------
        # EMAIL VALIDATION
        # -----------------------------------------

        if "@" not in email or "." not in email:
            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for("dashboard.customer_profile")
            )

        # -----------------------------------------
        # CHECK EMAIL UNIQUENESS
        # -----------------------------------------

        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_user:
            flash(
                "This email address is already in use.",
                "error"
            )

            return redirect(
                url_for("dashboard.customer_profile")
            )

        # -----------------------------------------
        # UPDATE USER INFORMATION
        # -----------------------------------------

        current_user.name = name
        current_user.email = email
        current_user.phone = phone if phone else None

        # -----------------------------------------
        # PROFILE IMAGE
        # -----------------------------------------

        profile_image = request.files.get(
            "profile_image"
        )

        if profile_image and profile_image.filename:

            original_filename = secure_filename(
                profile_image.filename
            )

            if not original_filename:
                flash(
                    "Invalid profile image.",
                    "error"
                )

                return redirect(
                    url_for("dashboard.customer_profile")
                )

            # Get extension
            extension = (
                original_filename
                .rsplit(".", 1)[-1]
                .lower()
                if "." in original_filename
                else ""
            )

            # Check extension
            if extension not in allowed_extensions:
                flash(
                    "Only JPG, JPEG, PNG and WEBP images are allowed.",
                    "error"
                )

                return redirect(
                    url_for("dashboard.customer_profile")
                )

            # -----------------------------------------
            # CREATE UPLOAD DIRECTORY
            # -----------------------------------------

            upload_folder = os.path.join(
                current_app.static_folder,
                "uploads",
                "profiles"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            # -----------------------------------------
            # DELETE OLD IMAGE
            # -----------------------------------------

            old_image = current_user.profile_image

            if old_image:

                old_image_path = os.path.join(
                    current_app.static_folder,
                    old_image
                )

                if os.path.isfile(old_image_path):

                    try:
                        os.remove(old_image_path)

                    except OSError:
                        pass

            # -----------------------------------------
            # CREATE UNIQUE FILE NAME
            # -----------------------------------------

            filename = (
                f"user_{current_user.id}."
                f"{extension}"
            )

            image_path = os.path.join(
                upload_folder,
                filename
            )

            # -----------------------------------------
            # SAVE IMAGE
            # -----------------------------------------

            profile_image.save(
                image_path
            )

            # Store path relative to static/
            current_user.profile_image = (
                f"uploads/profiles/{filename}"
            )

        # -----------------------------------------
        # SAVE CHANGES
        # -----------------------------------------

        db.session.commit()

        flash(
            "Your profile has been updated successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard.customer_profile")
        )

    # -----------------------------------------
    # SHOW PROFILE PAGE
    # -----------------------------------------

    return render_template(
        "dashboard/customer_profile.html",
        user=current_user
    )
# ============================================================
# CUSTOMER CHANGE PASSWORD
# ============================================================

@dashboard.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():

    if current_user.role != "user":
        abort(403)

    if request.method == "POST":

        current_password = request.form.get(
            "current_password", ""
        ).strip()

        new_password = request.form.get(
            "new_password", ""
        ).strip()

        confirm_password = request.form.get(
            "confirm_password", ""
        ).strip()

        # Check current password
        if not current_user.check_password(current_password):
            flash(
                "Your current password is incorrect.",
                "error"
            )
            return redirect(
                url_for("dashboard.change_password")
            )

        # Check new password
        if not new_password:
            flash(
                "New password is required.",
                "error"
            )
            return redirect(
                url_for("dashboard.change_password")
            )

        # Minimum password length
        if len(new_password) < 8:
            flash(
                "New password must be at least 8 characters long.",
                "error"
            )
            return redirect(
                url_for("dashboard.change_password")
            )

        # Confirm password
        if new_password != confirm_password:
            flash(
                "New passwords do not match.",
                "error"
            )
            return redirect(
                url_for("dashboard.change_password")
            )

        # Prevent using the same password
        if current_user.check_password(new_password):
            flash(
                "Your new password must be different from your current password.",
                "error"
            )
            return redirect(
                url_for("dashboard.change_password")
            )

        # Update password
        current_user.set_password(new_password)

        db.session.commit()

        flash(
            "Your password has been changed successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard.customer_profile")
        )

    return render_template(
        "dashboard/change_password.html",
        user=current_user
    )

# ============================================================
# CUSTOMER NOTIFICATION PREFERENCES
# ============================================================

@dashboard.route("/notification-preferences", methods=["GET", "POST"])
@login_required
def notification_preferences():

    if current_user.role != "user":
        abort(403)

    from ..models.notification_preference import NotificationPreference

    preferences = NotificationPreference.query.filter_by(
        user_id=current_user.id
    ).first()

    # Create default preferences for this user if they don't exist
    if not preferences:
        preferences = NotificationPreference(
            user_id=current_user.id
        )

        db.session.add(preferences)
        db.session.commit()

    if request.method == "POST":

        preferences.booking_confirmation = (
            request.form.get("booking_confirmation") == "on"
        )

        preferences.booking_updates = (
            request.form.get("booking_updates") == "on"
        )

        preferences.professional_responses = (
            request.form.get("professional_responses") == "on"
        )

        preferences.completion_reminders = (
            request.form.get("completion_reminders") == "on"
        )

        db.session.commit()

        flash(
            "Notification preferences updated successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard.customer_profile")
        )

    return render_template(
        "dashboard/notification_preferences.html",
        user=current_user,
        preferences=preferences
    )

@dashboard.route("/professional")
@login_required
def professional_dashboard():

    # Only professionals can access this page
    if current_user.role != "professional":
        abort(403)

    # Get professional profile
    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    # Get all requests assigned to this professional
    requests = ServiceRequest.query.filter_by(
        professional_id=professional.id
    ).order_by(
        ServiceRequest.created_at.desc()
    ).all()

    # -----------------------------------------
    # DASHBOARD STATISTICS
    # -----------------------------------------

    total_requests = len(requests)

    pending_requests = ServiceRequest.query.filter_by(
        professional_id=professional.id,
        status="confirmed"
    ).count()

    accepted_requests = ServiceRequest.query.filter_by(
        professional_id=professional.id,
        status="accepted"
    ).count()

    completed_requests = ServiceRequest.query.filter_by(
        professional_id=professional.id,
        status="completed"
    ).count()

    # -----------------------------------------
    # REVIEWS
    # -----------------------------------------

    reviews = Review.query.filter_by(
        professional_id=professional.id
    ).order_by(
        Review.created_at.desc()
    ).all()

    review_count = len(reviews)

    average_rating = db.session.query(
        func.avg(Review.rating)
    ).filter(
        Review.professional_id == professional.id
    ).scalar()

    average_rating = (
        round(float(average_rating), 1)
        if average_rating is not None
        else 0.0
    )

    # -----------------------------------------
    # UPCOMING APPOINTMENTS
    # -----------------------------------------

    upcoming_requests = ServiceRequest.query.filter(
        ServiceRequest.professional_id == professional.id,
        ServiceRequest.status == "accepted",
        ServiceRequest.preferred_date >= date.today()
    ).order_by(
        ServiceRequest.preferred_date.asc(),
        ServiceRequest.preferred_time.asc()
    ).limit(5).all()

    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    return render_template(
        "dashboard/professional.html",
        user=current_user,
        professional=professional,
        requests=requests,
        total_requests=total_requests,
        pending_requests=pending_requests,
        accepted_requests=accepted_requests,
        completed_requests=completed_requests,
        reviews=reviews,
        review_count=review_count,
        average_rating=average_rating,
        upcoming_requests=upcoming_requests,
        unread_notifications=unread_notifications
    )
# ============================================================
# PROFESSIONAL PROFILE EDIT
# ============================================================

@dashboard.route(
    "/professional/profile/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_professional_profile():

    # Only professionals can edit professional profiles
    if current_user.role != "professional":
        abort(403)

    # Get professional profile
    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    # Allowed image extensions
    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }

    if request.method == "POST":

        # -----------------------------------------
        # GET FORM DATA
        # -----------------------------------------

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        bio = request.form.get(
            "bio",
            ""
        ).strip()

        experience = request.form.get(
            "experience",
            ""
        ).strip()

        location = request.form.get(
            "location",
            ""
        ).strip()

        # -----------------------------------------
        # BASIC VALIDATION
        # -----------------------------------------

        if not name:

            flash(
                "Name is required.",
                "error"
            )

            return redirect(
                url_for(
                    "dashboard.edit_professional_profile"
                )
            )

        if not email:

            flash(
                "Email is required.",
                "error"
            )

            return redirect(
                url_for(
                    "dashboard.edit_professional_profile"
                )
            )

        # -----------------------------------------
        # CHECK EMAIL FORMAT
        # -----------------------------------------

        if "@" not in email or "." not in email:

            flash(
                "Please enter a valid email address.",
                "error"
            )

            return redirect(
                url_for(
                    "dashboard.edit_professional_profile"
                )
            )

        # -----------------------------------------
        # CHECK EMAIL UNIQUENESS
        # -----------------------------------------

        existing_user = User.query.filter(
            User.email == email,
            User.id != current_user.id
        ).first()

        if existing_user:

            flash(
                "This email address is already in use.",
                "error"
            )

            return redirect(
                url_for(
                    "dashboard.edit_professional_profile"
                )
            )

        # -----------------------------------------
        # VALIDATE EXPERIENCE
        # -----------------------------------------

        if experience:

            try:

                experience_value = int(
                    experience
                )

            except ValueError:

                flash(
                    "Years of experience must be a valid number.",
                    "error"
                )

                return redirect(
                    url_for(
                        "dashboard.edit_professional_profile"
                    )
                )

            if experience_value < 0 or experience_value > 100:

                flash(
                    "Please enter a valid number of years of experience.",
                    "error"
                )

                return redirect(
                    url_for(
                        "dashboard.edit_professional_profile"
                    )
                )

        else:

            experience_value = None

        # -----------------------------------------
        # UPDATE USER INFORMATION
        # -----------------------------------------

        current_user.name = name
        current_user.email = email
        current_user.phone = phone if phone else None

        # -----------------------------------------
        # UPDATE PROFESSIONAL INFORMATION
        # -----------------------------------------

        professional.bio = bio if bio else None
        professional.experience = experience_value
        professional.location = location if location else None

        # -----------------------------------------
        # PROFILE IMAGE
        # -----------------------------------------

        profile_image = request.files.get(
            "profile_image"
        )

        if profile_image and profile_image.filename:

            original_filename = secure_filename(
                profile_image.filename
            )

            if not original_filename:

                flash(
                    "Invalid profile image.",
                    "error"
                )

                return redirect(
                    url_for(
                        "dashboard.edit_professional_profile"
                    )
                )

            extension = (
                original_filename
                .rsplit(".", 1)[-1]
                .lower()
                if "." in original_filename
                else ""
            )

            if extension not in allowed_extensions:

                flash(
                    "Only JPG, JPEG, PNG and WEBP images are allowed.",
                    "error"
                )

                return redirect(
                    url_for(
                        "dashboard.edit_professional_profile"
                    )
                )

            # -----------------------------------------
            # CREATE UPLOAD DIRECTORY
            # -----------------------------------------

            upload_folder = os.path.join(
                current_app.static_folder,
                "uploads",
                "profiles"
            )

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            # -----------------------------------------
            # DELETE OLD IMAGE
            # -----------------------------------------

            old_image = current_user.profile_image

            if old_image:

                old_image_path = os.path.join(
                    current_app.static_folder,
                    old_image
                )

                if os.path.isfile(old_image_path):

                    try:

                        os.remove(
                            old_image_path
                        )

                    except OSError:

                        pass

            # -----------------------------------------
            # CREATE UNIQUE FILE NAME
            # -----------------------------------------

            filename = (
                f"user_{current_user.id}."
                f"{extension}"
            )

            image_path = os.path.join(
                upload_folder,
                filename
            )

            # -----------------------------------------
            # SAVE IMAGE
            # -----------------------------------------

            profile_image.save(
                image_path
            )

            # Store path relative to static/
            current_user.profile_image = (
                f"uploads/profiles/{filename}"
            )

        # -----------------------------------------
        # SAVE DATABASE CHANGES
        # -----------------------------------------

        db.session.commit()

        flash(
            "Your professional profile has been updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "dashboard.professional_dashboard"
            )
        )

    # -----------------------------------------
    # SHOW EDIT PAGE
    # -----------------------------------------

    return render_template(
        "dashboard/edit_professional_profile.html",
        user=current_user,
        professional=professional
    )
# ============================================================
# PROFESSIONAL SERVICE MANAGEMENT
# ============================================================

@dashboard.route("/professional/services", methods=["GET", "POST"])
@login_required
def manage_professional_services():

    if current_user.role != "professional":
        abort(403)

    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    # Get all active services grouped by category
    categories = ServiceCategory.query.filter_by(
        is_active=True
    ).order_by(ServiceCategory.name).all()

    active_services = Service.query.filter_by(
        is_active=True
    ).order_by(Service.name).all()

    # Services that are already approved and active
    approved_service_ids = {
        service.id for service in professional.services
    }

    # Existing pending approval requests
    pending_requests = ProfessionalServiceRequest.query.filter_by(
        professional_id=professional.id,
        status="pending"
    ).all()

    pending_service_ids = {
        request.service_id for request in pending_requests
    }
    rejected_requests = ProfessionalServiceRequest.query.filter_by(
    professional_id=professional.id,
    status="rejected"
    ).all()

    rejected_service_ids = {
        request.service_id for request in rejected_requests
    }

    if request.method == "POST":

        selected_ids = request.form.getlist("service_ids")

        try:
            selected_service_ids = {
                int(service_id)
                for service_id in selected_ids
            }
        except ValueError:
            flash("Invalid service selection.", "error")
            return redirect(
                url_for("dashboard.manage_professional_services")
            )

        # ---------------------------------------------------------
        # No service selected
        # ---------------------------------------------------------

        if not selected_service_ids and not pending_service_ids:
            flash(
                "Please select at least one service before saving.",
                "error"
            )
            return redirect(
                url_for("dashboard.manage_professional_services")
            )

        # Only allow active services
        valid_services = Service.query.filter(
            Service.id.in_(selected_service_ids),
            Service.is_active.is_(True)
        ).all()

        valid_service_ids = {
            service.id for service in valid_services
        }

        # ---------------------------------------------------------
        # REMOVE APPROVED SERVICES
        #
        # Removing an already-approved service does NOT require
        # admin approval.
        # ---------------------------------------------------------

        services_to_remove = approved_service_ids - valid_service_ids

        if services_to_remove:
            professional.services = [
                service
                for service in professional.services
                if service.id not in services_to_remove
            ]

            # Mark the old approval as removed
            for service_id in services_to_remove:

                old_request = ProfessionalServiceRequest.query.filter_by(
                    professional_id=professional.id,
                    service_id=service_id
                ).first()

                if old_request:
                    old_request.status = "removed"

        # ---------------------------------------------------------
        # NEW SERVICE REQUESTS
        #
        # A newly selected service does NOT immediately become
        # active. It goes into pending approval.
        # ---------------------------------------------------------

        new_service_ids = (
            valid_service_ids
            - approved_service_ids
            - pending_service_ids
        )

        pending_created = 0

        for service_id in new_service_ids:

            existing_request = ProfessionalServiceRequest.query.filter_by(
                professional_id=professional.id,
                service_id=service_id
            ).first()

            service = Service.query.get(service_id)

            if existing_request:
                # Re-request a previously rejected/removed service
                existing_request.status = "pending"
                existing_request.updated_at = datetime.utcnow()

                service_request = existing_request

            else:
                service_request = ProfessionalServiceRequest(
                    professional_id=professional.id,
                    service_id=service_id,
                    status="pending"
                )

                db.session.add(service_request)
                db.session.flush()

            create_admin_notification(
                title="New Professional Service Request",
                message=(
                    f"{professional.user.name} has requested approval "
                    f"for the {service.name} service."
                ),
                notification_type="new_professional_service_request",
                professional_service_request_id=service_request.id,
                professional_user_id=professional.user.id
            )

            pending_created += 1

            

        # ---------------------------------------------------------
        # KEEP EXISTING PENDING REQUESTS
        #
        # Pending requests cannot be directly activated by the
        # professional.
        # ---------------------------------------------------------

        db.session.commit()

        if pending_created > 0:
            flash(
                "Your selected service(s) have been submitted for admin approval.",
                "success"
            )
        else:
            flash(
                "Your service changes have been saved.",
                "success"
            )

        return redirect(
            url_for("dashboard.manage_professional_services")
        )

    return render_template(
        "dashboard/manage_professional_services.html",
        professional=professional,
        categories=categories,
        services=active_services,
        approved_service_ids=approved_service_ids,
        pending_service_ids=pending_service_ids,
        rejected_service_ids=rejected_service_ids
    )
@dashboard.route("/availability", methods=["GET", "POST"])
@login_required
def manage_availability():

    # Only professionals can manage availability
    if current_user.role != "professional":
        abort(403)

    # Get professional profile
    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    # Today's date
    today = date.today()

    # Last allowed date = 7 days ahead
    last_day = today.fromordinal(
        today.toordinal() + 7
    )

    if request.method == "POST":

        slot_date = request.form.get("slot_date")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")

        # Check required fields
        if not slot_date or not start_time or not end_time:

            flash(
                "Please select a date, start time and end time.",
                "error"
            )

            return redirect(
                url_for("dashboard.manage_availability")
            )

        # Convert date
        try:

            selected_date = datetime.strptime(
                slot_date,
                "%Y-%m-%d"
            ).date()

        except ValueError:

            flash(
                "Invalid date.",
                "error"
            )

            return redirect(
                url_for("dashboard.manage_availability")
            )

        # Convert times
        try:

            selected_start_time = datetime.strptime(
                start_time,
                "%H:%M"
            ).time()

            selected_end_time = datetime.strptime(
                end_time,
                "%H:%M"
            ).time()

        except ValueError:

            flash(
                "Invalid time.",
                "error"
            )

            return redirect(
                url_for("dashboard.manage_availability")
            )

        # Date must be within next 7 days
        if selected_date < today or selected_date > last_day:

            flash(
                "You can only add slots for the next 7 days.",
                "error"
            )

            return redirect(
                url_for("dashboard.manage_availability")
            )

        # End time must be after start time
        if selected_end_time <= selected_start_time:

            flash(
                "End time must be after start time.",
                "error"
            )

            return redirect(
                url_for("dashboard.manage_availability")
            )

        # Check for overlapping slots
        overlapping_slot = AvailabilitySlot.query.filter(
            AvailabilitySlot.professional_id == professional.id,
            AvailabilitySlot.slot_date == selected_date,
            AvailabilitySlot.start_time < selected_end_time,
            AvailabilitySlot.end_time > selected_start_time
        ).first()

        if overlapping_slot:

            flash(
                "This time overlaps with an existing slot.",
                "error"
            )

            return redirect(
                url_for("dashboard.manage_availability")
            )

        # Create slot
        slot = AvailabilitySlot(

            professional_id=professional.id,

            slot_date=selected_date,

            start_time=selected_start_time,

            end_time=selected_end_time,

            is_booked=False
        )

        db.session.add(slot)
        db.session.commit()

        flash(
            "Availability slot added successfully.",
            "success"
        )

        return redirect(
            url_for("dashboard.manage_availability")
        )

    # Get professional's slots
    slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.professional_id == professional.id,
        AvailabilitySlot.slot_date >= today,
        AvailabilitySlot.slot_date <= last_day
    ).order_by(
        AvailabilitySlot.slot_date,
        AvailabilitySlot.start_time
    ).all()

    return render_template(
        "dashboard/availability.html",
        user=current_user,
        professional=professional,
        slots=slots,
        today=today,
        last_day=last_day
    )


@dashboard.route(
    "/availability/delete/<int:slot_id>",
    methods=["POST"]
)
@login_required
def delete_availability(slot_id):

    # Only professionals
    if current_user.role != "professional":
        abort(403)

    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    slot = AvailabilitySlot.query.filter_by(
        id=slot_id,
        professional_id=professional.id
    ).first()

    if not slot:
        abort(404)

    # Don't allow deleting an already booked slot
    if slot.is_booked:

        flash(
            "A booked slot cannot be deleted.",
            "error"
        )

        return redirect(
            url_for("dashboard.manage_availability")
        )

    db.session.delete(slot)
    db.session.commit()

    flash(
        "Availability slot removed.",
        "success"
    )

    return redirect(
        url_for("dashboard.manage_availability")
    )


# ============================================================
# ACCEPT SERVICE REQUEST
# ============================================================

@dashboard.route(
    "/professional/request/<int:request_id>/accept",
    methods=["POST"]
)
@login_required
def accept_request(request_id):

    # Only professionals can accept requests
    if current_user.role != "professional":
        abort(403)

    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    service_request = ServiceRequest.query.get(
        request_id
    )

    if not service_request:
        abort(404)

    # Make sure this request belongs to this professional
    if service_request.professional_id != professional.id:
        abort(403)

    # Only pending requests can be accepted
    if service_request.status != "pending":

        flash(
            "This request can no longer be accepted.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.professional_dashboard"
            )
        )

    service_request.status = "accepted"

    db.session.commit()

    flash(
        "Service request accepted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "dashboard.professional_dashboard"
        )
    )


# ============================================================
# REJECT SERVICE REQUEST
# ============================================================

@dashboard.route(
    "/professional/request/<int:request_id>/reject",
    methods=["POST"]
)
@login_required
def reject_request(request_id):

    # Only professionals can reject requests
    if current_user.role != "professional":
        abort(403)

    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    service_request = ServiceRequest.query.get(
        request_id
    )

    if not service_request:
        abort(404)

    # Make sure this request belongs to this professional
    if service_request.professional_id != professional.id:
        abort(403)

    # Only pending requests can be rejected
    if service_request.status != "pending":

        flash(
            "This request can no longer be rejected.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.professional_dashboard"
            )
        )

    service_request.status = "rejected"

    db.session.commit()

    flash(
        "Service request rejected.",
        "success"
    )

    return redirect(
        url_for(
            "dashboard.professional_dashboard"
        )
    )


# ============================================================
# COMPLETE SERVICE REQUEST
# ============================================================

@dashboard.route(
    "/professional/request/<int:request_id>/complete",
    methods=["POST"]
)
@login_required
def complete_request(request_id):

    # Only professionals can complete requests
    if current_user.role != "professional":
        abort(403)

    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    service_request = ServiceRequest.query.get(
        request_id
    )

    if not service_request:
        abort(404)

    # Make sure this request belongs to this professional
    if service_request.professional_id != professional.id:
        abort(403)

    # Only accepted requests can be completed
    if service_request.status != "accepted":

        flash(
            "Only accepted requests can be marked as completed.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.professional_dashboard"
            )
        )

    service_request.status = "completed"

    create_notification(
        user_id=service_request.professional.user_id,
        title="Booking Completed",
        message=(
            f"Your {service_request.service.name} booking "
            "has been marked as completed."
        ),
        notification_type="booking_completed_professional",
        booking_id=service_request.id
    )

    preferences = NotificationPreference.query.filter_by(
        user_id=service_request.user_id
    ).first()

    if preferences is None:
        preferences = NotificationPreference(
            user_id=service_request.user_id
        )
        db.session.add(preferences)

    if preferences.completion_reminders:
        create_notification(
            user_id=service_request.user_id,
            title="Booking Completed",
            message=(
                f"Your booking for {service_request.service.name} "
                "has been marked as completed."
            ),
            notification_type="booking_completed",
            booking_id=service_request.id
        )

    db.session.commit()

    flash(
        "Service request marked as completed.",
        "success"
    )

    return redirect(
        url_for(
            "dashboard.professional_dashboard"
        )
    )
@dashboard.route("/bookings")
@login_required
def my_bookings():

    bookings = ServiceRequest.query.filter(
        ServiceRequest.user_id == current_user.id,
        ServiceRequest.payment_status.in_([
            "paid",
            "refunded"
        ])
    ).order_by(
        ServiceRequest.created_at.desc()
    ).all()

    # --------------------------------------------------------
    # BOOKING STATISTICS
    # --------------------------------------------------------

    total_bookings = len(bookings)

    upcoming_bookings = sum(
        1
        for booking in bookings
        if booking.status == "accepted"
        and booking.preferred_date
        and booking.preferred_date >= date.today()
    )

    completed_bookings = sum(
        1
        for booking in bookings
        if booking.status == "completed"
    )

    refunded_bookings = sum(
        1
        for booking in bookings
        if booking.payment_status == "refunded"
    )


    return render_template(
        "dashboard/my_bookings.html",
        user=current_user,
        bookings=bookings,
        total_bookings=total_bookings,
        upcoming_bookings=upcoming_bookings,
        completed_bookings=completed_bookings,
        refunded_bookings=refunded_bookings
    )

@dashboard.route(
    "/bookings/<int:request_id>/review",
    methods=["POST"]
)
@login_required
def submit_review(request_id):

    if current_user.role != "user":
        abort(403)

    service_request = ServiceRequest.query.filter_by(
        id=request_id,
        user_id=current_user.id
    ).first()

    if not service_request:
        abort(404)

    # Only completed services can be reviewed
    if service_request.status != "completed":
        flash(
            "You can review a service only after it has been completed.",
            "error"
        )
        return redirect(url_for("dashboard.my_bookings"))

    # ---------------------------------------------------------
    # CHECK FOR EXISTING REVIEW
    # ---------------------------------------------------------

    existing_review = Review.query.filter_by(
        service_request_id=service_request.id
    ).first()

    if existing_review:
        flash(
            "You have already reviewed this service.",
            "error"
        )
        return redirect(url_for("dashboard.my_bookings"))

    # ---------------------------------------------------------
    # GET FORM DATA
    # ---------------------------------------------------------

    rating = request.form.get("rating", type=int)
    comment = request.form.get("comment", "").strip()

    # ---------------------------------------------------------
    # VALIDATE RATING
    # ---------------------------------------------------------

    if rating is None or rating < 1 or rating > 5:
        flash(
            "Please select a rating between 1 and 5 stars.",
            "error"
        )
        return redirect(url_for("dashboard.my_bookings"))

    # ---------------------------------------------------------
    # GET PROFESSIONAL
    # ---------------------------------------------------------

    professional = service_request.professional

    if not professional:
        flash(
            "The professional associated with this booking could not be found.",
            "error"
        )
        return redirect(url_for("dashboard.my_bookings"))

    # ---------------------------------------------------------
    # GET SERVICE NAME BEFORE ADDING REVIEW
    # ---------------------------------------------------------

    service_name = service_request.service.name

    # ---------------------------------------------------------
    # CREATE REVIEW
    # ---------------------------------------------------------

    review = Review(
        user_id=current_user.id,
        professional_id=professional.id,
        service_request_id=service_request.id,
        rating=rating,
        comment=comment if comment else None
    )

    try:

        db.session.add(review)

        # Save review first
        db.session.commit()

    except Exception as e:

        # Roll back failed transaction
        db.session.rollback()

        # Handle duplicate review safely
        if "reviews_service_request_id_key" in str(e):

            flash(
                "You have already reviewed this service.",
                "error"
            )

            return redirect(
                url_for("dashboard.my_bookings")
            )

        # Re-raise unexpected errors
        raise

    # ---------------------------------------------------------
    # NOTIFY PROFESSIONAL
    # ---------------------------------------------------------

    create_notification(
        user_id=professional.user_id,
        title="New Review",
        message=(
            f"You received a new review for "
            f"{service_name}."
        ),
        notification_type="new_review",
        booking_id=service_request.id
    )

    db.session.commit()

    flash(
        "Thank you! Your review has been submitted.",
        "success"
    )

    return redirect(
        url_for("dashboard.my_bookings")
    )

@dashboard.route("/bookings/<int:request_id>")
@login_required
def booking_details(request_id):

    service_request = ServiceRequest.query.filter_by(
        id=request_id,
        user_id=current_user.id
    ).first()

    if not service_request:
        abort(404)

    return render_template(
        "dashboard/booking_details.html",
        service_request=service_request
    )
@dashboard.route(
    "/bookings/<int:request_id>/cancel",
    methods=["POST"]
)
@login_required
def cancel_booking(request_id):

    # Find the booking belonging to the logged-in user
    service_request = ServiceRequest.query.filter_by(
        id=request_id,
        user_id=current_user.id
    ).first()

    if not service_request:
        abort(404)

    # Only pending or confirmed bookings can be cancelled
    if service_request.status not in ["pending", "confirmed"]:

        flash(
            "This booking cannot be cancelled.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.booking_details",
                request_id=service_request.id
            )
        )

    # --------------------------------------------------
    # RELEASE AVAILABILITY SLOT
    # --------------------------------------------------

    if service_request.availability_slot:
        service_request.availability_slot.is_booked = False

    # --------------------------------------------------
    # CANCEL BOOKING
    # --------------------------------------------------

    service_request.status = "cancelled"

    # --------------------------------------------------
    # PROCESS REFUND
    # --------------------------------------------------

    if service_request.payment_status == "paid":

        service_request.refund_status = "refunded"

        service_request.refund_amount = (
            service_request.payment_amount
        )

        service_request.refund_id = (
            f"TEST-REFUND-{service_request.id}"
        )

        service_request.payment_status = "refunded"

    # --------------------------------------------------
    # ADMIN NOTIFICATION
    # --------------------------------------------------

    create_admin_notification(
        title="Booking Cancelled",
        message=(
            f"{service_request.user.name} has cancelled their "
            f"{service_request.service.name} booking "
            f"(Booking #{service_request.id})."
        ),
        notification_type="booking_cancelled_admin",
        booking_id=service_request.id
    )

    # --------------------------------------------------
    # PROFESSIONAL NOTIFICATION
    # --------------------------------------------------

    if service_request.professional:

        create_notification(
            user_id=service_request.professional.user_id,
            title="Booking Cancelled",
            message=(
                f"The customer has cancelled the booking for "
                f"{service_request.service.name}."
            ),
            notification_type="booking_cancelled",
            booking_id=service_request.id
        )

    # --------------------------------------------------
    # CUSTOMER NOTIFICATION
    # --------------------------------------------------

    preferences = NotificationPreference.query.filter_by(
        user_id=service_request.user_id
    ).first()

    if preferences is None:

        preferences = NotificationPreference(
            user_id=service_request.user_id
        )

        db.session.add(preferences)

    if preferences.booking_updates:

        if service_request.payment_status == "refunded":

            create_notification(
                user_id=service_request.user_id,
                title="Refund Processed",
                message=(
                    f"Your booking for "
                    f"{service_request.service.name} "
                    f"has been cancelled and your refund of "
                    f"₹{service_request.refund_amount} "
                    f"has been processed."
                ),
                notification_type="refund_processed",
                booking_id=service_request.id
            )

        else:

            create_notification(
                user_id=service_request.user_id,
                title="Booking Cancelled",
                message=(
                    f"Your booking for "
                    f"{service_request.service.name} "
                    f"has been cancelled."
                ),
                notification_type="booking_cancelled",
                booking_id=service_request.id
            )

    # --------------------------------------------------
    # COMMIT EVERYTHING
    # --------------------------------------------------

    db.session.commit()

    # --------------------------------------------------
    # SUCCESS MESSAGE
    # --------------------------------------------------

    if service_request.refund_status == "refunded":

        flash(
            "Your booking has been cancelled and your refund "
            "has been processed successfully.",
            "success"
        )

    else:

        flash(
            "Your booking has been cancelled successfully.",
            "success"
        )

    return redirect(
        url_for("dashboard.my_bookings")
    )
@dashboard.route(
    "/bookings/payment",
    methods=["GET"]
)
@login_required
def booking_payment():

    settings = get_admin_settings()

    if not settings.bookings_enabled:
        session.pop("pending_booking", None)
        session.pop("razorpay_order_id", None)

        flash(
            "Bookings are currently unavailable. Please try again later.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.user_dashboard"
            )
        )

    # --------------------------------
    # GET PENDING BOOKING FROM SESSION
    # --------------------------------

    pending_booking = session.get(
        "pending_booking"
    )

    if not pending_booking:

        flash(
            "No pending booking found.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.my_bookings"
            )
        )

    # --------------------------------
    # SECURITY CHECK
    # --------------------------------

    if pending_booking.get(
        "user_id"
    ) != current_user.id:

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "Invalid booking information.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.my_bookings"
            )
        )

    # --------------------------------
    # GET SERVICE
    # --------------------------------

    service = Service.query.get(
        pending_booking.get("service_id")
    )

    # --------------------------------
    # GET PROFESSIONAL
    # --------------------------------

    professional = ProfessionalProfile.query.get(
        pending_booking.get("professional_id")
    )

    # --------------------------------
    # GET SLOT
    # --------------------------------

    slot = AvailabilitySlot.query.filter_by(
        id=pending_booking.get("slot_id"),
        professional_id=pending_booking.get(
            "professional_id"
        )
    ).first()

    # --------------------------------
    # VALIDATE BOOKING DATA
    # --------------------------------

    if not service or not professional or not slot:

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "The booking information is no longer valid.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.my_bookings"
            )
        )

    # --------------------------------
    # CHECK SLOT AGAIN
    # --------------------------------

    if slot.is_booked:

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "Sorry, this slot has already been booked.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # --------------------------------
    # CHECK DATE AGAIN
    # --------------------------------

    today = datetime.utcnow().date()

    if slot.slot_date < today:

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "This availability slot is no longer available.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )
    amount = service.price or 0

    razorpay_client = razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"]
        )
    )

    razorpay_order = razorpay_client.order.create({
        "amount": int(float(amount) * 100),
    "currency": "INR",
    "receipt": f"booking_{pending_booking.get('slot_id')}",
    "payment_capture": 1
    })

    session["razorpay_order_id"] = razorpay_order["id"]
    # --------------------------------
    # SHOW PAYMENT PAGE
    # --------------------------------

    return render_template(
        "dashboard/payment.html",
        service=service,
        professional=professional,
        slot=slot,
        pending_booking=pending_booking,
        razorpay_order=razorpay_order,
        razorpay_key_id=current_app.config["RAZORPAY_KEY_ID"]
    )
@dashboard.route(
    "/bookings/process-payment",
    methods=["POST"]
)
@login_required
def process_payment():

    # --------------------------------
    # GET PENDING BOOKING
    # --------------------------------

    pending_booking = session.get(
        "pending_booking"
    )

    if not pending_booking:

        flash(
            "No pending booking found.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.my_bookings"
            )
        )

    # --------------------------------
    # SECURITY CHECK
    # --------------------------------

    if pending_booking.get(
        "user_id"
    ) != current_user.id:

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "Invalid booking information.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.my_bookings"
            )
        )

    # --------------------------------
    # GET SERVICE
    # --------------------------------

    service = Service.query.get(
        pending_booking.get("service_id")
    )

    # --------------------------------
    # GET PROFESSIONAL
    # --------------------------------

    professional = ProfessionalProfile.query.get(
        pending_booking.get("professional_id")
    )

    # --------------------------------
    # GET SLOT
    # --------------------------------

    slot = AvailabilitySlot.query.filter_by(
        id=pending_booking.get("slot_id"),
        professional_id=pending_booking.get(
            "professional_id"
        )
    ).first()

    # --------------------------------
    # VALIDATE
    # --------------------------------

    if not service or not professional or not slot:

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "The booking information is no longer valid.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.my_bookings"
            )
        )

    # --------------------------------
    # CHECK SLOT
    # --------------------------------

    if slot.is_booked:

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "Sorry, this slot has already been booked.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # --------------------------------
    # CHECK DATE
    # --------------------------------

    today = datetime.utcnow().date()

    if slot.slot_date < today:

        session.pop(
            "pending_booking",
            None
        )

        flash(
            "This availability slot is no longer available.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # --------------------------------
    # PAYMENT SUCCESS
    # --------------------------------

    amount = service.price or 0

    # --------------------------------
    # CREATE ACTUAL BOOKING
    # --------------------------------

    service_request = ServiceRequest(

        user_id=current_user.id,

        professional_id=professional.id,

        service_id=service.id,

        availability_slot_id=slot.id,

        description=pending_booking.get(
            "description"
        ),

        preferred_date=slot.slot_date,

        preferred_time=slot.start_time,

        location=pending_booking.get(
            "location"
        ),

        additional_details=pending_booking.get(
            "additional_details"
        ),

        status="confirmed",

        payment_status="paid",

        payment_amount=amount,

        payment_id=f"TEST-PAY-{current_user.id}-{slot.id}"
    )

    # --------------------------------
    # NOW BOOK THE SLOT
    # --------------------------------

    slot.is_booked = True
    db.session.add(service_request)
    db.session.flush()

    payment = Payment(
        service_request_id=service_request.id,
        user_id=service_request.user_id,
        professional_id=service_request.professional_id,
        amount=amount,
        currency="INR",
        status="paid",
        gateway="test",
        gateway_payment_id=service_request.payment_id,
        paid_at=datetime.utcnow()
    )

    db.session.add(payment)

    professional = db.session.get(
        ProfessionalProfile,
        service_request.professional_id
    )

    service = db.session.get(
        Service,
        service_request.service_id
    )

    user = db.session.get(
        User,
        service_request.user_id
    )

    create_admin_notification(
        title="New Booking",
        message=(
            f"New booking received for {service.name} "
            f"from {user.name}."
        ),
        notification_type="new_booking_admin",
        booking_id=service_request.id
    )

    preferences = NotificationPreference.query.filter_by(
        user_id=current_user.id
    ).first()

    if preferences is None:
        preferences = NotificationPreference(
            user_id=current_user.id
        )
        db.session.add(preferences)

    if preferences.booking_confirmation:
        create_notification(
            user_id=current_user.id,
            title="Booking Confirmed",
            message=f"Your booking for {service.name} has been confirmed successfully.",
            notification_type="booking_confirmation",
            booking_id=service_request.id
        )
    professional_user_id = professional.user_id

    create_notification(
        user_id=professional_user_id,
        title="New Booking Request",
        message=f"You have received a new booking request for {service.name}.",
        notification_type="new_booking",
        booking_id=service_request.id
    )

    db.session.commit()

    # --------------------------------
    # REMOVE PENDING BOOKING
    # --------------------------------

    session.pop(
        "pending_booking",
        None
    )

    # --------------------------------
    # REDIRECT TO SUCCESS
    # --------------------------------

    return redirect(
        url_for(
            "services.booking_success",
            request_id=service_request.id
        )
    )
@dashboard.route(
    "/requests/<int:request_id>/accept",
    methods=["POST"]
)
@login_required
def accept_service_request(request_id):

    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(403)

    service_request = ServiceRequest.query.filter_by(
        id=request_id,
        professional_id=professional.id
    ).first()

    if not service_request:
        abort(404)

    if service_request.payment_status != "paid":

        flash(
            "Only paid bookings can be accepted.",
            "error"
        )

        return redirect(
            url_for("dashboard.professional_dashboard")
        )

    service_request.status = "accepted"

    preferences = NotificationPreference.query.filter_by(
        user_id=service_request.user_id
    ).first()

    if preferences is None:
        preferences = NotificationPreference(
            user_id=service_request.user_id
        )
        db.session.add(preferences)

    if preferences.booking_updates:
        create_notification(
            user_id=service_request.user_id,
            title="Booking Accepted",
            message=(
                f"Your booking for {service_request.service.name} "
                "has been accepted by the professional."
            ),
            notification_type="booking_accepted",
            booking_id=service_request.id
        )

    db.session.commit()

    flash(
        "Booking accepted successfully.",
        "success"
    )

    return redirect(
        url_for("dashboard.professional_dashboard")
    )
@dashboard.route("/requests/<int:request_id>/reject", methods=["POST"])
@login_required
def reject_service_request(request_id):

    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(403)

    service_request = ServiceRequest.query.filter_by(
        id=request_id,
        professional_id=professional.id
    ).first()

    if not service_request:
        abort(404)

    # Only paid bookings can be rejected
    if service_request.payment_status != "paid":
        flash(
            "Only paid bookings can be rejected.",
            "error"
        )
        return redirect(
            url_for("dashboard.professional_dashboard")
        )

    # ---------------------------------------------------------
    # Reject booking
    # ---------------------------------------------------------

    service_request.status = "rejected"

    # ---------------------------------------------------------
    # Refund
    # ---------------------------------------------------------

    service_request.refund_status = "refunded"
    service_request.refund_amount = service_request.payment_amount
    service_request.refund_id = f"TEST-REFUND-{service_request.id}"

    # Mark payment as refunded
    service_request.payment_status = "refunded"

    # ---------------------------------------------------------
    # Notify customer about booking rejection
    # ---------------------------------------------------------

    preferences = NotificationPreference.query.filter_by(
        user_id=service_request.user_id
    ).first()

    if preferences is None:
        preferences = NotificationPreference(
            user_id=service_request.user_id
        )
        db.session.add(preferences)

    if preferences.booking_updates:

        create_notification(
            user_id=service_request.user_id,
            title="Booking Rejected",
            message=(
                f"Your booking for {service_request.service.name} "
                "has been rejected by the professional."
            ),
            notification_type="booking_rejected",
            booking_id=service_request.id
        )

    # ---------------------------------------------------------
    # Notify admin about processed refund
    # ---------------------------------------------------------

    create_admin_notification(
        title="Refund Processed",
        message=(
            f"Refund processed for "
            f"{service_request.user.name}'s "
            f"{service_request.service.name} booking "
            f"(Booking #{service_request.id}). "
            f"Refund amount: ₹{service_request.refund_amount}."
        ),
        notification_type="refund_processed_admin",
        booking_id=service_request.id
    )

    # ---------------------------------------------------------
    # Notify customer about refund
    # ---------------------------------------------------------

    if preferences.booking_updates:

        create_notification(
            user_id=service_request.user_id,
            title="Refund Processed",
            message=(
                f"Your refund for {service_request.service.name} "
                "has been processed successfully."
            ),
            notification_type="refund_processed",
            booking_id=service_request.id
        )

    # ---------------------------------------------------------
    # Release the availability slot
    # ---------------------------------------------------------

    if service_request.availability_slot:
        service_request.availability_slot.is_booked = False

    # ---------------------------------------------------------
    # Save everything
    # ---------------------------------------------------------

    db.session.commit()

    flash(
        "Booking rejected and refund completed.",
        "success"
    )

    return redirect(
        url_for("dashboard.professional_dashboard")
    )

# ============================================================
# PROFESSIONAL BOOKING MANAGEMENT
# ============================================================

@dashboard.route("/professional/bookings")
@login_required
def professional_bookings():

    # Only professionals can access this page
    if current_user.role != "professional":
        abort(403)

    # Get the professional profile
    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        flash(
            "Professional profile not found.",
            "error"
        )

        return redirect(
            url_for("dashboard.index")
        )

    # Get all bookings assigned to this professional
    bookings = (
        ServiceRequest.query
        .filter_by(
            professional_id=professional.id
        )
        .order_by(
            ServiceRequest.preferred_date.desc()
        )
        .all()
    )

    return render_template(
        "dashboard/professional_bookings.html",
        professional=professional,
        bookings=bookings
    )
# ============================================================
# PROFESSIONAL BOOKING DETAILS
# ============================================================

@dashboard.route("/professional/bookings/<int:request_id>")
@login_required
def professional_booking_details(request_id):

    # Only professionals can access this page
    if current_user.role != "professional":
        abort(403)

    # Get professional profile
    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    # Get the booking
    booking = ServiceRequest.query.filter_by(
        id=request_id,
        professional_id=professional.id
    ).first_or_404()

    return render_template(
        "dashboard/professional_booking_details.html",
        user=current_user,
        professional=professional,
        booking=booking
    )
# ============================================================
# PROFESSIONAL EARNINGS & PAYMENTS
# ============================================================

@dashboard.route("/professional/earnings")
@login_required
def professional_earnings():

    # Only professionals can access this page
    if current_user.role != "professional":
        abort(403)

    # Get professional profile
    professional = ProfessionalProfile.query.filter_by(
        user_id=current_user.id
    ).first()

    if not professional:
        abort(404)

    # Get all bookings belonging to this professional
    bookings = (
        ServiceRequest.query
        .filter_by(
            professional_id=professional.id
        )
        .order_by(
            ServiceRequest.created_at.desc()
        )
        .all()
    )

    # --------------------------------------------------------
    # EARNINGS CALCULATIONS
    # --------------------------------------------------------

    total_earnings = sum(
        float(booking.payment_amount or 0)
        for booking in bookings
    )

    total_refunded = sum(
        float(booking.refund_amount or 0)
        for booking in bookings
    )

    net_earnings = total_earnings - total_refunded

    # Paid bookings
    paid_bookings = [
        booking
        for booking in bookings
        if booking.payment_status == "paid"
    ]

    paid_earnings = sum(
        float(booking.payment_amount or 0)
        for booking in paid_bookings
    )

    # Pending payments
    pending_bookings = [
        booking
        for booking in bookings
        if booking.payment_status == "pending"
    ]

    pending_earnings = sum(
        float(booking.payment_amount or 0)
        for booking in pending_bookings
    )

    # Refunded bookings
    refunded_bookings = [
        booking
        for booking in bookings
        if booking.refund_amount
        and float(booking.refund_amount) > 0
    ]

    # Completed bookings
    completed_bookings = [
        booking
        for booking in bookings
        if booking.status == "completed"
    ]

    # --------------------------------------------------------
    # MONTHLY EARNINGS
    # --------------------------------------------------------

    monthly_earnings = {}

    for booking in bookings:

        if not booking.payment_amount:
            continue

        if not booking.created_at:
            continue

        month_key = booking.created_at.strftime("%Y-%m")

        monthly_earnings[month_key] = (
            monthly_earnings.get(month_key, 0)
            + float(booking.payment_amount)
            - float(booking.refund_amount or 0)
        )

    monthly_labels = []
    monthly_values = []

    for month in sorted(monthly_earnings.keys()):

        try:
            month_date = datetime.strptime(
                month,
                "%Y-%m"
            )

            label = month_date.strftime("%b %Y")

        except ValueError:
            label = month

        monthly_labels.append(label)
        monthly_values.append(
            round(monthly_earnings[month], 2)
        )

    return render_template(
        "dashboard/professional_earnings.html",
        user=current_user,
        professional=professional,
        bookings=bookings,
        total_earnings=round(total_earnings, 2),
        total_refunded=round(total_refunded, 2),
        net_earnings=round(net_earnings, 2),
        paid_earnings=round(paid_earnings, 2),
        pending_earnings=round(pending_earnings, 2),
        paid_bookings=len(paid_bookings),
        pending_bookings=len(pending_bookings),
        refunded_bookings=len(refunded_bookings),
        completed_bookings=len(completed_bookings),
        monthly_labels=monthly_labels,
        monthly_values=monthly_values
    )
# ============================================================
# CUSTOMER NOTIFICATIONS
# ============================================================

@dashboard.route("/notifications")
@login_required
def notifications():

    if current_user.role not in ["user", "professional"]:
        abort(403)

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    return render_template(
        "dashboard/notifications.html",
        user=current_user,
        notifications=notifications
    )


@dashboard.route("/notifications/<int:notification_id>")
@login_required
def notification_click(notification_id):
    if current_user.role not in ["user", "professional"]:
        abort(403)

    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()

    if not notification:
        abort(404)

    notification.is_read = True
    db.session.commit()

    if notification.booking_id:

        if current_user.role == "professional":
            return redirect(
                url_for(
                    "dashboard.professional_booking_details",
                    request_id=notification.booking_id
                )
            )

        return redirect(
            url_for(
                "dashboard.booking_details",
                request_id=notification.booking_id
            )
        )

    return redirect(url_for("dashboard.notifications"))
from flask import current_app


@dashboard.route("/test-email")
@login_required
def test_email():

    send_email(
        recipient="ajaybabu0509@gmail.com",
        subject="AllYourHelp Email Test",
        body="This is a test email from AllYourHelp."
    )

    return "Test email attempted. Check the Flask terminal."
@dashboard.route(
    "/favorites/<int:professional_id>/add",
    methods=["POST"]
)
@login_required
def add_favorite(professional_id):

    if current_user.role != "user":
        abort(403)

    professional = ProfessionalProfile.query.get(
        professional_id
    )

    if not professional:
        abort(404)

    existing_favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        professional_id=professional.id
    ).first()

    if existing_favorite:
        flash(
            "This professional is already in your favorites.",
            "info"
        )
    else:

        favorite = Favorite(
            user_id=current_user.id,
            professional_id=professional.id
        )

        db.session.add(favorite)
        db.session.commit()

        flash(
            f"{professional.user.name} has been added to your favorites.",
            "success"
        )

    return redirect(
        request.referrer
        or url_for("dashboard.index")
    )
@dashboard.route(
    "/favorites/<int:professional_id>/remove",
    methods=["POST"]
)
@login_required
def remove_favorite(professional_id):

    if current_user.role != "user":
        abort(403)

    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        professional_id=professional_id
    ).first()

    if not favorite:
        flash(
            "This professional is not in your favorites.",
            "info"
        )
    else:

        db.session.delete(favorite)
        db.session.commit()

        flash(
            "Professional removed from your favorites.",
            "success"
        )

    return redirect(
        request.referrer
        or url_for("dashboard.index")
    )
@dashboard.route("/favorites")
@login_required
def favorites():

    if current_user.role != "user":
        abort(403)

    favorites = Favorite.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Favorite.created_at.desc()
    ).all()

    return render_template(
        "dashboard/favorites.html",
        user=current_user,
        favorites=favorites
    )
@dashboard.route(
    "/bookings/verify-payment",
    methods=["POST"]
)
@login_required
def verify_payment():

    pending_booking = session.get("pending_booking")

    if not pending_booking:
        return {
            "success": False,
            "message": "No pending booking found."
        }, 400

    settings = get_admin_settings()

    if not settings.bookings_enabled:
        session.pop("pending_booking", None)
        session.pop("razorpay_order_id", None)

        return {
            "success": False,
            "message": "Bookings are currently unavailable. Please try again later."
        }, 403

    if pending_booking.get("user_id") != current_user.id:
        session.pop("pending_booking", None)
        session.pop("razorpay_order_id", None)

        return {
            "success": False,
            "message": "Invalid booking information."
        }, 403

    razorpay_payment_id = request.form.get(
        "razorpay_payment_id"
    )

    razorpay_order_id = request.form.get(
        "razorpay_order_id"
    )

    razorpay_signature = request.form.get(
        "razorpay_signature"
    )

    if not all([
        razorpay_payment_id,
        razorpay_order_id,
        razorpay_signature
    ]):
        return {
            "success": False,
            "message": "Incomplete payment information."
        }, 400

    # --------------------------------------------------
    # Verify that the order belongs to our server session
    # --------------------------------------------------

    expected_order_id = session.get(
        "razorpay_order_id"
    )

    if not expected_order_id:
        return {
            "success": False,
            "message": "Payment order information is missing."
        }, 400

    if razorpay_order_id != expected_order_id:
        return {
            "success": False,
            "message": "Invalid payment order."
        }, 400

    # --------------------------------------------------
    # Razorpay client
    # --------------------------------------------------

    razorpay_client = razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"]
        )
    )

    # --------------------------------------------------
    # Verify Razorpay signature
    # --------------------------------------------------

    try:

        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })

    except razorpay.errors.SignatureVerificationError:

        return {
            "success": False,
            "message": "Payment verification failed."
        }, 400

    # --------------------------------------------------
    # Fetch payment from Razorpay
    # --------------------------------------------------

    try:

        razorpay_payment = razorpay_client.payment.fetch(
            razorpay_payment_id
        )

    except Exception:

        return {
            "success": False,
            "message": "Unable to verify payment status."
        }, 400

    # --------------------------------------------------
    # Verify payment belongs to the expected order
    # --------------------------------------------------

    if razorpay_payment.get("order_id") != expected_order_id:

        return {
            "success": False,
            "message": "Payment does not belong to this booking."
        }, 400

    # --------------------------------------------------
    # Verify payment amount
    # --------------------------------------------------

    service = Service.query.get(
        pending_booking.get("service_id")
    )

    professional = ProfessionalProfile.query.get(
        pending_booking.get("professional_id")
    )

    slot = AvailabilitySlot.query.get(
        pending_booking.get("slot_id")
    )

    if not service or not professional or not slot:

        return {
            "success": False,
            "message": "Booking information is no longer available."
        }, 400

    amount = service.price or 0

    expected_amount = int(
        float(amount) * 100
    )

    if razorpay_payment.get("amount") != expected_amount:

        return {
            "success": False,
            "message": "Payment amount does not match the booking amount."
        }, 400

    # --------------------------------------------------
    # Verify payment status
    # --------------------------------------------------

    if razorpay_payment.get("status") != "captured":

        return {
            "success": False,
            "message": "Payment has not been captured."
        }, 400

    # --------------------------------------------------
    # Prevent double booking
    # --------------------------------------------------

    if slot.is_booked:

        return {
            "success": False,
            "message": "This time slot has already been booked."
        }, 400

    # --------------------------------------------------
    # Create ServiceRequest
    # --------------------------------------------------

    service_request = ServiceRequest(
        user_id=current_user.id,
        professional_id=professional.id,
        service_id=service.id,
        preferred_date=slot.slot_date,
        preferred_time=slot.start_time,
        availability_slot_id=slot.id,
        slot_id=slot.id,
        description=pending_booking.get(
            "description",
            ""
        ),
        location=pending_booking.get(
            "location"
        ),
        additional_details=pending_booking.get(
            "additional_details"
        ),
        status="confirmed",
        payment_status="paid",
        payment_id=razorpay_payment_id,
        payment_amount=amount,
        refund_status="not_required"
    )

    db.session.add(service_request)

    # We need the ServiceRequest ID before creating Payment
    db.session.flush()

    # --------------------------------------------------
    # Mark slot as booked
    # --------------------------------------------------

    slot.is_booked = True

    # --------------------------------------------------
    # Create Payment record
    # --------------------------------------------------

    payment = Payment(
        service_request_id=service_request.id,
        user_id=current_user.id,
        professional_id=professional.id,
        amount=amount,
        currency="INR",
        status="paid",
        gateway="razorpay",
        gateway_order_id=razorpay_order_id,
        gateway_payment_id=razorpay_payment_id,
        gateway_signature=razorpay_signature,
        paid_at=datetime.utcnow()
    )

    db.session.add(payment)

    # --------------------------------------------------
    # Save everything
    # --------------------------------------------------

    try:

        db.session.commit()

    except Exception:

        db.session.rollback()

        return {
            "success": False,
            "message": "Payment was verified, but the booking could not be saved."
        }, 500

    # --------------------------------------------------
    # Clear temporary booking information
    # --------------------------------------------------

    session.pop(
        "pending_booking",
        None
    )

    session.pop(
        "razorpay_order_id",
        None
    )

    # --------------------------------------------------
    # Success
    # --------------------------------------------------

    return {
        "success": True,
        "message": "Payment verified and booking confirmed.",
        "redirect_url": url_for(
            "services.booking_success",
            request_id=service_request.id
        )
    }
@dashboard.route(
    "/bookings/payment-failed",
    methods=["POST"]
)
@login_required
def payment_failed():

    pending_booking = session.get("pending_booking")

    if not pending_booking:
        return {
            "success": False,
            "message": "No pending booking found."
        }, 400

    if pending_booking.get("user_id") != current_user.id:
        return {
            "success": False,
            "message": "Invalid booking information."
        }, 403

    razorpay_order_id = request.form.get(
        "razorpay_order_id"
    )

    razorpay_payment_id = request.form.get(
        "razorpay_payment_id"
    )

    error_description = request.form.get(
        "error_description"
    )

    # Verify that this failure belongs to the
    # Razorpay order created for the current session.
    expected_order_id = session.get(
        "razorpay_order_id"
    )

    if not expected_order_id:
        return {
            "success": False,
            "message": "Payment session has expired. Please try again."
        }, 400

    if razorpay_order_id != expected_order_id:
        return {
            "success": False,
            "message": "Invalid payment order."
        }, 400

    if not razorpay_order_id:
        return {
            "success": False,
            "message": "Payment order information is missing."
        }, 400

    service = Service.query.get(
        pending_booking.get("service_id")
    )

    professional = ProfessionalProfile.query.get(
        pending_booking.get("professional_id")
    )

    if not service or not professional:
        return {
            "success": False,
            "message": "Booking information is no longer available."
        }, 400

    amount = service.price or 0

    # Prevent duplicate failure records
    existing_payment = Payment.query.filter_by(
        gateway_order_id=razorpay_order_id
    ).first()

    if existing_payment:
        return {
            "success": True,
            "message": "Payment failure was already recorded."
        }

    payment = Payment(
        service_request_id=None,
        user_id=current_user.id,
        professional_id=professional.id,
        amount=amount,
        currency="INR",
        status="failed",
        gateway="razorpay",
        gateway_order_id=razorpay_order_id,
        gateway_payment_id=razorpay_payment_id,
        failure_reason=error_description
    )

    db.session.add(payment)

    try:

        db.session.commit()

    except Exception:
        db.session.rollback()

        return {
            "success": False,
            "message": "Failed to record payment information."
        }, 500
    return {
        "success": True,
        "message": "Payment failure recorded."
    }