"""
Email service for sending alerts and notifications via Resend
Sends from verified domain: floodwarning.biz
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

class FloodAlertEmailService:
    """Email service for flood warning system using Resend"""
    
    @staticmethod
    def _send_email(subject, html_content, recipient_email, recipient_name=None):
        """Base method to send emails via Resend"""
        try:
            text_content = strip_tags(html_content)
            
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[recipient_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send(fail_silently=False)
            
            logger.info(f"Email sent to {recipient_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return False
    
    # ==========================================
    # REPORT-RELATED EMAILS (User Reports)
    # ==========================================
    
    @staticmethod
    def send_report_confirmation(recipient_email, recipient_name, report_id, location):
        """Send confirmation when user submits a flood report"""
        subject = f"Report Received: #{report_id} - Flood Warning System"
        
        html_content = f"""
        <html>
        <body style="font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto; padding: 0;">
            <div style="background: linear-gradient(135deg, #0d6efd 0%, #0056b3 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">Flood Warning System</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0;">Report Received</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <p>Dear {recipient_name},</p>
                
                <p>Thank you for submitting your flood report to our system. Your contribution is valuable and helps protect our community.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <h3 style="margin: 0 0 15px; color: #333;">Report Details</h3>
                    <p style="margin: 5px 0;"><strong>Report ID:</strong> #{report_id}</p>
                    <p style="margin: 5px 0;"><strong>Location:</strong> {location}</p>
                    <p style="margin: 5px 0;"><strong>Status:</strong> <span style="color: #fd7e14; font-weight: bold;">Under Review</span></p>
                    <p style="margin: 5px 0;"><strong>Submitted:</strong> Just now</p>
                </div>
                
                <p>Our team of authorities will review your report shortly. Once they have verified the information, you will receive an update via email.</p>
                
                <p style="margin-top: 30px;">
                    <a href="{settings.SITE_URL}/report/{report_id}/" style="display: inline-block; background: #0d6efd; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">View Report Status</a>
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="color: #666; font-size: 12px; margin: 0;">
                    This is an automated message from Flood Warning System. Do not reply to this email.
                </p>
            </div>
        </body>
        </html>
        """
        
        return FloodAlertEmailService._send_email(subject, html_content, recipient_email, recipient_name)
    
    @staticmethod
    def send_report_validated(recipient_email, recipient_name, report_id, admin_notes=None):
        """Send notification when report is validated"""
        subject = f"Flood Report #{report_id} Has Been Validated"
        
        notes_section = ""
        if admin_notes:
            notes_section = f"""
            <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #0d6efd;">
                <h4 style="color: #0056b3; margin-top: 0;">Admin Notes</h4>
                <p style="margin: 0; color: #333; white-space: pre-wrap;">{admin_notes}</p>
            </div>
            """
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #28a745, #1e7e34); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Report Validated</h1>
            </div>
            <div style="padding: 30px; background: #f8f9fa; border-radius: 0 0 10px 10px;">
                <h2 style="color: #28a745;">Your Report Has Been Validated</h2>
                <p>Dear {recipient_name},</p>
                <p>Your flood report #{report_id} has been reviewed and validated by our authorities.</p>
                
                <div style="background: #d4edda; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #28a745;">
                    <p style="margin: 0; color: #155724;"><strong>Status:</strong> Validated</p>
                    <p style="margin: 10px 0 0; color: #155724;">Your report is now being used to help protect the community.</p>
                </div>
                
                {notes_section}
                
                <p>Thank you for your contribution to community safety.</p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="color: #666; font-size: 12px;">Flood Warning System - Protecting Nairobi Communities</p>
            </div>
        </body>
        </html>
        """
        
        return FloodAlertEmailService._send_email(subject, html_content, recipient_email, recipient_name)
    
    @staticmethod
    def send_report_rejected(recipient_email, recipient_name, report_id, reason=None):
        """Send notification when report is rejected"""
        subject = f"Flood Report #{report_id} Update"
        
        reason_text = reason if reason else "The report could not be verified at this time."
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #6c757d, #495057); padding: 20px; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0;">Report Update</h1>
            </div>
            <div style="padding: 30px; background: #f8f9fa; border-radius: 0 0 10px 10px;">
                <h2 style="color: #333;">Report #{report_id} Status Update</h2>
                <p>Dear {recipient_name},</p>
                <p>We have reviewed your flood report and unfortunately could not validate it at this time.</p>
                
                <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #ffc107;">
                    <h4 style="color: #856404; margin-top: 0;">Reason for Rejection</h4>
                    <p style="margin: 0; color: #333; white-space: pre-wrap;">{reason_text}</p>
                </div>
                
                <p>If you believe this is an error or have additional information, please submit a new report with more details.</p>
                
                <a href="{settings.SITE_URL}/submit-report/" style="display: inline-block; background: #0d6efd; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 15px;">Submit New Report</a>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="color: #666; font-size: 12px;">Flood Warning System</p>
            </div>
        </body>
        </html>
        """
        
        return FloodAlertEmailService._send_email(subject, html_content, recipient_email, recipient_name)
    
    # ==========================================
    # AUTHORITY NOTIFICATIONS
    # ==========================================
    
    @staticmethod
    def send_new_report_notification(authority_email, report_id, location, submitted_by, report_text):
        """Notify admin when new report is submitted"""
        subject = f"New Flood Report Submitted: #{report_id}"
        
        html_content = f"""
        <html>
        <body style="font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto; padding: 0;">
            <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0;">New Report Submitted</h1>
                <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0;">Action Required</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <p>A new flood report has been submitted and requires your review.</p>
                
                <div style="background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border: 2px solid #ff6b6b;">
                    <h3 style="margin: 0 0 15px; color: #333;">Report Information</h3>
                    <p style="margin: 5px 0;"><strong>Report ID:</strong> #{report_id}</p>
                    <p style="margin: 5px 0;"><strong>Location:</strong> {location}</p>
                    <p style="margin: 5px 0;"><strong>Submitted By:</strong> {submitted_by}</p>
                    <p style="margin: 5px 0;"><strong>Description:</strong> {report_text[:100]}...</p>
                </div>
                
                <p style="margin-top: 20px;">Please review this report and take appropriate action (validate or reject).</p>
                
                <p style="margin-top: 30px;">
                    <a href="{settings.SITE_URL}/authority/dashboard/" style="display: inline-block; background: #ff6b6b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: bold;">Review Report</a>
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="color: #666; font-size: 12px; margin: 0;">
                    Flood Warning System - Authority Dashboard
                </p>
            </div>
        </body>
        </html>
        """
        
        return FloodAlertEmailService._send_email(subject, html_content, authority_email, "Admin")
    
    @staticmethod
    def notify_authorities_new_report(report):
        """Notify all authorities about new report"""
        from core.models import CustomUser
        
        authorities = CustomUser.objects.filter(
            role='authority',
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        sent_count = 0
        for authority in authorities:
            success = FloodAlertEmailService.send_new_report_notification(
                authority_email=authority.email,
                report_id=report.id,
                location=report.location_description or 'Not specified',
                submitted_by=report.submitted_by.username,
                report_text=report.report_text or ''
            )
            if success:
                sent_count += 1
        
        logger.info(f"Notified {sent_count} authorities about report #{report.id}")
        return sent_count
    
    # ==========================================
    # FLOOD ALERTS TO RESIDENTS
    # ==========================================
    
    @staticmethod
    def send_flood_alert(recipient_email, recipient_name, ward_name, risk_level, alert_message):
        """Send flood alert to resident"""
        colors = {
            'High': ('#dc3545', '#f8d7da', '#721c24'),
            'Medium': ('#fd7e14', '#fff3cd', '#856404'),
            'Low': ('#28a745', '#d4edda', '#155724')
        }
        
        bg_color, alert_bg, text_color = colors.get(risk_level, ('#6c757d', '#e9ecef', '#333'))
        
        subject = f"Flood Alert: {risk_level} Risk in {ward_name}"
        
        html_content = f"""
        <html>
        <body style="font-family: 'Arial', sans-serif; max-width: 600px; margin: 0 auto; padding: 0;">
            <div style="background: {bg_color}; padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 32px;">FLOOD ALERT</h1>
                <p style="color: white; margin: 10px 0 0; font-size: 18px;">{risk_level} Risk Level</p>
            </div>
            
            <div style="padding: 30px; background: #f8f9fa;">
                <p>Dear {recipient_name},</p>
                
                <p>A flood alert has been issued for your area.</p>
                
                <div style="background: {alert_bg}; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid {bg_color};">
                    <h3 style="margin: 0 0 10px; color: {text_color};">{ward_name}</h3>
                    <p style="margin: 0; color: {text_color}; font-size: 14px;">{alert_message}</p>
                </div>
                
                <h3 style="color: #333; margin-top: 25px;">Safety Instructions</h3>
                <ul style="color: #555; line-height: 1.8;">
                    <li>Stay informed and monitor official updates</li>
                    <li>Avoid walking or driving through flood waters</li>
                    <li>Move to higher ground if flooding is imminent</li>
                    <li>Keep emergency supplies ready</li>
                    <li>Follow evacuation orders if issued</li>
                </ul>
                
                <h3 style="color: #333;">Emergency Contacts</h3>
                <ul style="color: #555; line-height: 1.8;">
                    <li>Kenya Red Cross: 1199</li>
                    <li>National Emergency: 999</li>
                    <li>NDMA: 0800 723 253</li>
                </ul>
                
                <p style="margin-top: 30px;">
                    <a href="{settings.SITE_URL}/map/" style="display: inline-block; background: {bg_color}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">View Live Flood Map</a>
                </p>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #ddd;">
                <p style="color: #666; font-size: 12px; margin: 0;">
                    Stay safe. Flood Warning System - Protecting Nairobi
                </p>
            </div>
        </body>
        </html>
        """
        
        return FloodAlertEmailService._send_email(subject, html_content, recipient_email, recipient_name)
    
    @staticmethod
    def send_ward_flood_alert(ward, risk_level, message):
        """Send flood alert to all users in affected ward"""
        from core.models import CustomUser
        
        users = CustomUser.objects.filter(
            is_active=True,
            email__isnull=False
        ).exclude(email='')
        
        sent_count = 0
        for user in users:
            success = FloodAlertEmailService.send_flood_alert(
                recipient_email=user.email,
                recipient_name=user.username,
                ward_name=ward.name,
                risk_level=risk_level,
                alert_message=message
            )
            if success:
                sent_count += 1
        
        logger.info(f"Sent flood alerts for {ward.name} to {sent_count} users")
        return sent_count
