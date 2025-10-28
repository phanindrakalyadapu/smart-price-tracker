import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings
import traceback
from app.services.ai_analysis import analyze_product_with_gpt
import asyncio

async def send_welcome_email(email_to: str, first_name: str):
    try:
        print(f"📨 Sending welcome email to {email_to}...")

        # Create email
        subject = "Welcome to Smart Price Tracker!"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Hi {first_name},</h2>
                <p>Thank you for registering with <b>Smart Price Tracker</b>! 🎉</p>
                <p>You’ll now receive real-time alerts when product prices change.</p>
                <p>– The Smart Price Tracker Team</p>
            </body>
        </html>
        """

        # Build email
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.MAIL_FROM
        message["To"] = email_to
        message.attach(MIMEText(html_content, "html"))

        # Connect to Gmail SMTP (use MAIL_SERVER / MAIL_PORT from your settings)
        server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
        server.starttls()
        server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
        server.sendmail(settings.MAIL_FROM, email_to, message.as_string())
        server.quit()

        print("✅ Welcome email sent successfully!")

    except Exception as e:
        print(f"❌ EMAIL ERROR: {e}")
        print(traceback.format_exc())

def _send_html(to_email: str, subject: str, html: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.MAIL_FROM
    msg["To"] = to_email
    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT)
    server.starttls()
    server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
    server.sendmail(settings.MAIL_FROM, to_email, msg.as_string())
    server.quit()

async def send_price_change_email(
        to_email: str, 
        first_name: str, 
        product_name: str, 
        product_url: str, 
        old_price: float, 
        new_price: float, 
        ai_summary: str = None, 
        review_summary: str = None,
    ):
    try:
        direction = "dropped" if new_price < (old_price or new_price) else "increased"
        subject = f"Price {direction}: {product_name}"

        html = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6;">
            <h3>Hi {first_name}, 👋</h3>
            <p>The price for <b>{product_name}</b> has 
               <b style="color:{'green' if direction=='dropped' else 'red'};">{direction}</b>.</p>
            <p><b>Old Price:</b> ${old_price:.2f} &nbsp;&nbsp; <b>New Price:</b> ${new_price:.2f}</p>

            <p><a href="{product_url}" style="color:#4f46e5; text-decoration:none;">View Product</a></p>

            <hr style="margin: 20px 0;">
            <h4 style="color:#4f46e5; margin-bottom:5px;">AI Insight 🧠</h4>
            <p style="margin-top:0;">{ai_summary or 'AI analysis unavailable.'}</p>

            <h4 style="color:#10b981; margin-bottom:5px;">Review Analysis 💬</h4>
            <p style="margin-top:0;">{review_summary or 'Review summary unavailable.'}</p>

            <hr style="margin: 20px 0;">
            <p style="font-size:14px; color:gray;">– Smart Price Tracker Team 🚀</p>
        </body>
        </html>
        """
        # Run blocking send in background thread
        await asyncio.to_thread(_send_html, to_email, subject, html)

        print(f"✅ Price change email sent to {to_email}")

    except Exception as e:
        print("❌ EMAIL ERROR (price change):", e)
        print(traceback.format_exc())

def send_product_added_email(to_email: str, first_name: str, product_name: str, product_url: str, current_price: float):
    """
    Sends an email to the user confirming that a product has been added successfully.
    Synchronous & uses the same SMTP path as _send_html.
    """
    try:
        subject = f"✅ {product_name} added successfully!"
        html_content = f"""
        <div style="font-family: Arial, sans-serif;">
            <h2>Hi {first_name}, 👋</h2>
            <p>Great news! The product <strong>{product_name}</strong> has been successfully added to your Smart Price Tracker watchlist.</p>
            <p><b>Current Price:</b> ${float(current_price):.2f}</p>
            <p><a href="{product_url}">View Product</a></p>
            <hr>
            <p>We'll automatically notify you if we detect any change in this product's price.</p>
            <p>– Smart Price Tracker Team 🚀</p>
        </div>
        """
        _send_html(to_email, subject, html_content)
        print(f"📨 Product added email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send product added email: {str(e)}")


