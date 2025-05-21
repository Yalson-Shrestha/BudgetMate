from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from .models import db, User, Transaction
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime
from sqlalchemy import extract, func

main = Blueprint('main', __name__)

@main.route('/')
def index():
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
    return redirect(url_for('main.index'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Get current month's transactions
    current_month = date.today().month
    current_year = date.today().year
    
    # Get all transactions for the current month
    monthly_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        extract('month', Transaction.date) == current_month,
        extract('year', Transaction.date) == current_year
    ).order_by(Transaction.date.desc()).all()
    
    # Get all transactions for the current day
    today = date.today()
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
        current_month=datetime(current_year, current_month, 1).strftime('%B %Y')
    )

@main.route('/chart')
@login_required
def chart():
    now = datetime.now()
    current_month_start = date(now.year, now.month, 1)

    # Get all current user's transactions for this month
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= current_month_start
    ).all()

    # Separate income and expense
    category_expenses = {}
    category_income = {}

    for t in transactions:
        if t.type == 'expense':
            category_expenses[t.category] = category_expenses.get(t.category, 0) + t.amount
        elif t.type == 'income':
            category_income[t.category] = category_income.get(t.category, 0) + t.amount

    # Convert to list of tuples for easier use in chart
    category_expenses_list = list(category_expenses.items())
    category_income_list = list(category_income.items())

    return render_template(
        'chart.html',
        category_expenses=category_expenses_list,
        category_income=category_income_list
    )


@main.route('/add_transaction', methods=['POST'])
@login_required
def add_transaction():
    amount = request.form.get('amount')
    category = request.form.get('category')
    type_ = request.form.get('type')  # 'income' or 'expense'
    note = request.form.get('note')

    if not amount or not category or not type_:
        flash('Please fill in all required fields.', 'danger')
        return redirect(url_for('main.dashboard'))

    try:
        amount = float(amount)
    except ValueError:
        flash('Invalid amount entered.', 'danger')
        return redirect(url_for('main.dashboard'))

    transaction = Transaction(
        amount=amount,
        category=category,
        type=type_,
        note=note,
        user_id=current_user.id
    )

    db.session.add(transaction)
    db.session.commit()
    flash('Transaction added successfully!', 'success')
    return redirect(url_for('main.dashboard'))