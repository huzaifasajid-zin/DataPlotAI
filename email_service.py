import os
import smtplib
import csv
import io
from email.message import EmailMessage
from models import JobListing

def send_scrape_completion_email(user, task, count):
    """
    Sends an email to the user when a scraping task is completed.
    Attaches a CSV of the scraped results.
    """
    smtp_server = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("MAIL_PORT", 587))
    smtp_user = os.environ.get("MAIL_USERNAME")
    smtp_pass = os.environ.get("MAIL_PASSWORD")
    sender_email = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@datapilot.ai")

    subject = f"DataPilot AI: Extraction Complete for '{task.keyword}'"
    
    base_url = os.environ.get("BASE_URL", "http://127.0.0.1:5000")
    report_link = f"{base_url}/dashboard"
    
    body = f"""Hello {user.name},

Your DataPilot AI scraping task for the keyword '{task.keyword}' has completed!

Task Summary:
- Keyword: {task.keyword}
- Location: {task.location or 'Global'}
- New Records Extracted: {count}

Attached is the raw CSV report of the new data. You can also view and analyze the full dataset by logging into your DataPilot AI dashboard here:
{report_link}

Powered by DataPilot AI Autonomous Engine
"""

    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = user.email
    msg.set_content(body)

    # Generate CSV Attachment
    jobs = JobListing.query.filter_by(task_id=task.id).all()
    if jobs:
        csv_buffer = io.StringIO()
        writer = csv.writer(csv_buffer)
        writer.writerow(['Title', 'Company', 'Location', 'Salary/Price', 'Link', 'Date Posted', 'Source'])
        for job in jobs:
            writer.writerow([job.title, job.company, job.location, job.price_or_salary, job.link, job.date_posted, job.source])
        
        csv_data = csv_buffer.getvalue().encode('utf-8')
        msg.add_attachment(csv_data, maintype='text', subtype='csv', filename=f"{task.keyword}_report.csv")

    # If no credentials, simulate sending to console to avoid crashes
    if not smtp_user or not smtp_pass:
        print("====== EMAIL SERVICE (DEVELOPMENT MOCK) ======")
        print(f"To: {user.email}")
        print(f"Subject: {subject}")
        print(f"Body: \n{body}")
        print(f"[Attachment]: {task.keyword}_report.csv generated containing {len(jobs)} rows.")
        print("==============================================")
        print("NOTE: Set MAIL_USERNAME and MAIL_PASSWORD environment variables to send real emails via SMTP.")
        return True

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"[EmailService] Successfully sent completion email to {user.email}")
        return True
    except Exception as e:
        print(f"[EmailService] Failed to send email: {e}")
        return False
