from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from core.config import config
import os

# Email configuration
email_config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your-email@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "your-app-password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "noreply@teachme.ai"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

fastmail = FastMail(email_config)

async def send_invite_email(email: str, org_name: str, invite_id: str, frontend_url: str = "http://localhost:3000"):
    """Send organization invite email"""
    
    # Email service debug info (can be removed in production)
    # print(f"🔧 EMAIL SERVICE DEBUG: Starting send_invite_email")
    
    # Create invite link
    invite_link = f"{frontend_url}/invites?invite_id={invite_id}"
    
    # Email template
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Organization Invitation - TeachMe AI</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .button:hover {{ background: #5a6fd8; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎓 TeachMe AI</h1>
                <h2>Organization Invitation</h2>
            </div>
            <div class="content">
                <h3>You've been invited to join an organization!</h3>
                <p>Hello,</p>
                <p>You have been invited to join <strong>{org_name}</strong> as an <strong>Organization Administrator</strong> on TeachMe AI.</p>
                
                <p>As an Organization Administrator, you will be able to:</p>
                <ul>
                    <li>Manage your organization's settings</li>
                    <li>Invite teachers and students</li>
                    <li>Create and manage courses</li>
                    <li>Monitor learning progress</li>
                </ul>
                
                <p>Click the button below to accept or reject this invitation:</p>
                
                <div style="text-align: center;">
                    <a href="{invite_link}" class="button">View Invitation</a>
                </div>
                
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background: #eee; padding: 10px; border-radius: 5px;">{invite_link}</p>
                
                <p>This invitation will expire in 7 days.</p>
                
                <p>Best regards,<br>The TeachMe AI Team</p>
            </div>
            <div class="footer">
                <p>© 2025 TeachMe AI. All rights reserved.</p>
                <p>If you didn't expect this invitation, you can safely ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_content = f"""
    Organization Invitation - TeachMe AI
    
    You have been invited to join {org_name} as an Organization Administrator.
    
    Click here to view your invitation: {invite_link}
    
    This invitation will expire in 7 days.
    
    Best regards,
    The TeachMe AI Team
    """
    
    message = MessageSchema(
        subject="🎓 Organization Invitation - TeachMe AI",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    try:
        await fastmail.send_message(message)
        print(f"✅ Invite email sent to {email} (org: {org_name}, invite_id: {invite_id})")
        return True
    except Exception as e:
        print(f"❌ Failed to send invite email to {email}: {str(e)}")
        return False


async def send_course_invite_email(email: str, org_name: str, course_title: str, token: str, frontend_url: str = "http://localhost:3000"):
    """Send course enrollment invite email with token link"""
    enroll_link = f"{frontend_url}/courses/enroll?token={token}"
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset=\"utf-8\">
        <title>Course Invitation - TeachMe AI</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .button:hover {{ background: #5a6fd8; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class=\"container\">
            <div class=\"header\">
                <h1>🎓 TeachMe AI</h1>
                <h2>Course Invitation</h2>
            </div>
            <div class=\"content\">
                <h3>You've been invited to join a course!</h3>
                <p>Hello,</p>
                <p>You have been invited to join <strong>{course_title}</strong> in the organization <strong>{org_name}</strong>.</p>
                <div style=\"text-align: center;\">
                    <a href=\"{enroll_link}\" class=\"button\">Join Course</a>
                </div>
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style=\"word-break: break-all; background: #eee; padding: 10px; border-radius: 5px;\">{enroll_link}</p>
                <p>This link will expire in a limited time.</p>
                <p>Best regards,<br>The TeachMe AI Team</p>
            </div>
            <div class=\"footer\">
                <p>© 2025 TeachMe AI. All rights reserved.</p>
            </div>
        </div>
    </body>
    </html>
    """
    message = MessageSchema(
        subject="🎓 Course Invitation - TeachMe AI",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    try:
        await fastmail.send_message(message)
        print(f"✅ Course invite email sent to {email} (org: {org_name}, course: {course_title})")
        return True
    except Exception as e:
        print(f"❌ Failed to send course invite to {email}: {str(e)}")
        return False
