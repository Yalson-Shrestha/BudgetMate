from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from .models import db, User, Transaction
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
from sqlalchemy import extract, func
from urllib.parse import quote

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if email already exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please use a different email or login.')
            return redirect(url_for('main.signup'))
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            flash('Username already taken. Please choose a different username.')
            return redirect(url_for('main.signup'))

        # Create new user
        user = User(
            username=username,
            email=email,
            password=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        flash('Signup successful! Please log in.')
        return redirect(url_for('main.login'))
    return render_template('signup.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('main.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Get current month's transactions
    current_month = date.today().month
    current_year = date.today().year
    today = date.today()
    now = datetime.now()
    
    # Get all transactions for the current month
    monthly_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).order_by(Transaction.date.desc()).all()
    
    # Get all transactions for the current day
    daily_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date == today
    ).order_by(Transaction.date.desc()).all()
    
    # Calculate monthly totals
    monthly_income = sum(t.amount for t in monthly_transactions if t.type == 'income')
    monthly_expenses = sum(t.amount for t in monthly_transactions if t.type == 'expense')
    monthly_balance = monthly_income - monthly_expenses
    
    # Calculate daily totals
    daily_income = sum(t.amount for t in daily_transactions if t.type == 'income')
    daily_expenses = sum(t.amount for t in daily_transactions if t.type == 'expense')
    
    # Get category-wise monthly expenses
    category_expenses = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).group_by(Transaction.category).all()
    
    # Get category-wise monthly income
    category_income = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).group_by(Transaction.category).all()
    
    return render_template('dashboard.html',
        daily_transactions=daily_transactions,
        monthly_transactions=monthly_transactions,
        daily_income=daily_income,
        daily_expenses=daily_expenses,
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_balance=monthly_balance,
        category_expenses=category_expenses,
        category_income=category_income,
        current_month=datetime(current_year, current_month, 1).strftime('%B %Y'),
        today=today,
        now=now
    )

@main.route('/add', methods=['POST'])
@login_required
def add_transaction():
    t = Transaction(
        amount=float(request.form['amount']),
        category=request.form['category'],
        type=request.form['type'],
        note=request.form.get('note', ''),
        user_id=current_user.id
    )
    db.session.add(t)
    db.session.commit()
    return redirect(url_for('main.dashboard'))

@main.route('/chart')
@login_required
def chart():
    # Get current month's transactions
    current_month = date.today().month
    current_year = date.today().year
    
    # Get category-wise monthly expenses
    category_expenses = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'expense',
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).group_by(Transaction.category).all()
    
    # Convert expense data to list of lists for JSON serialization
    expense_data = [[row[0], float(row[1])] for row in category_expenses]
    
    # Get category-wise monthly income
    category_income = db.session.query(
        Transaction.category,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.user_id == current_user.id,
        Transaction.type == 'income',
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).group_by(Transaction.category).all()
    
    # Convert income data to list of lists for JSON serialization
    income_data = [[row[0], float(row[1])] for row in category_income]
    
    return render_template('chart.html',
        category_expenses=expense_data,
        category_income=income_data,
        current_month=datetime(current_year, current_month, 1).strftime('%B %Y')
    )

@main.route('/help')
@login_required
def help():
    return render_template('help.html')

@main.route('/feedback')
@login_required
def feedback():
    return render_template('feedback.html')
