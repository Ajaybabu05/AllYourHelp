from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    abort,
    flash,
    request
)
from flask_login import login_required, current_user
from datetime import datetime
from collections import defaultdict
from ..extensions import db
from ..models.professional_service_request import ProfessionalServiceRequest
from ..models.user import User
from ..models.professional_profile import ProfessionalProfile
from ..models.service import Service
from ..models.service_category import ServiceCategory
from ..models.service_request import ServiceRequest
from app.models.notification import Notification
from ..models import Review
from ..models.admin_activity_log import AdminActivityLog
from app.routes.dashboard import create_notification
from ..utils.admin_activity import log_admin_activity

# ============================================================
# ADMIN BLUEPRINT
# ============================================================

admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

@admin.route("/")
@login_required
def dashboard():

    if current_user.role != "admin":
        abort(403)

    log_admin_activity(
        action="view_dashboard",
        description="Admin viewed the admin dashboard",
        target_type="dashboard"
    )

    # Existing statistics
    total_users = User.query.filter_by(
        role="user"
    ).count()

    total_professionals = User.query.filter_by(
        role="professional"
    ).count()

    total_services = Service.query.filter_by(
        is_active=True
    ).count()

    pending_service_requests = ProfessionalServiceRequest.query.filter_by(
        status="pending"
    ).count()

    verified_professionals = ProfessionalProfile.query.filter_by(
        is_verified=True
    ).count()

    # Booking statistics
    total_bookings = ServiceRequest.query.count()

    pending_bookings = ServiceRequest.query.filter_by(
        status="pending"
    ).count()

    confirmed_bookings = ServiceRequest.query.filter_by(
        status="confirmed"
    ).count()

    completed_bookings = ServiceRequest.query.filter_by(
        status="completed"
    ).count()

    rejected_bookings = ServiceRequest.query.filter_by(
        status="rejected"
    ).count()

    unread_notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).count()

    # Revenue statistics
    paid_bookings = ServiceRequest.query.filter_by(
        payment_status="paid"
    ).all()

    refunded_bookings = ServiceRequest.query.filter_by(
        payment_status="refunded"
    ).all()

    total_revenue = sum(
        float(booking.payment_amount or 0)
        for booking in paid_bookings
    )

    total_refunded = sum(
        float(booking.refund_amount or 0)
        for booking in refunded_bookings
    )

    net_revenue = total_revenue - total_refunded

    booking_chart_labels = [
        "Pending",
        "Confirmed",
        "Completed",
        "Rejected"
    ]

    booking_chart_values = [
        pending_bookings,
        confirmed_bookings,
        completed_bookings,
        rejected_bookings
    ]

    revenue_chart_labels = [
        "Revenue",
        "Refunded",
        "Net Revenue"
    ]

    revenue_chart_values = [
        total_revenue,
        total_refunded,
        net_revenue
    ]
    booking_chart_data = [
        {
            "status": "Pending",
            "count": pending_bookings
        },
        {
            "status": "Confirmed",
            "count": confirmed_bookings
        },
        {
            "status": "Completed",
            "count": completed_bookings
        },
        {
            "status": "Rejected",
            "count": rejected_bookings
        }
    ]

    revenue_chart_data = [
        {
            "type": "Revenue",
            "amount": total_revenue
        },
        {
            "type": "Refunded",
            "amount": total_refunded
        },
        {
            "type": "Net Revenue",
            "amount": net_revenue
        }
    ]

    return render_template(
        "admin/dashboard.html",

        total_users=total_users,
        total_professionals=total_professionals,
        total_services=total_services,
        pending_service_requests=pending_service_requests,
        verified_professionals=verified_professionals,

        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        confirmed_bookings=confirmed_bookings,
        completed_bookings=completed_bookings,
        rejected_bookings=rejected_bookings,

        total_revenue=total_revenue,
        total_refunded=total_refunded,
        net_revenue=net_revenue,
        booking_chart_data=booking_chart_data,
        revenue_chart_data=revenue_chart_data,
        booking_chart_labels=booking_chart_labels,
        booking_chart_values=booking_chart_values,
        revenue_chart_labels=revenue_chart_labels,
        revenue_chart_values=revenue_chart_values,
        unread_notifications=unread_notifications
        )

@admin.route("/activity-logs")
@login_required
def activity_logs():

    if current_user.role != "admin":
        abort(403)

    # Get filter values
    action = request.args.get("action", "").strip()
    target_type = request.args.get("target_type", "").strip()
    admin_id = request.args.get("admin_id", "").strip()
    search = request.args.get("search", "").strip()
    start_date = request.args.get("start_date", "").strip()
    end_date = request.args.get("end_date", "").strip()

    # Base query
    query = AdminActivityLog.query

    # Filter by action
    if action:
        query = query.filter(
            AdminActivityLog.action == action
        )

    # Filter by target type
    if target_type:
        query = query.filter(
            AdminActivityLog.target_type == target_type
        )

    # Filter by admin
    if admin_id:
        try:
            query = query.filter(
                AdminActivityLog.admin_id == int(admin_id)
            )
        except ValueError:
            pass

    # Search description
    if search:
        query = query.filter(
            AdminActivityLog.description.ilike(
                f"%{search}%"
            )
        )

    # Filter by start date
    if start_date:
        try:
            start_date_obj = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            )

            query = query.filter(
                AdminActivityLog.created_at >= start_date_obj
            )

        except ValueError:
            pass

    # Filter by end date
    if end_date:
        try:
            end_date_obj = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            )

            # Include the entire selected end date
            from datetime import timedelta

            end_date_obj = end_date_obj + timedelta(days=1)

            query = query.filter(
                AdminActivityLog.created_at < end_date_obj
            )

        except ValueError:
            pass

    # Pagination
    page = request.args.get("page", 1, type=int)

    pagination = query.order_by(
        AdminActivityLog.created_at.desc()
    ).paginate(
        page=page,
        per_page=20,
        error_out=False
    )

    logs = pagination.items

    # Dropdown options
    actions = db.session.query(
        AdminActivityLog.action
    ).distinct().order_by(
        AdminActivityLog.action
    ).all()

    target_types = db.session.query(
        AdminActivityLog.target_type
    ).filter(
        AdminActivityLog.target_type.isnot(None)
    ).distinct().order_by(
        AdminActivityLog.target_type
    ).all()

    admins = User.query.filter_by(
        role="admin"
    ).order_by(
        User.name
    ).all()

    return render_template(
        "admin/activity_logs.html",
        logs=logs,
        pagination=pagination,
        actions=[item[0] for item in actions],
        target_types=[item[0] for item in target_types],
        admins=admins,
        selected_action=action,
        selected_target_type=target_type,
        selected_admin_id=admin_id,
        search=search,
        start_date=start_date,
        end_date=end_date
    )

@admin.route("/users")
@login_required
def users():

    if current_user.role != "admin":
        abort(403)

    users = User.query.order_by(
        User.created_at.desc()
    ).all()

    return render_template(
        "admin/users.html",
        users=users
    )

@admin.route("/professionals")
@login_required
def professionals():

    if current_user.role != "admin":
        abort(403)

    professionals = ProfessionalProfile.query.join(
        User,
        ProfessionalProfile.user_id == User.id
    ).order_by(
        User.created_at.desc()
    ).all()

    # ---------------------------------------
    # PROFESSIONAL PERFORMANCE
    # ---------------------------------------

    performance = {}

    for professional in professionals:

        # Get all bookings for this professional
        bookings = ServiceRequest.query.filter_by(
            professional_id=professional.id
        ).all()

        total_bookings = len(bookings)

        completed_bookings = sum(
            1
            for booking in bookings
            if booking.status == "completed"
        )

        cancelled_bookings = sum(
            1
            for booking in bookings
            if booking.status == "cancelled"
        )

        pending_bookings = sum(
            1
            for booking in bookings
            if booking.status == "pending"
        )

        confirmed_bookings = sum(
            1
            for booking in bookings
            if booking.status == "confirmed"
        )

        # -----------------------------------
        # REVENUE
        # -----------------------------------

        total_revenue = sum(
            booking.payment_amount or 0
            for booking in bookings
            if booking.payment_status == "paid"
        )

        refunded_amount = sum(
            booking.refund_amount or 0
            for booking in bookings
            if booking.refund_status == "refunded"
        )

        # -----------------------------------
        # REVIEWS
        # -----------------------------------

        reviews = Review.query.filter_by(
            professional_id=professional.id
        ).all()

        total_reviews = len(reviews)

        average_rating = (
            sum(review.rating for review in reviews)
            / total_reviews
            if total_reviews > 0
            else 0
        )

        performance[professional.id] = {
            "total_bookings": total_bookings,
            "completed_bookings": completed_bookings,
            "cancelled_bookings": cancelled_bookings,
            "pending_bookings": pending_bookings,
            "confirmed_bookings": confirmed_bookings,
            "total_revenue": total_revenue,
            "refunded_amount": refunded_amount,
            "total_reviews": total_reviews,
            "average_rating": average_rating
        }

    return render_template(
        "admin/professionals.html",
        professionals=professionals,
        performance=performance
    )

@admin.route(
    "/professionals/<int:professional_id>/toggle-verification",
    methods=["POST"]
)
@login_required
def toggle_professional_verification(professional_id):

    if current_user.role != "admin":
        abort(403)

    professional = ProfessionalProfile.query.get(
        professional_id
    )

    if not professional:
        abort(404)

    professional.is_verified = not professional.is_verified

    db.session.commit()

    # Log the admin action
    if professional.is_verified:

        log_admin_activity(
            action="verify_professional",
            description=(
                f"Admin verified professional "
                f"{professional.user.name} "
                f"(User ID: {professional.user.id}, "
                f"Profile ID: {professional.id})."
            ),
            target_type="professional",
            target_id=professional.id
        )

        flash(
            f"{professional.user.name} has been verified successfully.",
            "success"
        )

    else:

        log_admin_activity(
            action="unverify_professional",
            description=(
                f"Admin removed verification from professional "
                f"{professional.user.name} "
                f"(User ID: {professional.user.id}, "
                f"Profile ID: {professional.id})."
            ),
            target_type="professional",
            target_id=professional.id
        )

        flash(
            f"{professional.user.name} is no longer verified.",
            "success"
        )

    return redirect(
        url_for("admin.professionals")
    )

@admin.route("/categories")
@login_required
def categories():

    if current_user.role != "admin":
        abort(403)

    categories = ServiceCategory.query.order_by(
        ServiceCategory.name.asc()
    ).all()

    return render_template(
        "admin/categories.html",
        categories=categories
    )

@admin.route("/categories/create", methods=["GET", "POST"])
@login_required
def create_category():

    if current_user.role != "admin":
        abort(403)

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        description = request.form.get(
            "description",
            ""
        ).strip()

        if not name:
            flash(
                "Category name is required.",
                "error"
            )
            return redirect(
                url_for("admin.create_category")
            )

        if not slug:
            flash(
                "Category slug is required.",
                "error"
            )
            return redirect(
                url_for("admin.create_category")
            )

        existing_category = ServiceCategory.query.filter(
            ServiceCategory.slug == slug
        ).first()

        if existing_category:

            flash(
                "A category with this slug already exists.",
                "error"
            )

            return redirect(
                url_for("admin.create_category")
            )

        category = ServiceCategory(
            name=name,
            slug=slug,
            description=description if description else None,
            is_active=True
        )

        db.session.add(category)
        db.session.commit()

        # Log the admin action
        log_admin_activity(
            action="create_category",
            description=(
                f"Admin created service category "
                f"'{category.name}' (ID: {category.id})."
            ),
            target_type="category",
            target_id=category.id
        )

        flash(
            f"{category.name} category has been created.",
            "success"
        )

        return redirect(
            url_for("admin.categories")
        )

    return render_template(
        "admin/create_category.html"
    )

@admin.route(
    "/categories/<int:category_id>/edit",
    methods=["GET", "POST"]
)
@login_required
def edit_category(category_id):

    if current_user.role != "admin":
        abort(403)

    category = ServiceCategory.query.get(
        category_id
    )

    if not category:
        abort(404)

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        slug = request.form.get(
            "slug",
            ""
        ).strip().lower()

        description = request.form.get(
            "description",
            ""
        ).strip()

        if not name:

            flash(
                "Category name is required.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_category",
                    category_id=category.id
                )
            )

        if not slug:

            flash(
                "Category slug is required.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_category",
                    category_id=category.id
                )
            )

        existing_category = ServiceCategory.query.filter(
            ServiceCategory.slug == slug,
            ServiceCategory.id != category.id
        ).first()

        if existing_category:

            flash(
                "Another category already uses this slug.",
                "error"
            )

            return redirect(
                url_for(
                    "admin.edit_category",
                    category_id=category.id
                )
            )

        category.name = name
        category.slug = slug
        category.description = (
            description
            if description
            else None
        )

        db.session.commit()

        # Log the admin action
        log_admin_activity(
            action="edit_category",
            description=(
                f"Admin edited service category "
                f"'{category.name}' (ID: {category.id})."
            ),
            target_type="category",
            target_id=category.id
        )

        flash(
            f"{category.name} has been updated.",
            "success"
        )

        return redirect(
            url_for("admin.categories")
        )

    return render_template(
        "admin/edit_category.html",
        category=category
    )

@admin.route(
    "/categories/<int:category_id>/toggle-status",
    methods=["POST"]
)
@login_required
def toggle_category_status(category_id):

    if current_user.role != "admin":
        abort(403)

    category = ServiceCategory.query.get(
        category_id
    )

    if not category:
        abort(404)

    category.is_active = not category.is_active

    db.session.commit()

    # Log the admin action
    if category.is_active:
        log_admin_activity(
            action="activate_category",
            description=(
                f"Admin activated category "
                f"'{category.name}' (ID: {category.id})."
            ),
            target_type="category",
            target_id=category.id
        )
    else:
        log_admin_activity(
            action="deactivate_category",
            description=(
                f"Admin deactivated category "
                f"'{category.name}' (ID: {category.id})."
            ),
            target_type="service",
            target_id=category.id
        )

    if category.is_active:

        flash(
            f"{category.name} has been activated.",
            "success"
        )

    else:

        flash(
            f"{category.name} has been deactivated.",
            "success"
        )

    return redirect(
        url_for("admin.categories")
    )

@admin.route(
    "/users/<int:user_id>/toggle-status",
    methods=["POST"]
)
@login_required
def toggle_user_status(user_id):

    if current_user.role != "admin":
        abort(403)

    user = User.query.get(user_id)

    if not user:
        abort(404)

    # Prevent an admin from disabling their own account
    if user.id == current_user.id:
        flash(
            "You cannot deactivate your own admin account.",
            "error"
        )
        return redirect(url_for("admin.users"))

    user.is_active = not user.is_active

    db.session.commit()

    # Log the admin action
    if user.is_active:
        log_admin_activity(
            action="activate_user",
            description=(
                f"Admin activated the account of user "
                f"{user.name} (ID: {user.id})."
            ),
            target_type="user",
            target_id=user.id
        )

        flash(
            f"{user.name}'s account has been activated.",
            "success"
        )

    else:
        log_admin_activity(
            action="deactivate_user",
            description=(
                f"Admin deactivated the account of user "
                f"{user.name} (ID: {user.id})."
            ),
            target_type="user",
            target_id=user.id
        )

        flash(
            f"{user.name}'s account has been deactivated.",
            "success"
        )
    return redirect(url_for("admin.users"))

@admin.route("/services")
@login_required
def services():

    if current_user.role != "admin":
        abort(403)

    services = Service.query.order_by(
        Service.name.asc()
    ).all()

    return render_template(
        "admin/services.html",
        services=services
    )

@admin.route("/services/create", methods=["GET", "POST"])
@login_required
def create_service():

    if current_user.role != "admin":
        abort(403)

    categories = ServiceCategory.query.filter_by(
        is_active=True
    ).order_by(
        ServiceCategory.name.asc()
    ).all()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "").strip()
        category_id = request.form.get("category_id", type=int)

        if not name or not slug or not category_id:
            flash(
                "Please fill in all required fields.",
                "error"
            )
            return redirect(
                url_for("admin.create_service")
            )

        existing_service = Service.query.filter_by(
            slug=slug
        ).first()

        if existing_service:
            flash(
                "A service with this slug already exists.",
                "error"
            )
            return redirect(
                url_for("admin.create_service")
            )

        category = ServiceCategory.query.filter_by(
            id=category_id,
            is_active=True
        ).first()

        if not category:
            flash(
                "Please select a valid active category.",
                "error"
            )
            return redirect(
                url_for("admin.create_service")
            )

        try:
            service_price = float(price)

            if service_price < 0:
                raise ValueError

        except (ValueError, TypeError):
            flash(
                "Please enter a valid price.",
                "error"
            )
            return redirect(
                url_for("admin.create_service")
            )

        service = Service(
            category_id=category.id,
            name=name,
            slug=slug,
            description=description if description else None,
            price=service_price,
            is_active=True
        )

        db.session.add(service)
        db.session.commit()

        # Log the admin action
        log_admin_activity(
            action="create_service",
            description=(
                f"Admin created service "
                f"'{service.name}' (ID: {service.id})."
            ),
            target_type="service",
            target_id=service.id
        )

        flash(
            f"{service.name} has been created.",
            "success"
        )

        return redirect(
            url_for("admin.services")
        )

    return render_template(
        "admin/create_service.html",
        categories=categories
    )

@admin.route("/services/<int:service_id>/edit", methods=["GET", "POST"])
@login_required
def edit_service(service_id):

    if current_user.role != "admin":
        abort(403)

    service = Service.query.get(service_id)

    if not service:
        abort(404)

    categories = ServiceCategory.query.filter_by(
        is_active=True
    ).order_by(
        ServiceCategory.name.asc()
    ).all()

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        slug = request.form.get("slug", "").strip().lower()
        description = request.form.get("description", "").strip()
        price = request.form.get("price", "").strip()
        category_id = request.form.get("category_id", type=int)

        if not name or not slug or not category_id:
            flash(
                "Please fill in all required fields.",
                "error"
            )
            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        existing_service = Service.query.filter(
            Service.slug == slug,
            Service.id != service.id
        ).first()

        if existing_service:
            flash(
                "Another service with this slug already exists.",
                "error"
            )
            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        category = ServiceCategory.query.filter_by(
            id=category_id,
            is_active=True
        ).first()

        if not category:
            flash(
                "Please select a valid active category.",
                "error"
            )
            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        try:
            service_price = float(price)

            if service_price < 0:
                raise ValueError

        except (ValueError, TypeError):
            flash(
                "Please enter a valid price.",
                "error"
            )
            return redirect(
                url_for(
                    "admin.edit_service",
                    service_id=service.id
                )
            )

        service.name = name
        service.slug = slug
        service.description = description if description else None
        service.price = service_price
        service.category_id = category.id

        db.session.commit()

        # Log the admin action
        log_admin_activity(
            action="edit_service",
            description=(
                f"Admin edited service "
                f"'{service.name}' (ID: {service.id})."
            ),
            target_type="service",
            target_id=service.id
        )

        flash(
            f"{service.name} has been updated.",
            "success"
        )

        return redirect(
            url_for("admin.services")
        )

    return render_template(
        "admin/edit_service.html",
        service=service,
        categories=categories
    )

@admin.route(
    "/services/<int:service_id>/toggle-status",
    methods=["POST"]
)
@login_required
def toggle_service_status(service_id):

    if current_user.role != "admin":
        abort(403)

    service = Service.query.get(service_id)

    if not service:
        abort(404)

    service.is_active = not service.is_active

    db.session.commit()

    # Log the admin action
    if service.is_active:
        log_admin_activity(
            action="activate_service",
            description=(
                f"Admin activated service "
                f"'{service.name}' (ID: {service.id})."
            ),
            target_type="service",
            target_id=service.id
        )
    else:
        log_admin_activity(
            action="deactivate_service",
            description=(
                f"Admin deactivated service "
                f"'{service.name}' (ID: {service.id})."
            ),
            target_type="service",
            target_id=service.id
        )

    if service.is_active:
        flash(
            f"{service.name} has been activated successfully.",
            "success"
        )
    else:
        flash(
            f"{service.name} has been deactivated successfully.",
            "success"
        )

    return redirect(
        url_for("admin.services")
    )


# ============================================================
# VIEW PENDING SERVICE REQUESTS
# ============================================================

@admin.route("/service-requests")
@login_required
def service_requests():

    if current_user.role != "admin":
        abort(403)

    requests = ProfessionalServiceRequest.query.filter_by(
        status="pending"
    ).order_by(
        ProfessionalServiceRequest.created_at.asc()
    ).all()

    return render_template(
        "admin/service_requests.html",
        requests=requests
    )

@admin.route("/service-requests/<int:request_id>")
@login_required
def service_request_details(request_id):

    if current_user.role != "admin":
        abort(403)

    service_request = ProfessionalServiceRequest.query.get(
        request_id
    )

    if not service_request:
        abort(404)

    return render_template(
        "admin/service_request_details.html",
        service_request=service_request
    )


# ============================================================
# APPROVE SERVICE REQUEST
# ============================================================

@admin.route(
    "/service-requests/<int:request_id>/approve",
    methods=["POST"]
)
@login_required
def approve_service_request(request_id):

    # Only administrators are allowed
    if current_user.role != "admin":
        abort(403)

    service_request = ProfessionalServiceRequest.query.get(
        request_id
    )

    if not service_request:
        abort(404)

    # Request must still be pending
    if service_request.status != "pending":

        flash(
            "This service request has already been processed.",
            "error"
        )

        return redirect(
            url_for("admin.service_requests")
        )

    professional = service_request.professional
    service = service_request.service

    if not professional or not service:

        flash(
            "The professional or service associated with this request no longer exists.",
            "error"
        )

        return redirect(
            url_for("admin.service_requests")
        )

    # Service must still be active
    if not service.is_active:

        service_request.status = "rejected"

        db.session.commit()

        flash(
            "This service is no longer active and cannot be approved.",
            "error"
        )

        return redirect(
            url_for("admin.service_requests")
        )

    # Add the service to the professional's approved services
    if service not in professional.services:

        professional.services.append(service)

    # Mark request as approved
    service_request.status = "approved"
    db.session.commit()
    # Log the admin action
    log_admin_activity(
        action="approve_service_request",
        description=(
            f"Admin approved service request "
            f"(Request ID: {service_request.id}) "
            f"for professional "
            f"{service_request.professional.user.name} "
            f"and service "
            f"'{service_request.service.name}'."
        ),
        target_type="service_request",
        target_id=service_request.id
    )

    create_notification(
        user_id=professional.user_id,
        title="Service Request Approved",
        message=(
            f"Your request to offer the {service.name} service "
            "has been approved by the AllYourHelp admin."
        ),
        notification_type="service_request_approved",
        professional_service_request_id=service_request.id
    )

    flash(
        f"{service.name} has been approved for "
        f"{professional.user.name}.",
        "success"
    )

    return redirect(
        url_for("admin.service_requests")
    )


# ============================================================
# REJECT SERVICE REQUEST
# ============================================================

@admin.route(
    "/service-requests/<int:request_id>/reject",
    methods=["POST"]
)
@login_required
def reject_service_request(request_id):

    # Only administrators are allowed
    if current_user.role != "admin":
        abort(403)

    service_request = ProfessionalServiceRequest.query.get(
        request_id
    )

    if not service_request:
        abort(404)

    # Request must still be pending
    if service_request.status != "pending":

        flash(
            "This service request has already been processed.",
            "error"
        )

        return redirect(
            url_for("admin.service_requests")
        )

    service = service_request.service

    # Mark request as rejected
    service_request.status = "rejected"
    db.session.commit()
    # Log the admin action
    log_admin_activity(
        action="reject_service_request",
        description=(
            f"Admin rejected service request "
            f"(Request ID: {service_request.id}) "
            f"for professional "
            f"{service_request.professional.user.name} "
            f"and service "
            f"'{service_request.service.name}'."
        ),
        target_type="service_request",
        target_id=service_request.id
    )

    if service_request.professional:
        create_notification(
            user_id=service_request.professional.user_id,
            title="Service Request Rejected",
            message=(
                f"Your request to offer the {service.name} service "
                "has been rejected by the AllYourHelp admin."
            ),
            notification_type="service_request_rejected",
            professional_service_request_id=service_request.id
        )

    if service:

        flash(
            f"{service.name} service request has been rejected.",
            "success"
        )

    else:

        flash(
            "The service request has been rejected.",
            "success"
        )

    return redirect(
        url_for("admin.service_requests")
    )
@admin.route("/bookings")
@login_required
def bookings():

    if current_user.role != "admin":
        abort(403)

    # --------------------------------
    # GET FILTER VALUES
    # --------------------------------

    status_filter = request.args.get(
        "status",
        "all"
    ).lower()

    search = request.args.get(
        "search",
        ""
    ).strip()

    payment_status = request.args.get(
        "payment_status",
        "all"
    ).lower()

    date_from = request.args.get(
        "date_from",
        ""
    ).strip()

    date_to = request.args.get(
        "date_to",
        ""
    ).strip()


    # --------------------------------
    # BASE QUERY
    # --------------------------------

    query = ServiceRequest.query


    # --------------------------------
    # BOOKING STATUS FILTER
    # --------------------------------

    if status_filter in [
        "pending",
        "confirmed",
        "completed",
        "rejected"
    ]:

        query = query.filter(
            ServiceRequest.status == status_filter
        )


    # --------------------------------
    # SEARCH FILTER
    #
    # Searches:
    # - User name
    # - User email
    # - Professional name
    # - Service name
    # --------------------------------

    if search:

        search_term = f"%{search}%"

        query = query.join(
            ServiceRequest.user
        ).join(
            ServiceRequest.professional
        ).join(
            ServiceRequest.service
        ).filter(
            db.or_(
                User.name.ilike(search_term),
                User.email.ilike(search_term),
                Service.name.ilike(search_term)
            )
        )


    # --------------------------------
    # PAYMENT STATUS FILTER
    # --------------------------------

    if payment_status in [
        "paid",
        "cancelled",
        "refunded"
    ]:

        query = query.filter(
            ServiceRequest.payment_status == payment_status
        )


    # --------------------------------
    # DATE FILTER
    # --------------------------------

    if date_from:

        query = query.filter(
            ServiceRequest.preferred_date >= date_from
        )


    if date_to:

        query = query.filter(
            ServiceRequest.preferred_date <= date_to
        )


    # --------------------------------
    # GET BOOKINGS
    # --------------------------------

    bookings = query.order_by(
        ServiceRequest.created_at.desc()
    ).all()


    # --------------------------------
    # SEND DATA TO TEMPLATE
    # --------------------------------

    return render_template(
        "admin/bookings.html",

        bookings=bookings,

        status_filter=status_filter,

        search=search,

        payment_status=payment_status,

        date_from=date_from,

        date_to=date_to
    )

# ============================================================
# ADMIN REPORTS
# ============================================================

# ============================================================
# ADMIN REPORTS & ANALYTICS
# ============================================================

# ============================================================
# ADMIN REPORTS & ANALYTICS
# ============================================================

@admin.route("/reports")
@login_required
def reports():

    if current_user.role != "admin":
        abort(403)

    # --------------------------------
    # GET DATE FILTERS
    # --------------------------------

    date_from = request.args.get("date_from", "").strip()
    date_to = request.args.get("date_to", "").strip()

    # --------------------------------
    # BASE QUERY
    # --------------------------------

    query = ServiceRequest.query

    # --------------------------------
    # DATE FILTER
    # --------------------------------

    if date_from:
        try:
            date_from_obj = datetime.strptime(
                date_from,
                "%Y-%m-%d"
            ).date()

            query = query.filter(
                ServiceRequest.preferred_date >= date_from_obj
            )

        except ValueError:
            date_from = ""

    if date_to:
        try:
            date_to_obj = datetime.strptime(
                date_to,
                "%Y-%m-%d"
            ).date()

            query = query.filter(
                ServiceRequest.preferred_date <= date_to_obj
            )

        except ValueError:
            date_to = ""

    # --------------------------------
    # GET FILTERED BOOKINGS
    # --------------------------------

    bookings = query.all()

    # --------------------------------
    # SUMMARY STATISTICS
    # --------------------------------

    total_bookings = len(bookings)

    paid_bookings = [
        booking
        for booking in bookings
        if booking.payment_status == "paid"
    ]

    refunded_bookings = [
        booking
        for booking in bookings
        if booking.payment_status == "refunded"
    ]

    cancelled_payments = [
        booking
        for booking in bookings
        if booking.payment_status == "cancelled"
    ]

    total_paid_bookings = len(paid_bookings)

    total_revenue = sum(
        float(booking.payment_amount or 0)
        for booking in paid_bookings
    )

    total_refunded = sum(
        float(booking.refund_amount or 0)
        for booking in refunded_bookings
    )

    net_revenue = total_revenue - total_refunded

    # --------------------------------
    # BOOKING STATUS
    # --------------------------------

    status_counts = {
        "Pending": 0,
        "Confirmed": 0,
        "Completed": 0,
        "Rejected": 0,
        "Cancelled": 0
    }

    for booking in bookings:

        status = (booking.status or "").lower()

        if status == "pending":
            status_counts["Pending"] += 1

        elif status == "confirmed":
            status_counts["Confirmed"] += 1

        elif status == "completed":
            status_counts["Completed"] += 1

        elif status == "rejected":
            status_counts["Rejected"] += 1

        elif status == "cancelled":
            status_counts["Cancelled"] += 1

    booking_status_labels = list(
        status_counts.keys()
    )

    booking_status_values = list(
        status_counts.values()
    )

    # --------------------------------
    # PAYMENT STATUS
    # --------------------------------

    payment_counts = {
        "Paid": len(paid_bookings),
        "Refunded": len(refunded_bookings),
        "Cancelled": len(cancelled_payments)
    }

    payment_labels = list(
        payment_counts.keys()
    )

    payment_values = list(
        payment_counts.values()
    )

    # --------------------------------
    # BOOKINGS BY SERVICE
    # --------------------------------

    service_counts = {}

    for booking in bookings:

        service_name = (
            booking.service.name
            if booking.service
            else "Unknown"
        )

        service_counts[service_name] = (
            service_counts.get(
                service_name,
                0
            ) + 1
        )

    service_data = sorted(
        service_counts.items(),
        key=lambda item: item[1],
        reverse=True
    )

    service_labels = [
        item[0]
        for item in service_data
    ]

    service_values = [
        item[1]
        for item in service_data
    ]

    # --------------------------------
    # BOOKINGS BY PROFESSIONAL
    # --------------------------------

    professional_counts = {}

    for booking in bookings:

        if (
            booking.professional
            and booking.professional.user
        ):
            professional_name = (
                booking.professional.user.name
            )
        else:
            professional_name = "Unknown"

        professional_counts[
            professional_name
        ] = professional_counts.get(
            professional_name,
            0
        ) + 1

    professional_data = sorted(
        professional_counts.items(),
        key=lambda item: item[1],
        reverse=True
    )

    professional_labels = [
        item[0]
        for item in professional_data[:10]
    ]

    professional_values = [
        item[1]
        for item in professional_data[:10]
    ]

    # --------------------------------
    # MONTHLY ANALYTICS
    # --------------------------------

    monthly_bookings = {}
    monthly_revenue = {}
    monthly_refunded = {}

    for booking in bookings:

        if not booking.preferred_date:
            continue

        month_key = booking.preferred_date.strftime(
            "%Y-%m"
        )

        # Booking count
        monthly_bookings[month_key] = (
            monthly_bookings.get(
                month_key,
                0
            ) + 1
        )

        # Revenue
        if booking.payment_status == "paid":

            monthly_revenue[month_key] = (
                monthly_revenue.get(
                    month_key,
                    0
                )
                + float(
                    booking.payment_amount or 0
                )
            )

        # Refund
        if booking.payment_status == "refunded":

            monthly_refunded[month_key] = (
                monthly_refunded.get(
                    month_key,
                    0
                )
                + float(
                    booking.refund_amount or 0
                )
            )

    all_months = sorted(
        set(
            list(monthly_bookings.keys())
            + list(monthly_revenue.keys())
            + list(monthly_refunded.keys())
        )
    )

    monthly_booking_values = [
        monthly_bookings.get(month, 0)
        for month in all_months
    ]

    monthly_revenue_values = [
        monthly_revenue.get(month, 0)
        for month in all_months
    ]

    monthly_refunded_values = [
        monthly_refunded.get(month, 0)
        for month in all_months
    ]

    monthly_net_values = [
        monthly_revenue.get(month, 0)
        - monthly_refunded.get(month, 0)
        for month in all_months
    ]

    # --------------------------------
    # RENDER REPORTS PAGE
    # --------------------------------

    return render_template(
        "admin/reports.html",

        date_from=date_from,
        date_to=date_to,

        total_bookings=total_bookings,
        total_paid_bookings=total_paid_bookings,

        total_revenue=total_revenue,
        total_refunded=total_refunded,
        net_revenue=net_revenue,

        booking_status_labels=booking_status_labels,
        booking_status_values=booking_status_values,

        payment_labels=payment_labels,
        payment_values=payment_values,

        service_labels=service_labels,
        service_values=service_values,

        professional_labels=professional_labels,
        professional_values=professional_values,

        monthly_labels=all_months,
        monthly_booking_values=monthly_booking_values,

        monthly_revenue_values=monthly_revenue_values,
        monthly_refunded_values=monthly_refunded_values,
        monthly_net_values=monthly_net_values
    )

@admin.route("/bookings/<int:request_id>")
@login_required
def booking_details(request_id):

    if current_user.role != "admin":
        abort(403)

    booking = ServiceRequest.query.get(request_id)

    if not booking:
        abort(404)

    return render_template(
        "admin/booking_details.html",
        booking=booking
    )
@admin.route("/notifications")
@login_required
def notifications():
    if current_user.role != "admin":
        abort(403)

    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    return render_template(
        "admin/notifications.html",
        user=current_user,
        notifications=notifications
    )
@admin.route("/notifications/<int:notification_id>")
@login_required
def notification_click(notification_id):

    if current_user.role != "admin":
        abort(403)

    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=current_user.id
    ).first()

    if not notification:
        abort(404)

    notification.is_read = True
    db.session.commit()

    # Professional service request
    if notification.professional_service_request_id:
        return redirect(
            url_for(
                "admin.service_request_details",
                request_id=notification.professional_service_request_id
            )
        )

    # Professional registration
    if notification.professional_user_id:
        return redirect(
            url_for(
                "admin.professional_details",
                user_id=notification.professional_user_id
            )
        )

    # Booking
    if notification.booking_id:
        return redirect(
            url_for(
                "admin.booking_details",
                request_id=notification.booking_id
            )
        )

    return redirect(
        url_for("admin.notifications")
    )

@admin.route("/professionals/<int:user_id>")
@login_required
def professional_details(user_id):

    if current_user.role != "admin":
        abort(403)

    professional = ProfessionalProfile.query.filter_by(
        user_id=user_id
    ).first()

    if not professional:
        abort(404)

    # ---------------------------------------
    # BOOKINGS
    # ---------------------------------------

    bookings = ServiceRequest.query.filter_by(
        professional_id=professional.id
    ).order_by(
        ServiceRequest.created_at.desc()
    ).all()

    total_bookings = len(bookings)

    completed_bookings = sum(
        1 for booking in bookings
        if booking.status == "completed"
    )

    cancelled_bookings = sum(
        1 for booking in bookings
        if booking.status == "cancelled"
    )

    pending_bookings = sum(
        1 for booking in bookings
        if booking.status == "pending"
    )

    confirmed_bookings = sum(
        1 for booking in bookings
        if booking.status == "confirmed"
    )

    # ---------------------------------------
    # REVENUE
    # ---------------------------------------

    total_revenue = sum(
        booking.payment_amount or 0
        for booking in bookings
        if booking.payment_status == "paid"
    )

    refunded_amount = sum(
        booking.refund_amount or 0
        for booking in bookings
        if booking.refund_status == "refunded"
    )

    # ---------------------------------------
    # REVIEWS
    # ---------------------------------------

    reviews = Review.query.filter_by(
        professional_id=professional.id
    ).order_by(
        Review.created_at.desc()
    ).all()

    total_reviews = len(reviews)

    average_rating = (
        sum(review.rating for review in reviews) / total_reviews
        if total_reviews > 0
        else 0
    )

    # ---------------------------------------
    # SERVICES
    # ---------------------------------------

    services = professional.services

    # ---------------------------------------
    # BOOKING STATUS CHART
    # ---------------------------------------

    booking_status_data = {
        "Completed": completed_bookings,
        "Confirmed": confirmed_bookings,
        "Pending": pending_bookings,
        "Cancelled": cancelled_bookings
    }

    # ---------------------------------------
    # MONTHLY REVENUE CHART
    # ---------------------------------------

    monthly_revenue = defaultdict(float)

    for booking in bookings:

        if (
            booking.payment_status == "paid"
            and booking.payment_amount
            and booking.created_at
        ):

            month_key = booking.created_at.strftime("%Y-%m")

            monthly_revenue[month_key] += float(
                booking.payment_amount
            )

    monthly_revenue = dict(
        sorted(monthly_revenue.items())
    )

    revenue_labels = []

    for month in monthly_revenue.keys():

        date_value = datetime.strptime(
            month,
            "%Y-%m"
        )

        revenue_labels.append(
            date_value.strftime("%b %Y")
        )

    revenue_values = list(
        monthly_revenue.values()
    )

    # ---------------------------------------
    # RENDER
    # ---------------------------------------

    return render_template(
        "admin/professional_details.html",

        professional=professional,

        bookings=bookings,
        services=services,
        reviews=reviews,

        total_bookings=total_bookings,
        completed_bookings=completed_bookings,
        cancelled_bookings=cancelled_bookings,
        pending_bookings=pending_bookings,
        confirmed_bookings=confirmed_bookings,

        total_revenue=total_revenue,
        refunded_amount=refunded_amount,

        total_reviews=total_reviews,
        average_rating=average_rating,

        booking_status_data=booking_status_data,
        revenue_labels=revenue_labels,
        revenue_values=revenue_values
    )