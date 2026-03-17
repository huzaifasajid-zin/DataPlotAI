"""Pytest configuration and fixtures."""
import pytest
import tempfile
import os
from app import create_app
from models import db, User, ScrapeTask, JobListing, AutomationSchedule


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    # Create a temporary database file
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def app_context(app):
    """Provide an app context."""
    with app.app_context():
        yield


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(
            name='Test User',# type: ignore
            email='test@example.com',# type: ignore
            password_hash='hashed_password_here',# type: ignore
            purpose='Testing'# type: ignore
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_user_with_tasks(app, test_user):
    """Create a test user with scrape tasks."""
    with app.app_context():
        task = ScrapeTask(
            user_id=test_user.id,# type: ignore
            keyword='python',# type: ignore
            location='Remote',# type: ignore
            status='completed'# type: ignore
        )
        db.session.add(task)
        db.session.commit()
        
        job = JobListing(
            task_id=task.id,# type: ignore
            title='Python Developer',# type: ignore
            company='Tech Corp',# type: ignore
            location='Remote',# type: ignore
            price_or_salary='$100k-$150k',# type: ignore
            link='https://example.com/job1',# type: ignore
            date_posted='2024-01-15',# type: ignore
            source='LinkedIn'# type: ignore
        )
        db.session.add(job)
        db.session.commit()
        
        return test_user


@pytest.fixture
def logged_in_client(client, app, test_user):
    """Create a logged-in test client."""
    with client:
        with app.app_context():
            # Simulate login by setting session
            with client.session_transaction() as sess:
                sess['user_id'] = test_user.id
            yield client
