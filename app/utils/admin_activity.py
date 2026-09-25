from flask import request
from flask_login import current_user

from ..extensions import db
from ..models.admin_activity_log import AdminActivityLog


def log_admin_activity(
    action,
    description,
    target_type=None,
    target_id=None
):
    """
    Create an activity log for the currently logged-in admin.
    """

    if not current_user.is_authenticated:
        return

    if current_user.role != "admin":
        return

    log = AdminActivityLog(
        admin_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        description=description,
        ip_address=request.remote_addr
    )

    db.session.add(log)
    db.session.commit()