import os
import logging
from typing import List
from pydantic import BaseModel, EmailStr, ValidationError
from dotenv import load_dotenv, find_dotenv
import resend


# ----- Logging setup -----
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ----- Load environment variables -----
load_dotenv(find_dotenv())
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
if not RESEND_API_KEY:
    raise RuntimeError("RESEND_API_KEY is not set")

resend.api_key = RESEND_API_KEY

# ----- Pydantic model -----
class Email(BaseModel):
    from_email: EmailStr
    to: List[EmailStr]
    subject: str
    html: str

# ----- Email Service -----
class EmailService:
    """
    Service to send emails via Resend API
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        resend.api_key = self.api_key

    def send_email(self, email: Email) -> dict:
        """
        Send email via Resend
        """
        try:
            if not email.from_email or not email.to or not email.subject or not email.html:
                raise ValueError("Invalid email parameters")

            response = resend.Emails.send({
                "from": email.from_email,
                "to": email.to,
                "subject": email.subject,
                "html": email.html
            })
            logger.info(f"Email sent successfully to {email.to}")
            return response

        except ValidationError as ve:
            logger.error(f"Email validation error: {ve}")
            raise

        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            raise RuntimeError(f"Email send failed: {e}")
