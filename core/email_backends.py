import resend
import logging
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

logger = logging.getLogger(__name__)

class ResendEmailBackend(BaseEmailBackend):
    """Custom email backend using Resend API for floodwarning.biz domain"""
    
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        self.api_key = getattr(settings, 'RESEND_API_KEY', '')
        if self.api_key:
            resend.api_key = self.api_key
        else:
            logger.warning("RESEND_API_KEY not configured")
    
    def send_messages(self, email_messages):
        if not email_messages:
            return 0
        
        if not self.api_key:
            logger.error("Cannot send emails: RESEND_API_KEY not configured")
            return 0
        
        sent_count = 0
        for message in email_messages:
            try:
                html_content = None
                text_content = message.body
                
                # Extract HTML content if available
                if hasattr(message, 'alternatives'):
                    for content, mimetype in message.alternatives:
                        if mimetype == 'text/html':
                            html_content = content
                            break
                
                # Build email data
                from_email = message.from_email or settings.DEFAULT_FROM_EMAIL
                
                email_data = {
                    "from": from_email,
                    "to": list(message.to),
                    "subject": message.subject,
                }
                
                # Add CC and BCC if present
                if message.cc:
                    email_data["cc"] = list(message.cc)
                if message.bcc:
                    email_data["bcc"] = list(message.bcc)
                
                # Add reply-to if present
                if message.reply_to:
                    email_data["reply_to"] = list(message.reply_to)[0]
                
                # Add content
                if html_content:
                    email_data["html"] = html_content
                if text_content:
                    email_data["text"] = text_content
                
                # Send via Resend API
                response = resend.Emails.send(email_data)
                logger.info(f"Email sent via Resend to {message.to}: {message.subject} (ID: {response.get('id', 'unknown')})")
                sent_count += 1
                
            except Exception as e:
                logger.error(f"Resend email error to {message.to}: {str(e)}")
                if not self.fail_silently:
                    raise e
        
        return sent_count
