"""Tests for Flask API endpoints."""
import pytest
import json
from models import db, ScrapeTask, AutomationSchedule


class TestAppRoutes:
    """Test main app routes."""
    
    def test_index_redirect_when_logged_in(self, logged_in_client):
        """Test that logged-in users are redirected from index."""
        response = logged_in_client.get('/')
        assert response.status_code == 302
        assert 'app' in response.location
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/dashboard', follow_redirects=False)
        # Should redirect to login or return 401/302
        assert response.status_code in [301, 302, 401]
    
    def test_jobs_view_requires_login(self, client):
        """Test that jobs view requires authentication."""
        response = client.get('/jobs', follow_redirects=False)
        assert response.status_code in [301, 302, 401]
    
    def test_automations_view_requires_login(self, client):
        """Test that automations view requires authentication."""
        response = client.get('/automations', follow_redirects=False)
        assert response.status_code in [301, 302, 401]
    
    def test_export_jobs_requires_login(self, client):
        """Test that export endpoint requires authentication."""
        response = client.get('/export/jobs', follow_redirects=False)
        assert response.status_code in [301, 302, 401]


class TestAPIAutomations:
    """Test automation API endpoints."""
    
    def test_create_automation_success(self, logged_in_client, app, test_user):
        """Test creating an automation successfully."""
        data = {
            'keyword': 'python developer',
            'frequency': 'daily',
            'location': 'Remote',
            'company': 'Google',
            'time_period': 'last_week',
            'salary': '$100k-$150k'
        }
        response = logged_in_client.post(
            '/api/automations',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 200
        assert 'Automation created successfully' in response.get_json().get('message', '')
        
        with app.app_context():
            auto = AutomationSchedule.query.filter_by(user_id=test_user.id).first()
            assert auto is not None
            assert auto.keyword == 'python developer'
    
    def test_create_automation_missing_keyword(self, logged_in_client):
        """Test creating automation without keyword fails."""
        data = {
            'frequency': 'daily'
        }
        response = logged_in_client.post(
            '/api/automations',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400
        assert 'required' in response.get_json().get('error', '').lower()
    
    def test_create_automation_missing_frequency(self, logged_in_client):
        """Test creating automation without frequency fails."""
        data = {
            'keyword': 'python'
        }
        response = logged_in_client.post(
            '/api/automations',
            data=json.dumps(data),
            content_type='application/json'
        )
        assert response.status_code == 400
    
    def test_create_automation_requires_login(self, client):
        """Test that create automation requires authentication."""
        data = {'keyword': 'python', 'frequency': 'daily'}
        response = client.post(
            '/api/automations',
            data=json.dumps(data),
            content_type='application/json',
            follow_redirects=False
        )
        assert response.status_code in [301, 302, 401]
    
    def test_toggle_automation_success(self, logged_in_client, app, test_user):
        """Test toggling automation active status."""
        with app.app_context():
            auto = AutomationSchedule(
                user_id=test_user.id, # type: ignore
                keyword='python', # type: ignore
                frequency='daily', # type: ignore
                is_active=True # type: ignore
            )
            db.session.add(auto)
            db.session.commit()
            auto_id = auto.id
        
        # Authenticate the client with the test user
        logged_in_client.set_cookie('.session', test_user.session_id)
        
        response = logged_in_client.put(f'/api/automations/{auto_id}/toggle')
        assert response.status_code == 200
        
        with app.app_context():
            updated_auto = AutomationSchedule.query.get(auto_id)
            assert updated_auto.is_active is False # type: ignore
    
    def test_toggle_automation_not_found(self, logged_in_client):
        """Test toggling non-existent automation."""
        response = logged_in_client.put('/api/automations/9999/toggle')
        assert response.status_code == 404


class TestExportJobs:
    """Test job export functionality."""
    
    def test_export_jobs_csv_header(self, logged_in_client, test_user_with_tasks):
        """Test that exported CSV has correct headers."""
        response = logged_in_client.get('/export/jobs')
        assert response.status_code == 200
        assert response.content_type == 'text/csv; charset=utf-8'
        assert b'ID,Task ID,Title,Company,Location' in response.data
    
    def test_export_jobs_includes_data(self, logged_in_client, test_user_with_tasks):
        """Test that exported CSV includes job data."""
        response = logged_in_client.get('/export/jobs')
        assert response.status_code == 200
        assert b'Python Developer' in response.data
        assert b'Tech Corp' in response.data


class TestScrapeAPI:
    """Test scraping API endpoints (if they exist)."""
    
    def test_scrape_endpoint_requires_login(self, client):
        """Test that scrape endpoints require authentication."""
        data = {'keyword': 'python'}
        response = client.post(
            '/api/trigger_scrape',
            data=json.dumps(data),
            content_type='application/json',
            follow_redirects=False
        )
        # Either requires login or endpoint doesn't exist
        assert response.status_code in [301, 302, 401, 404]
