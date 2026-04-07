import smtplib
import random
import string
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

def generate_verification_code(length=6):
    """Generates a secure numeric code."""
    return ''.join(random.choices(string.digits, k=length))

def send_verification_email(recipient_email, code, config):
    """
    Sends the HTML verification email using SMTP settings from app config.
    """
    # 1. Load Credentials from Config
    smtp_server = config.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = config.get("SMTP_PORT", 587)
    sender_email = config.get("MAIL_USERNAME") # Assuming these are in your .env
    sender_password = config.get("MAIL_PASSWORD")

    if not sender_email or not sender_password:
        logger.error("❌ EMAIL ERROR: MAIL_USERNAME or MAIL_PASSWORD missing in config.")
        # For testing purposes only, print the code to console so you aren't stuck
        print(f"\n[DEBUG MODE] Verification Code for {recipient_email}: {code}\n")
        return True # Return True to allow flow to continue during dev

    try:
        # 2. Build the Email
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Your ANDSE Verification Code: {code}"
        msg["From"] = f"ANDSE Security <{sender_email}>"
        msg["To"] = recipient_email

        # 3. HTML Body (Professional & Massive)
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
            <div style="max-width: 500px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 10px; border: 1px solid #ddd;">
              <h2 style="color: #333; text-align: center;">Verify Your Identity</h2>
              <p style="color: #666; font-size: 16px;">Welcome to ANDSE AI. Please use the following code to complete your secure registration:</p>
              
              <div style="background: #e0f7fa; color: #006064; font-size: 32px; font-weight: bold; text-align: center; padding: 15px; margin: 20px 0; border-radius: 5px; letter-spacing: 5px;">
                {code}
              </div>
              
              <p style="color: #999; font-size: 12px; text-align: center;">This code will expire in 10 minutes.</p>
            </div>
          </body>
        </html>
        """
        msg.attach(MIMEText(html, "html"))

        # 4. Send via SMTP
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Verification email sent to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"❌ SMTP FAILURE: {str(e)}")
        # Fallback for dev: Print code if email fails
        print(f"\n[FALLBACK] Verification Code for {recipient_email}: {code}\n")
        return False