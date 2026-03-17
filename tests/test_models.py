"""Tests for database models."""
import pytest
from models import db, User, ScrapeTask, JobListing, AutomationSchedule
from datetime import datetime


class TestUserModel:
    """Test User model."""
    
    def test_create_user(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                name='John Doe', # type: ignore
                email='john@example.com', # type: ignore
                password_hash='hashed_pass', # type: ignore
                purpose='Job Search' # type: ignore
            )
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.email == 'john@example.com'
            assert user.name == 'John Doe'
            assert user.is_admin is False
    
    def test_user_unique_email(self, app):
        """Test that emails must be unique."""
        with app.app_context():
            user1 = User(
                name='User 1', # type: ignore
                email='unique@example.com', # type: ignore
                password_hash='pass1' # type: ignore
            )
            user2 = User(
                name='User 2', # type: ignore
                email='unique@example.com', # type: ignore
                password_hash='pass2' # type: ignore
            )
            db.session.add(user1)
            db.session.commit()
            
            db.session.add(user2)
            with pytest.raises(Exception):
                db.session.commit()


class TestScrapeTaskModel:
    """Test ScrapeTask model."""
    
    def test_create_scrape_task(self, app, test_user):
        """Test creating a scrape task."""
        with app.app_context():
            task = ScrapeTask(
                user_id=test_user.id, # type: ignore
                keyword='python jobs', # type: ignore
                location='New York', # type: ignore
                status='pending' # type: ignore
            )
            db.session.add(task)
            db.session.commit()
            
            assert task.id is not None
            assert task.keyword == 'python jobs'
            assert task.status == 'pending'
            assert task.created_at is not None
    
    def test_scrape_task_default_status(self, app, test_user):
        """Test that task status defaults to 'pending'."""
        with app.app_context():
            task = ScrapeTask(
                user_id=test_user.id, # type: ignore
                keyword='test' # type: ignore
            )
            db.session.add(task)
            db.session.commit()
            
            assert task.status == 'pending'


class TestJobListingModel:
    """Test JobListing model."""
    
    def test_create_job_listing(self, app, test_user_with_tasks):
        """Test creating a job listing."""
        with app.app_context():
            task = ScrapeTask.query.first()
            job = JobListing(
                task_id=task.id, # type: ignore
                title='Senior Developer',# type: ignore
                company='TechCorp',# type: ignore
                location='San Francisco',# type: ignore
                price_or_salary='$150k-$200k',# type: ignore
                link='https://example.com/job',# type: ignore
                date_posted='2024-01-20'# type: ignore
            )
            db.session.add(job)
            db.session.commit()
            
            assert job.id is not None
            assert job.title == 'Senior Developer'
            assert job.company == 'TechCorp'


class TestAutomationScheduleModel:
    """Test AutomationSchedule model."""
    
    def test_create_automation(self, app, test_user):
        """Test creating an automation schedule."""
        with app.app_context():
            auto = AutomationSchedule(
                user_id=test_user.id,# type: ignore
                keyword='python',# type: ignore
                frequency='daily',# type: ignore
                location='Remote'# type: ignore
            )
            db.session.add(auto)
            db.session.commit()
            
            assert auto.id is not None
            assert auto.keyword == 'python'
            assert auto.frequency == 'daily'
            assert auto.is_active is True
    
    def test_automation_defaults(self, app, test_user):
        """Test automation schedule defaults."""
        with app.app_context():
            auto = AutomationSchedule(
                user_id=test_user.id,# type: ignore
                keyword='test',# type: ignore
                frequency='weekly'# type: ignore
            )
            db.session.add(auto)
            db.session.commit()
            
            assert auto.is_active is True
            assert auto.last_run is None
