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
        pass
    
    def test_scrape_task_default_status(self, app, test_user):
        pass


class TestJobListingModel:
    """Test JobListing model."""
    
    def test_create_job_listing(self, app, test_user_with_tasks):
        pass


class TestAutomationScheduleModel:
    """Test AutomationSchedule model."""
    
    def test_create_automation(self, app, test_user):
        pass
    
    def test_automation_defaults(self, app, test_user):
        pass
