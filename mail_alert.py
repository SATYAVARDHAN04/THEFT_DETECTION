import smtplib
from email.mime.text import MIMEText

# Email Credentials
EMAIL_SENDER = "svardhan278@gmail.com"
EMAIL_PASSWORD = "ayjv lbmi byej pdyk"  # App Password
EMAIL_RECEIVER = "manikondavasavi19431@gmail.com"

def send_email_alert(reason):
    subject = "🚨 Alert: Suspicious Activity Detected!"
    body = f"Warning: {reason} detected in surveillance footage."

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        server.quit()
        print("✅ Email Alert Sent Successfully!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")