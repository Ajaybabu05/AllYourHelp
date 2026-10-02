from flask import (
    Blueprint,
    render_template,
    abort,
    request,
    redirect,
    url_for,
    flash,
    session
)

from flask_login import login_required, current_user

from datetime import datetime, time

from ..extensions import db
from sqlalchemy import func

from ..models.review import Review
from ..models import Favorite
from ..models.service_category import ServiceCategory
from ..models.service import Service
from ..models.service_request import ServiceRequest
from ..models.professional_profile import ProfessionalProfile
from ..models.availability_slot import AvailabilitySlot
from ..models.payment import Payment

services = Blueprint(
    "services",
    __name__,
    url_prefix="/services"
)


@services.route("/<slug>")
@login_required
def category_services(slug):

    category = ServiceCategory.query.filter_by(
        slug=slug,
        is_active=True
    ).first()

    if not category:
        abort(404)

    active_services = [
        service
        for service in category.services
        if service.is_active
    ]

    return render_template(
        "services/category.html",
        category=category,
        services=active_services
    )


@services.route("/service/<slug>/professionals")
@login_required
def service_professionals(slug):

    service = Service.query.filter_by(
        slug=slug,
        is_active=True
    ).first()

    if not service:
        abort(404)

    professionals = [
        professional
        for professional in service.professionals
        if professional.user.is_active
        and professional.is_verified
    ]

    return render_template(
        "services/professionals.html",
        service=service,
        professionals=professionals
    )


@services.route("/professional/<int:professional_id>")
@login_required
def professional_profile(professional_id):

    professional = ProfessionalProfile.query.get(
        professional_id
    )

    if not professional:
        abort(404)

    if not professional.is_verified:
        abort(404)

    if not professional.user.is_active:
        abort(404)

    service_slug = request.args.get("service")

    # Get all reviews for this professional
    reviews = Review.query.filter_by(
        professional_id=professional.id
    ).order_by(
        Review.created_at.desc()
    ).all()

    # Calculate average rating
    average_rating = db.session.query(
        func.avg(Review.rating)
    ).filter(
        Review.professional_id == professional.id
    ).scalar()

    # Number of reviews
    review_count = len(reviews)

    # Use 0 when the professional has no reviews
    average_rating = float(average_rating) if average_rating else 0.0
    # Check whether the current customer has
    # already added this professional to favorites

    favorite = None

    if current_user.role == "user":

        favorite = Favorite.query.filter_by(
            user_id=current_user.id,
            professional_id=professional.id
        ).first()

    return render_template(
        "services/professional_profile.html",
        professional=professional,
        service_slug=service_slug,
        reviews=reviews,
        average_rating=average_rating,
        review_count=review_count,
        favorite=favorite
    )

@services.route(
    "/professional/<int:professional_id>/request",
    methods=["GET", "POST"]
)
@login_required
def request_service(professional_id):

    professional = ProfessionalProfile.query.get(professional_id)

    if not professional:
        abort(404)

    if not professional.is_verified:
        abort(404)

    if not professional.user.is_active:
        abort(404)

    # Available slots
    available_slots = AvailabilitySlot.query.filter(
        AvailabilitySlot.professional_id == professional.id,
        AvailabilitySlot.is_booked == False,
        AvailabilitySlot.slot_date >= datetime.utcnow().date()
    ).order_by(
        AvailabilitySlot.slot_date,
        AvailabilitySlot.start_time
    ).all()

    # GET
    if request.method == "GET":

        return render_template(
            "services/request_service.html",
            professional=professional,
            available_slots=available_slots
        )

    # POST
    service_id = request.form.get("service_id")
    slot_id = request.form.get("slot_id")

    description = request.form.get(
        "description",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    additional_details = request.form.get(
        "additional_details",
        ""
    ).strip()

    # -----------------------------
    # VALIDATION
    # -----------------------------

    if not service_id or not slot_id or not description:

        flash(
            "Please select a service, available slot and provide your requirement.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # Get service
    service = Service.query.get(service_id)

    if not service:

        flash(
            "Invalid service selected.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # Make sure professional provides service
    if service not in professional.services:

        flash(
            "This professional does not provide this service.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # Get slot
    slot = AvailabilitySlot.query.filter_by(
        id=slot_id,
        professional_id=professional.id
    ).first()

    if not slot:

        flash(
            "Invalid availability slot.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # Check if already booked
    if slot.is_booked:

        flash(
            "Sorry, this slot has already been booked. Please select another slot.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # Check date
    today = datetime.utcnow().date()

    if slot.slot_date < today:

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

    # ------------------------------------
    # DO NOT CREATE SERVICE REQUEST HERE
    # ------------------------------------

    return render_template(
        "services/review_booking.html",

        professional=professional,

        service=service,

        slot=slot,

        description=description,

        location=location,

        additional_details=additional_details
    )

@services.route("/booking/review")
@login_required
def review_booking():

    from flask import session

    booking_data = session.get("booking_data")

    if not booking_data:

        flash(
            "Your booking session has expired. Please start again.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.user_dashboard"
            )
        )

    professional = ProfessionalProfile.query.get(
        booking_data["professional_id"]
    )

    service = Service.query.get(
        booking_data["service_id"]
    )

    slot = AvailabilitySlot.query.filter_by(
        id=booking_data["slot_id"],
        professional_id=booking_data["professional_id"]
    ).first()

    # Validate everything still exists

    if not professional or not service or not slot:

        session.pop("booking_data", None)

        flash(
            "The selected booking information is no longer available.",
            "error"
        )

        return redirect(
            url_for(
                "dashboard.user_dashboard"
            )
        )

    # Check slot again

    if slot.is_booked:

        session.pop("booking_data", None)

        flash(
            "Sorry, this slot has already been booked. Please select another slot.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # Check date again

    if slot.slot_date < datetime.utcnow().date():

        session.pop("booking_data", None)

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

    return render_template(
        "services/review_booking.html",
        professional=professional,
        service=service,
        slot=slot,
        booking_data=booking_data
    )
@services.route(
    "/professional/<int:professional_id>/confirm-booking",
    methods=["POST"]
)
@login_required
def confirm_booking(professional_id):

    professional = ProfessionalProfile.query.get(
        professional_id
    )

    if not professional:
        abort(404)

    if not professional.is_verified:
        abort(404)

    if not professional.user.is_active:
        abort(404)

    # --------------------------------
    # GET SUBMITTED VALUES
    # --------------------------------

    service_id = request.form.get("service_id")
    slot_id = request.form.get("slot_id")

    description = request.form.get(
        "description",
        ""
    ).strip()

    location = request.form.get(
        "location",
        ""
    ).strip()

    additional_details = request.form.get(
        "additional_details",
        ""
    ).strip()

    # --------------------------------
    # VALIDATE REQUIRED INFORMATION
    # --------------------------------

    if not service_id or not slot_id or not description:

        flash(
            "Invalid booking information.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # --------------------------------
    # GET SERVICE
    # --------------------------------

    service = Service.query.get(service_id)

    if not service:

        flash(
            "Invalid service selected.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # --------------------------------
    # MAKE SURE PROFESSIONAL PROVIDES SERVICE
    # --------------------------------

    if service not in professional.services:

        flash(
            "This professional does not provide this service.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # --------------------------------
    # GET SLOT
    # --------------------------------

    slot = AvailabilitySlot.query.filter_by(
        id=slot_id,
        professional_id=professional.id
    ).first()

    if not slot:

        flash(
            "Invalid availability slot.",
            "error"
        )

        return redirect(
            url_for(
                "services.request_service",
                professional_id=professional.id
            )
        )

    # --------------------------------
    # CHECK SLOT AVAILABILITY
    # --------------------------------

    if slot.is_booked:

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
    # STORE PENDING BOOKING IN SESSION
    # --------------------------------

    session["pending_booking"] = {

        "user_id": current_user.id,

        "professional_id": professional.id,

        "service_id": service.id,

        "slot_id": slot.id,

        "description": description,

        "location": location,

        "additional_details": additional_details
    }

    # --------------------------------
    # REDIRECT TO PAYMENT
    # --------------------------------

    return redirect(
        url_for(
            "dashboard.booking_payment"
        )
    )
@services.route("/booking-success/<int:request_id>")
@login_required
def booking_success(request_id):

    service_request = ServiceRequest.query.filter_by(
        id=request_id,
        user_id=current_user.id
    ).first()

    if not service_request:
        abort(404)

    return render_template(
        "services/booking_success.html",
        service_request=service_request
    )