import threading
from apscheduler.schedulers.background import BackgroundScheduler
from models import db, AutomationSchedule, ScrapeTask
from scrapers.job_scraper import JobScraper
from datetime import datetime, timedelta

def run_scraper(app, task_id, keyword):
    """Background execution string for a single scraping job"""
    with app.app_context():
        try:
            task = ScrapeTask.query.get(task_id)
            if task is None:
                print(f"[Scheduler] Task with ID {task_id} not found.")
                return
            task.status = 'running'
            db.session.commit()
            
            scraper = JobScraper(task_id=task_id)
            count = scraper.scrape(keyword)
            
            task.status = 'completed'
            db.session.commit()
            print(f"[Scheduler] Scraping completed for '{keyword}'. Found {count} jobs.")
            
            # Trigger Email Notification
            from email_service import send_scrape_completion_email
            from models import User
            if task.user_id:
                user = User.query.get(task.user_id)
                if user:
                    send_scrape_completion_email(user, task, count)
        except Exception as e:
            print(f"[Scheduler] Scraping failed: {e}")
            if task:
                task.status = 'failed'
                db.session.commit()

def check_and_run_automations(app):
    """Monitors the active 'AutomationSchedule' entries in the database and runs due tasks."""
    print(f"[{datetime.utcnow()}] Checking for due automations...")
    with app.app_context():
        now = datetime.utcnow()
        active_automations = AutomationSchedule.query.filter_by(is_active=True).all()
        
        for auto in active_automations:
            # Determine if it's due
            due = False
            if not auto.last_run:
                due = True
            else:
                elapsed = now - auto.last_run
                if auto.frequency == 'minutely' and elapsed >= timedelta(minutes=1):
                    due = True
                elif auto.frequency == 'hourly' and elapsed >= timedelta(hours=1):
                    due = True
                elif auto.frequency == 'daily' and elapsed >= timedelta(days=1):
                    due = True
                elif auto.frequency == 'weekly' and elapsed >= timedelta(days=7):
                    due = True
            
            if due:
                print(f"[Scheduler] Automation {auto.id} for '{auto.keyword}' is due. Triggering...")
                
                # Auto generate a ScrapeTask and run it
                task = ScrapeTask(
                    keyword=auto.keyword,
                    location=auto.location,
                    company=auto.company,
                    time_period=auto.time_period,
                    salary=auto.salary,
                    status='pending',
                    user_id=auto.user_id
                )
                db.session.add(task)
                
                # Update last run
                auto.last_run = now
                db.session.commit()
                
                # Spawn scraper thread
                thread = threading.Thread(target=run_scraper, args=(app, task.id, auto.keyword))
                thread.start()

def init_scheduler(app):
    """Initializes APScheduler with the check_and_run_automations job bound to Flask context"""
    scheduler = BackgroundScheduler(daemon=True)
    # Ping the database every 60 seconds to see if any schedule is due
    scheduler.add_job(func=lambda: check_and_run_automations(app), trigger="interval", seconds=60)
    scheduler.start()
    print("[Scheduler] Startup Complete: Automations Background Engine is running.")
