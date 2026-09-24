from flask_mail import Message
from ..extensions import mail


def send_email(recipient, subject, body):

    try:
        message = Message(
            subject=subject,
            recipients=[recipient]
        )

        message.body = body

        mail.send(message)

        print(f"Email sent successfully to {recipient}")

        return True

    except Exception as e:

        print("====================================")
        print("EMAIL SENDING ERROR")
        print(f"Recipient: {recipient}")
        print(f"Error: {repr(e)}")
        print("====================================")

        return False