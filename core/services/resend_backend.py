import resend
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

class ResendEmailBackend(BaseEmailBackend):
    def __init__(self, fail_silently=False, **kwargs):
        super().__init__(fail_silently=fail_silently, **kwargs)
        resend.api_key = settings.RESEND_API_KEY

    def send_messages(self, email_messages):
        sent_count = 0
        for message in email_messages:
            try:
                resend.Emails.send({
                    "from": message.from_email,
                    "to": message.to,
                    "subject": message.subject,
                    "html": message.body if message.content_subtype == 'html' else None,
                    "text": message.body if message.content_subtype != 'html' else None,
                })
                sent_count += 1
            except Exception as e:
                if not self.fail_silently:
                    raise e
        return sent_count
