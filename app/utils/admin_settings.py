from ..extensions import db
from ..models.admin_settings import AdminSettings


def get_admin_settings():
    """
    Return the application's admin settings.

    Creates the default settings record if one does not exist.
    """

    settings = AdminSettings.query.first()

    if not settings:
        settings = AdminSettings(
            site_name="AllYourHelp",
            support_email=None,
            support_phone=None,
            maintenance_mode=False,
            bookings_enabled=True,
            payments_enabled=True,
            email_notifications_enabled=True,
            platform_fee_percentage=0
        )

        db.session.add(settings)
        db.session.commit()

    return settings
