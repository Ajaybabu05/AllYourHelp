from . import create_app
from .extensions import db
from .models.service_category import ServiceCategory
from .models.service import Service


categories = {
    "Legal": [
        ("Family Lawyer", "Legal assistance related to family matters."),
        ("Property Lawyer", "Legal assistance related to property matters."),
        ("Criminal Lawyer", "Legal assistance for criminal cases."),
        ("Corporate Lawyer", "Legal services for businesses and companies.")
    ],

    "Medical": [
        ("General Physician", "General medical consultation."),
        ("Dentist", "Dental consultation and treatment."),
        ("Dermatologist", "Skin, hair and related medical services."),
        ("Physiotherapist", "Physical therapy and rehabilitation services.")
    ],

    "CA & Tax": [
        ("Income Tax", "Income tax filing and related assistance."),
        ("GST Services", "GST registration, filing and compliance."),
        ("Accounting", "Bookkeeping and accounting assistance."),
        ("Tax Consultation", "Professional tax planning and consultation.")
    ],

    "Property": [
        ("Property Consultant", "Professional property consultation."),
        ("Real Estate Agent", "Assistance with buying and selling property."),
        ("Property Documentation", "Assistance with property-related services.")
    ],

    "Education": [
        ("Mathematics Tutor", "Mathematics tutoring."),
        ("Science Tutor", "Science tutoring."),
        ("English Tutor", "English language tutoring."),
        ("Programming Tutor", "Programming and computer science tutoring.")
    ],

    "Visa": [
        ("Student Visa", "Assistance with student visa applications."),
        ("Work Visa", "Assistance with work visa applications."),
        ("Tourist Visa", "Assistance with tourist visa applications."),
        ("Immigration Consultation", "Professional immigration guidance.")
    ],

    "Technology": [
        ("Web Development", "Website development and maintenance."),
        ("Software Development", "Custom software development."),
        ("IT Support", "Technical and IT support."),
        ("Mobile App Development", "Android and iOS application development.")
    ],

    "Documentation": [
        ("Document Preparation", "Professional document preparation."),
        ("Application Assistance", "Help with applications."),
        ("Resume Preparation", "Professional resume creation and improvement."),
        ("Official Documents", "Assistance with official documentation.")
    ],

    "Business": [
        ("Business Consulting", "Professional business consultation."),
        ("Startup Consulting", "Guidance for starting and growing a business."),
        ("Business Registration", "Assistance with business registration."),
        ("Marketing Consulting", "Business marketing guidance.")
    ],

    "Loans": [
        ("Home Loan", "Assistance with home loan applications."),
        ("Education Loan", "Assistance with education loan applications."),
        ("Personal Loan", "Assistance with personal loan applications."),
        ("Business Loan", "Assistance with business loan applications.")
    ]
}


def seed_database():

    app = create_app()

    with app.app_context():

        for category_name, service_list in categories.items():

            category = ServiceCategory.query.filter_by(
                name=category_name
            ).first()

            if not category:
                category = ServiceCategory(
                    name=category_name,
                    slug=category_name.lower()
                    .replace(" & ", "-")
                    .replace(" ", "-"),
                    description=f"{category_name} related professional services."
                )

                db.session.add(category)
                db.session.flush()

            for service_name, description in service_list:

                slug = service_name.lower().replace(" ", "-")

                existing_service = Service.query.filter_by(
                    slug=slug
                ).first()

                if existing_service:
                    continue

                service = Service(
                    category_id=category.id,
                    name=service_name,
                    slug=slug,
                    description=description
                )

                db.session.add(service)

        db.session.commit()

        print("Service categories and services seeded successfully!")


if __name__ == "__main__":
    seed_database()