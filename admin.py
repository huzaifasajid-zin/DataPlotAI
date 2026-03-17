from flask import Blueprint, render_template, session, redirect, url_for, flash, request, jsonify
from functools import wraps
from models import db, User, ScrapeTask, JobListing, AutomationSchedule

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('You do not have permission to access the admin panel.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.before_request
@admin_required
def before_request():
    pass # All routes in this blueprint require admin

@admin_bp.route('/')
def admin_dashboard():
    total_users = User.query.count()
    total_tasks = ScrapeTask.query.count()
    total_jobs = JobListing.query.count()
    total_automations = AutomationSchedule.query.count()
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                           total_users=total_users,
                           total_tasks=total_tasks,
                           total_jobs=total_jobs,
                           total_automations=total_automations,
                           recent_users=recent_users)

@admin_bp.route('/users')
def manage_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/api/users/<int:user_id>/toggle_admin', methods=['POST'])
def toggle_admin(user_id):
    # Prevent self-demotion
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot change your own admin status'}), 400
        
    user = User.query.get_or_404(user_id)
    user.is_admin = not user.is_admin
    db.session.commit()
    return jsonify({'message': f"User {user.email} admin status set to {user.is_admin}", 'is_admin': user.is_admin})

@admin_bp.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if user_id == session['user_id']:
        return jsonify({'error': 'Cannot delete yourself'}), 400
        
    user = User.query.get_or_404(user_id)
    # Delete their automations
    AutomationSchedule.query.filter_by(user_id=user.id).delete()
    # Scrape tasks are currently not linked directly to users in the DB schema, 
    # but in a complete system they would be, so they could be deleted here too.
    
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted successfully'})
