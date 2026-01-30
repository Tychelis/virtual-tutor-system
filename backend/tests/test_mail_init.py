import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sender_email = "your email"
app_password = "your app password"

receiver_email = "your email"

subject = "test"
body = "This is a test message."

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.ehlo()
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
    print("Success")
except Exception as e:
    print("Fail:", str(e))

