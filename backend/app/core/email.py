import smtplib
import ssl
import html
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging
from .config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

# Constants for token expiry (should match security.py)
PASSWORD_RESET_EXPIRY_HOURS = 1
EMAIL_VERIFICATION_EXPIRY_HOURS = 24


class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.from_email = settings.FROM_EMAIL
        self.from_name = settings.FROM_NAME
        
        # Validate required settings
        required_settings = [
            (self.smtp_server, "SMTP_SERVER"),
            (self.smtp_username, "SMTP_USERNAME"),
            (self.smtp_password, "SMTP_PASSWORD"),
            (self.from_email, "FROM_EMAIL"),
            (self.from_name, "FROM_NAME")
        ]
        
        for value, name in required_settings:
            if not value:
                raise ValueError(f"Missing required email setting: {name}")

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email."""
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Add text part if provided
            if text_content:
                text_part = MIMEText(text_content, "plain")
                message.attach(text_part)

            # Add HTML part
            html_part = MIMEText(html_content, "html")
            message.attach(html_part)

            # Create SMTP session with proper connection management
            try:
                if self.smtp_use_tls:
                    context = ssl.create_default_context()
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.starttls(context=context)
                        server.login(self.smtp_username, self.smtp_password)
                        server.send_message(message)
                else:
                    with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                        server.login(self.smtp_username, self.smtp_password)
                        server.send_message(message)
            except smtplib.SMTPException as e:
                logger.error(f"SMTP error sending email to {to_email}: {str(e)}")
                return False
            except (OSError, ConnectionError) as e:
                logger.error(f"Connection error sending email to {to_email}: {str(e)}")
                return False

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            return False

    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email."""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        escaped_user_name = html.escape(user_name)
        
        subject = "Reset Your Password - Tiny CRM"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Password Reset Request</h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 16px; margin-bottom: 20px;">Hi {escaped_user_name},</p>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    We received a request to reset your password for your Tiny CRM account. 
                    If you didn't make this request, you can safely ignore this email.
                </p>
                
                <p style="font-size: 16px; margin-bottom: 30px;">
                    To reset your password, click the button below:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px;">
                        Reset Password
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    This link will expire in {PASSWORD_RESET_EXPIRY_HOURS} hour(s) for security reasons.
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 20px;">
                    If the button doesn't work, you can copy and paste this link into your browser:
                    <br><a href="{reset_url}" style="color: #667eea; word-break: break-all;">{reset_url}</a>
                </p>
                
                <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666; text-align: center;">
                    Best regards,<br>
                    The Tiny CRM Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {user_name},

        We received a request to reset your password for your Tiny CRM account.
        If you didn't make this request, you can safely ignore this email.

        To reset your password, visit this link:
        {reset_url}

        This link will expire in {PASSWORD_RESET_EXPIRY_HOURS} hour(s) for security reasons.

        Best regards,
        The Tiny CRM Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

    def send_email_verification_email(self, to_email: str, verification_token: str, user_name: str) -> bool:
        """Send email verification email."""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        escaped_user_name = html.escape(user_name)
        
        subject = "Verify Your Email - Tiny CRM"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Welcome to Tiny CRM!</h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 16px; margin-bottom: 20px;">Hi {escaped_user_name},</p>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    Thank you for signing up for Tiny CRM! To complete your registration and 
                    secure your account, please verify your email address.
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px;">
                        Verify Email
                    </a>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    This link will expire in {EMAIL_VERIFICATION_EXPIRY_HOURS} hour(s) for security reasons.
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 20px;">
                    If the button doesn't work, you can copy and paste this link into your browser:
                    <br><a href="{verification_url}" style="color: #667eea; word-break: break-all;">{verification_url}</a>
                </p>
                
                <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666; text-align: center;">
                    Welcome aboard!<br>
                    The Tiny CRM Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {user_name},

        Thank you for signing up for Tiny CRM! To complete your registration and 
        secure your account, please verify your email address.

        To verify your email, visit this link:
        {verification_url}

        This link will expire in {EMAIL_VERIFICATION_EXPIRY_HOURS} hour(s) for security reasons.

        Welcome aboard!
        The Tiny CRM Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_changed_notification(self, to_email: str, user_name: str) -> bool:
        """Send password changed notification email."""
        escaped_user_name = html.escape(user_name)
        
        subject = "Password Changed - Tiny CRM"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Changed</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">Password Changed</h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 16px; margin-bottom: 20px;">Hi {escaped_user_name},</p>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    This is a confirmation that your password has been successfully changed for your Tiny CRM account.
                </p>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    If you didn't make this change, please contact our support team immediately.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666; text-align: center;">
                    Best regards,<br>
                    The Tiny CRM Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hi {user_name},

        This is a confirmation that your password has been successfully changed for your Tiny CRM account.

        If you didn't make this change, please contact our support team immediately.

        Best regards,
        The Tiny CRM Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)

    def send_organization_invite(
        self, 
        to_email: str, 
        organization_name: str, 
        inviter_name: str, 
        invite_code: str, 
        role: str,
        expires_at: datetime
    ) -> bool:
        """Send organization invite email."""
        invite_url = f"{settings.FRONTEND_URL}/join?code={invite_code}"
        escaped_organization_name = html.escape(organization_name)
        escaped_inviter_name = html.escape(inviter_name)
        escaped_role = html.escape(role)
        
        subject = f"Invitation to join {escaped_organization_name} - Tiny CRM"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Organization Invitation</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                <h1 style="color: white; margin: 0; font-size: 28px;">You're Invited!</h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 30px; border-radius: 0 0 10px 10px; border: 1px solid #e9ecef;">
                <p style="font-size: 16px; margin-bottom: 20px;">Hello,</p>
                
                <p style="font-size: 16px; margin-bottom: 20px;">
                    <strong>{escaped_inviter_name}</strong> has invited you to join 
                    <strong>{escaped_organization_name}</strong> on Tiny CRM as a <strong>{escaped_role}</strong>.
                </p>
                
                <p style="font-size: 16px; margin-bottom: 30px;">
                    Click the button below to accept this invitation and join the organization:
                </p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invite_url}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; font-size: 16px;">
                        Accept Invitation
                    </a>
                </div>
                
                <div style="background: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin: 0 0 10px 0; color: #1976d2;">Organization Details:</h3>
                    <p style="margin: 5px 0;"><strong>Organization:</strong> {escaped_organization_name}</p>
                    <p style="margin: 5px 0;"><strong>Role:</strong> {escaped_role}</p>
                    <p style="margin: 5px 0;"><strong>Invited by:</strong> {escaped_inviter_name}</p>
                    <p style="margin: 5px 0;"><strong>Expires:</strong> {expires_at.strftime('%B %d, %Y at %I:%M %p UTC')}</p>
                </div>
                
                <p style="font-size: 14px; color: #666; margin-top: 30px;">
                    If you don't have a Tiny CRM account yet, you'll be able to create one when you accept the invitation.
                </p>
                
                <p style="font-size: 14px; color: #666; margin-top: 20px;">
                    If the button doesn't work, you can copy and paste this link into your browser:
                    <br><a href="{invite_url}" style="color: #667eea; word-break: break-all;">{invite_url}</a>
                </p>
                
                <hr style="border: none; border-top: 1px solid #e9ecef; margin: 30px 0;">
                
                <p style="font-size: 14px; color: #666; text-align: center;">
                    Best regards,<br>
                    The Tiny CRM Team
                </p>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Hello,

        {inviter_name} has invited you to join {organization_name} on Tiny CRM as a {role}.

        Organization Details:
        - Organization: {organization_name}
        - Role: {role}
        - Invited by: {inviter_name}
        - Expires: {expires_at.strftime('%B %d, %Y at %I:%M %p UTC')}

        To accept this invitation, visit:
        {invite_url}

        If you don't have a Tiny CRM account yet, you'll be able to create one when you accept the invitation.

        Best regards,
        The Tiny CRM Team
        """
        
        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService() 
 