import smtplib
import os
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
        self.port = int(os.environ.get("MAIL_PORT", 465))
        self.use_ssl = True
        self.username = os.environ.get("MAIL_USERNAME")
        self.password = os.environ.get("MAIL_PASSWORD")

    def send_email(self, recipient, subject, body_html):
        if not self.username or not self.password:
            logger.error("Email credentials missing.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = f"ANDSE AI <{self.username}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(body_html, 'html'))

            if self.use_ssl:
                with smtplib.SMTP_SSL(self.server, self.port) as smtp:
                    smtp.login(self.username, self.password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(self.server, self.port) as smtp:
                    smtp.starttls()
                    smtp.login(self.username, self.password)
                    smtp.send_message(msg)
            
            logger.info(f"Email sent to {recipient}")
            return True
        except Exception as e:
            logger.error(f"Email Dispatch Failed: {e}")
            return False

email_service = EmailService()
