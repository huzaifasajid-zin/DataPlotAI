from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    purpose = db.Column(db.String(255))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    automations = db.relationship('AutomationSchedule', backref='user', lazy=True)

class ScrapeTask(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # made True for migration safety
    keyword = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    company = db.Column(db.String(255))
    time_period = db.Column(db.String(50))
    salary = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending') # pending, running, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class JobListing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('scrape_task.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    company = db.Column(db.String(255))
    location = db.Column(db.String(255))
    price_or_salary = db.Column(db.String(255))
    link = db.Column(db.Text)
    date_posted = db.Column(db.String(100))
    source = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AutomationSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    keyword = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255))
    company = db.Column(db.String(255))
    time_period = db.Column(db.String(50))
    salary = db.Column(db.String(255))
    frequency = db.Column(db.String(50), nullable=False) # 'hourly', 'daily', 'weekly'
    is_active = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
