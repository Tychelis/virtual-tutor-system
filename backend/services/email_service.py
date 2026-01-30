from flask_mail import Message, Mail

# Initialize Flask-Mail instance
mail = Mail()

def send_verification_email(email, code):
    """Send a verification code email to the specified recipient."""
    msg = Message(
        "Your TutorNet Verification Code",  # Email subject
        recipients=[email],                 # Recipient list
        body=f"Your verification code is: {code}\nValid for 5 minutes."  # Email body
    )
    mail.send(msg)  # Send the email
