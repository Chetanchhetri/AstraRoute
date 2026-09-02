import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_otp_email_sync(recipient_email: str, otp_code: str) -> bool:
    sender_email = settings.EMAIL_SENDER.strip()
    sender_password = settings.EMAIL_PASSWORD.replace(" ", "").strip()

    if not sender_email or not sender_password:
        print("❌ Mail Error: 'EMAIL_SENDER' or 'EMAIL_PASSWORD' is empty in app settings.")
        return False

    html_message = f"""
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>OTP Verification</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; background-color: #f4f4f4; margin: 0; padding: 0; }}
            .email-container {{ max-width: 600px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); overflow: hidden; }}
            .header {{ background: linear-gradient(90deg, #00ff8e 0%, #00c9ff 100%); color: white; padding: 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 600; }}
            .content {{ padding: 30px; text-align: center; }}
            .otp-container {{ background: #f8f9fa; border: 2px solid #00c9ff; border-radius: 12px; padding: 20px; margin: 20px 0; }}
            .otp-code {{ font-size: 36px; font-weight: 700; color: #00c9ff; letter-spacing: 8px; font-family: 'Courier New', monospace; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>🔐 AstraRoute Verification</h1>
            </div>
            <div class="content">
                <p>Use the code below to complete your registration:</p>
                <div class="otp-container">
                    <div class="otp-code">{otp_code}</div>
                </div>
                <p style="font-size: 12px; color: #777;">This code expires in 10 minutes.</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = f"AstraRoute <{sender_email}>"
    msg["To"] = recipient_email
    msg["Subject"] = f"{otp_code} is your AstraRoute Verification Code"
    msg.attach(MIMEText(html_message, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())
        print(f"✅ OTP email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"❌ SMTP Transmission Failure: {str(e)}")
        return False

send_otp_email = send_otp_email_sync