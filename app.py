import os
from datetime import datetime
from threading import Thread
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import threading
import csv
from io import StringIO
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response, session
from models import db, ScrapeTask, JobListing, AutomationSchedule, ProfileListing
from visualization.charts import Visualizer
from scrapers.job_scraper import JobScraper
from authentication import auth_bp, login_required
from automation.scheduler import init_scheduler

def create_app():
    app = Flask(__name__)
    

    basedir = os.path.abspath(os.path.dirname(__file__))
    app.secret_key = os.environ.get('SECRET_KEY', 'develop_secret_key_123')
    
    # Database Configuration
    database_url = os.environ.get("DATABASE_URL")
    sqlite_url = "sqlite:///" + os.path.join(basedir, 'data', 'data.db')
    
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        # If running locally and using a Render internal hostname, fix it for external access
        if not os.environ.get('RENDER') and "dpg-" in database_url and ".render.com" not in database_url:
            from urllib.parse import urlparse, urlunparse
            parsed = urlparse(database_url)
            if parsed.hostname:
                new_hostname = f"{parsed.hostname}.oregon-postgres.render.com"
                new_netloc = parsed.netloc.replace(parsed.hostname, new_hostname)
                database_url = urlunparse(parsed._replace(netloc=new_netloc))
                print(f"Fixed Render internal URL for external access: {new_hostname}")

        # Check if psycopg2 driver is available for PostgreSQL
        if "postgresql" in database_url:
            try:
                import psycopg2
                app.config['SQLALCHEMY_DATABASE_URI'] = database_url
                print(f"Using PostgreSQL database: {database_url.split('@')[-1]}") 
            except ImportError:
                print("PostgreSQL driver 'psycopg2' not found. Falling back to SQLite.")
                app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_url
        else:
            app.config['SQLALCHEMY_DATABASE_URI'] = database_url
            print(f"Using database: {database_url}")
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_url
        print(f"Using SQLite database: {sqlite_url}")
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    # Register Authentication Blueprint
    app.register_blueprint(auth_bp)
    
    # Register Admin Blueprint
    from admin import admin_bp
    app.register_blueprint(admin_bp)
    
    # Create necessary folders
    os.makedirs(os.path.join(basedir, 'data'), exist_ok=True)
    
    # Ensure tables are created and start scheduler
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database creation failed: {e}")
            if app.config['SQLALCHEMY_DATABASE_URI'] != sqlite_url:
                print("Falling back to SQLite...")
                app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_url
                # No easy way to re-init db extension here without potential side effects, 
                # but for simple apps, this fallback is a good safety net.
                # In most cases, the next request will trigger engine creation with the new URI if the first failed.
                try:
                    db.create_all()
                except Exception as e2:
                    print(f"SQLite fallback also failed: {e2}")
        
    init_scheduler(app)
        
    @app.route('/')
    def index():
        if 'user_id' in session:
            return redirect(url_for('scraper_app'))
        return render_template('home.html')
        
    @app.route('/app')
    @login_required
    def scraper_app():
        user_id = session.get('user_id')
        tasks = ScrapeTask.query.filter_by(user_id=user_id).order_by(ScrapeTask.created_at.desc()).limit(10).all()
        return render_template('index.html', recent_tasks=tasks)

    @app.route('/dashboard')
    @login_required
    def dashboard():
        user_id = session.get('user_id')
        location_chart = Visualizer.generate_location_chart(user_id=user_id)
        company_chart = Visualizer.generate_company_chart(user_id=user_id)
        timeline_chart = Visualizer.generate_timeline_chart(user_id=user_id)
        total_jobs = JobListing.query.join(ScrapeTask).filter(ScrapeTask.user_id == user_id).count()
        total_tasks = ScrapeTask.query.filter_by(user_id=user_id).count()
        
        # Calculate some fake delta metrics for the UI like in the reference
        earnings = total_jobs * 150 # Arbitrary metric based on jobs
        sales = total_tasks * 24
        revenue = total_jobs * 115
        
        return render_template('dashboard.html', 
                               location_chart=location_chart, 
                               company_chart=company_chart,
                               timeline_chart=timeline_chart,
                               total_jobs=total_jobs,
                               total_tasks=total_tasks,
                               earnings=earnings,
                               sales=sales,
                               revenue=revenue)

    @app.route('/jobs')
    @login_required
    def jobs_view():
        user_id = session.get('user_id')
        jobs = JobListing.query.join(ScrapeTask).filter(ScrapeTask.user_id == user_id).order_by(JobListing.date_posted.desc(), JobListing.id.desc()).all()
        return render_template('jobs.html', jobs=jobs)
        
    @app.route('/automations')
    @login_required
    def automations_view():
        autos = AutomationSchedule.query.filter_by(user_id=session['user_id']).order_by(AutomationSchedule.created_at.desc()).all()
        return render_template('automations.html', automations=autos)

    @app.route('/profiles')
    @login_required
    def profiles_view():
        user_id = session.get('user_id')
        profiles = ProfileListing.query.join(ScrapeTask).filter(ScrapeTask.user_id == user_id).order_by(ProfileListing.created_at.desc(), ProfileListing.id.desc()).all()
        return render_template('profiles.html', profiles=profiles)

    @app.route('/export/jobs')
    @login_required
    def export_jobs():
        user_id = session.get('user_id')
        jobs = JobListing.query.join(ScrapeTask).filter(ScrapeTask.user_id == user_id).all()
        
        def generate():
            data = StringIO()
            writer = csv.writer(data)
            writer.writerow(('ID', 'Task ID', 'Title', 'Company', 'Location', 'Price/Salary', 'Link', 'Date Posted', 'Source'))
            yield data.getvalue()
            data.seek(0)
            data.truncate(0)
            
            for job in jobs:
                writer.writerow((
                    job.id, job.task_id, job.title, job.company, job.location, 
                    job.price_or_salary, job.link, job.date_posted, job.source
                ))
                yield data.getvalue()
                data.seek(0)
                data.truncate(0)

        response = Response(generate(), mimetype='text/csv')
        response.headers.set("Content-Disposition", "attachment", filename="jobs_export.csv")
        return response

    @app.route('/api/automations', methods=['POST'])
    @login_required
    def create_automation():
        data = request.json
        keyword = data.get('keyword')
        freq = data.get('frequency')
        location = data.get('location')
        company = data.get('company')
        time_period = data.get('time_period')
        salary = data.get('salary')
        task_type = data.get('task_type', 'job')
        
        if not keyword or not freq:
            return jsonify({'error': 'Keyword and frequency are required'}), 400
            
        auto = AutomationSchedule(
            user_id=session.get('user_id'), # type: ignore
            keyword=keyword, # type: ignore
            location=location, # type: ignore
            company=company, # type: ignore
            time_period=time_period, # type: ignore
            salary=salary, # type: ignore
            experience=data.get('experience'), # type: ignore
            task_type=task_type, # type: ignore
            frequency=freq # type: ignore
        )
        db.session.add(auto)
        db.session.commit()
        return jsonify({'message': 'Automation created successfully'}), 200

    @app.route('/api/automations/<int:auto_id>/toggle', methods=['PUT'])
    @login_required
    def toggle_automation(auto_id):
        auto = AutomationSchedule.query.filter_by(id=auto_id, user_id=session['user_id']).first_or_404()
        auto.is_active = not auto.is_active
        db.session.commit()
        return jsonify({'message': f"Automation {'activated' if auto.is_active else 'paused'}", 'status': auto.is_active})

    @app.route('/api/automations/<int:auto_id>', methods=['DELETE'])
    @login_required
    def delete_automation(auto_id):
        auto = AutomationSchedule.query.filter_by(id=auto_id, user_id=session['user_id']).first_or_404()
        db.session.delete(auto)
        db.session.commit()
        return jsonify({'message': 'Automation deleted successfully'}), 200

    @app.route('/api/delete_task/<int:task_id>', methods=['DELETE'])
    @login_required
    def delete_task(task_id):
        try:
            task = ScrapeTask.query.filter_by(id=task_id, user_id=session.get('user_id')).first_or_404()
            JobListing.query.filter_by(task_id=task.id).delete()
            ProfileListing.query.filter_by(task_id=task.id).delete()
            db.session.delete(task)
            db.session.commit()
            return jsonify({'message': 'Task deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    def run_scraper(app, task_id, keyword):
        with app.app_context():
            try:
                task = ScrapeTask.query.get(task_id)
                if task is None:
                    print(f"Task with ID {task_id} not found.")
                    return
                task.status = 'running'
                db.session.commit()
                
                if getattr(task, 'task_type', 'job') == 'profile':
                    from scrapers.profile_scraper import ProfileScraper
                    scraper = ProfileScraper(task_id=task_id)
                else:
                    scraper = JobScraper(task_id=task_id)
                    
                count = scraper.scrape(keyword)
                
                task.status = 'completed'
                db.session.commit()
                print(f"Scraping completed for '{keyword}'. Found {count} results.")
            except Exception as e:
                print(f"Scraping failed: {e}")
                
    @app.route('/api/trigger_scrape', methods=['POST'])
    @login_required
    def trigger_scrape():
        data = request.json
        keyword = data.get('keyword')
        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400
            
        task = ScrapeTask()
        task.user_id = session.get('user_id')
        task.keyword = keyword
        task.location = data.get('location')
        task.company = data.get('company')
        task.time_period = data.get('time_period')
        task.salary = data.get('salary')
        task.experience = data.get('experience')
        task.task_type = data.get('task_type', 'job')
        task.status = 'pending'

        db.session.add(task)
        db.session.commit()
        
        thread = threading.Thread(target=run_scraper, args=(app, task.id, keyword))
        thread.start()
        
        return jsonify({'message': 'Scrape task triggered successfully', 'task_id': task.id})

    @app.route('/api/task_status/<int:task_id>')
    @login_required
    def task_status(task_id):
        task = ScrapeTask.query.filter_by(id=task_id, user_id=session.get('user_id')).first_or_404()
        return jsonify({'status': task.status, 'keyword': task.keyword, 'task_type': getattr(task, 'task_type', 'job')})

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
    
    # For PythonAnywhere deployment, in WSGI file:
    # import sys
    # project_home = '/home/Huzaifa965/DataPlotAI'
    # if project_home not in sys.path:
    #     sys.path = [project_home] + sys.path
    # from app import create_app
    # application = create_app()
