import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

sender = os.getenv("EMAIL_SENDER", "").strip()
password = os.getenv("EMAIL_PASSWORD", "").replace(" ", "").strip()
recipient = sender  # Send test email to yourself

print(f"Testing SMTP with sender: {sender}")

msg = MIMEText("This is a test OTP email from AstraRoute.")
msg["Subject"] = "SMTP Test Email"
msg["From"] = sender
msg["To"] = recipient

try:
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print("✅ Email sent successfully! Check your inbox/spam folder.")
except Exception as e:
    print(f"❌ Failed to send email: {e}")