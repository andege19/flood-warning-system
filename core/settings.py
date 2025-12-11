import resend
import logging
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

class ResendEmailBackend(BaseEmailBackend):
    """Custom email backend using Resend API"""
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        resend.api_key = getattr(settings, 'RESEND_API_KEY', '')
    
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        sent_count = 0
        for message in email_messages:
            try:
                html_content = None
                text_content = message.body
                
                if hasattr(message, 'alternatives'):
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            html_content = content
                            break
                
                email_data = {
                    "from": message.from_email or settings.DEFAULT_FROM_EMAIL,
                    "to": list(message.to),
                    "subject": message.subject,
                }
                
                if html_content:
                    email_data["html"] = html_content
                else:
                    email_data["text"] = text_content
                
                resend.Emails.send(email_data)
                logger.info(f"Email sent via Resend: {message.subject} to {message.to}")
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Resend email error: {str(e)}")
                if not self.fail_silently:
                    raise e
        
        return sent_count