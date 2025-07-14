from flask import Flask, request
from flask_login import LoginManager
from flask_session import Session
import os
from dotenv import load_dotenv
from .models import db, User
from flask_wtf import CSRFProtect

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
    
    # Session configuration
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['PERMANENT_SESSION_LIFETIME'] = 30 * 24 * 60 * 60  # 30 days
    # Only enable secure cookies in production
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # Database configuration
    if os.getenv('DATABASE_URL'):
        app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL').replace('postgres://', 'postgresql://')
    else:
        # Use absolute path for SQLite database
        instance_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
        os.makedirs(instance_path, exist_ok=True)
        db_path = os.path.join(instance_path, 'budgetmate.db')
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)
    Session(app)  # Initialize Flask-Session
    login_manager = LoginManager(app)
    login_manager.login_view = 'main.login'
    csrf = CSRFProtect(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints
    from .routes import main
    app.register_blueprint(main)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Add template filter for mobile detection
    @app.template_filter('mobile_template')
    def mobile_template(template_name):
        if is_mobile():
            # Try to load mobile-specific template first
            mobile_template = f"mobile/{template_name}"
            try:
                app.jinja_env.get_template(mobile_template)
                return mobile_template
            except:
                return template_name
        return template_name

    def is_mobile():
        user_agent = request.headers.get('User-Agent', '').lower()
        mobile_agents = ['iphone', 'android', 'mobile', 'tablet', 'ipad']
        return any(agent in user_agent for agent in mobile_agents)

    # Register the function to be available in templates
    app.jinja_env.globals.update(is_mobile=is_mobile)

    return app

app = create_app()
