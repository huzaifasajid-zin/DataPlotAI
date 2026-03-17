"""General application tests."""
import pytest
from app import create_app
from models import db, User


class TestAppCreation:
    """Test Flask app creation and initialization."""
    
    def test_app_creates_successfully(self, app):
        """Test that app can be created."""
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_app_has_secret_key(self, app):
        """Test that app has a secret key configured."""
        assert app.secret_key is not None
    
    def test_app_database_configured(self, app):
        """Test that database is configured."""
        assert 'SQLALCHEMY_DATABASE_URI' in app.config
        assert 'sqlite:///' in app.config['SQLALCHEMY_DATABASE_URI']


class TestDatabase:
    """Test database operations."""
    
    def test_database_creates_tables(self, app):
        """Test that database tables are created."""
        with app.app_context():
            # Tables should exist after app creation
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            assert 'user' in tables
            assert 'scrape_task' in tables
            assert 'job_listing' in tables
            assert 'automation_schedule' in tables
    
    def test_database_session_management(self, app):
        """Test proper database session handling."""
        with app.app_context():
            user = User(
                name='Huzaifa Sajid', # type: ignore
                email='testing@test.com',    # type: ignore
                password_hash='hash' # type: ignore
            )
            db.session.add(user)
            db.session.commit()
            
            user_id = user.id
            retrieved_user = User.query.get(user_id)
            assert retrieved_user is not None
            assert retrieved_user.email == 'testing@test.com'


class TestErrorHandling:
    """Test error handling."""
    
    def test_404_on_invalid_route(self, client):
        """Test 404 error on invalid route."""
        response = client.get('/invalid/route/that/does/not/exist')
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        pass


class TestContextManagement:
    """Test Flask app context management."""
    
    def test_app_context_available(self, app_context):
        """Test that app context is properly managed."""
        from flask import current_app
        assert current_app is not None
    
    def test_database_available_in_context(self, app_context):
        """Test that database is available in app context."""
        from flask_sqlalchemy import SQLAlchemy
        assert db is not None
        
        # Should be able to query
        users = User.query.all()
        assert isinstance(users, list)
