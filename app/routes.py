from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from .models import db, User, Transaction, Category
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date, datetime, timedelta
from sqlalchemy import extract, func
from urllib.parse import quote
from calendar import monthrange
import traceback

main = Blueprint('main', __name__)

# Error handlers
@main.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error=error), 404

@main.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    current_app.logger.error(f'Server Error: {error}')
    current_app.logger.error(traceback.format_exc())
    return render_template('error.html', error=error), 500

@main.errorhandler(Exception)
def unhandled_exception(e):
    db.session.rollback()
    current_app.logger.error(f'Unhandled Exception: {e}')
    current_app.logger.error(traceback.format_exc())
    return render_template('error.html', error=e), 500

@main.route('/')
@login_required
def index():
    # Get selected month from query parameter, default to current month
    selected_month = request.args.get('month', datetime.now().strftime('%Y-%m'))
    try:
        selected_date = datetime.strptime(selected_month, '%Y-%m')
    except ValueError:
        selected_date = datetime.now()
    
    # Get available months for the selector (last 12 months)
    available_months = []
    current_date = datetime.now()
    for i in range(12):
        month_date = current_date - timedelta(days=30*i)
        available_months.append(month_date.replace(day=1))

    # Get the first and last day of the selected month
    first_day = selected_date.replace(day=1)
    last_day = selected_date.replace(day=monthrange(selected_date.year, selected_date.month)[1])

    # Get transactions for the selected month
    monthly_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= first_day,
        Transaction.date <= last_day
    ).order_by(Transaction.date.desc()).all()

    # Get today's transactions
    today = datetime.now().date()
    daily_transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= today,
        Transaction.date < today + timedelta(days=1)
    ).order_by(Transaction.date.desc()).all()

    # Calculate monthly totals
    monthly_income = sum(t.amount for t in monthly_transactions if t.type == 'income')
    monthly_expenses = sum(t.amount for t in monthly_transactions if t.type == 'expense')
    monthly_balance = monthly_income - monthly_expenses

    # Calculate daily totals
    daily_income = sum(t.amount for t in daily_transactions if t.type == 'income')
    daily_expenses = sum(t.amount for t in daily_transactions if t.type == 'expense')

    # Choose template based on device
    template = 'mobile/dashboard.html' if request.headers.get('User-Agent', '').lower() in ['iphone', 'android', 'mobile', 'tablet', 'ipad'] else 'dashboard.html'

    # Fetch categories for the dropdown (default + custom)
    default_categories = [
        '🍔 Food', '🚌 Transport', '🏠 Rent', '🏥 Health', '🛍️ Shopping', '📚 Education'
    ]
    custom_categories = [c.name for c in Category.query.filter_by(user_id=current_user.id).all()]
    all_categories = default_categories + [c for c in custom_categories if c not in default_categories]

    return render_template(template,
                         monthly_transactions=monthly_transactions,
                         daily_transactions=daily_transactions,
                         monthly_income=monthly_income,
                         monthly_expenses=monthly_expenses,
                         monthly_balance=monthly_balance,
                         daily_income=daily_income,
                         daily_expenses=daily_expenses,
                         now=datetime.now(),
                         today=today,
                         selected_month=selected_month,
                         selected_month_name=selected_date.strftime('%B %Y'),
                         available_months=available_months,
                         categories=all_categories)

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
        try:
            user = User.query.filter_by(email=request.form['email']).first()
            if user and check_password_hash(user.password, request.form['password']):
                login_user(user, remember=True)
                return redirect(url_for('main.index'))
            flash('Invalid email or password', 'error')
        except Exception as e:
            current_app.logger.error(f'Login error: {e}')
            current_app.logger.error(traceback.format_exc())
            flash('An error occurred during login. Please try again.', 'error')
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.')
    return redirect(url_for('main.login'))

@main.route('/add', methods=['POST'])
@login_required
def add_transaction():
    try:
        # Validate amount
        amount = request.form.get('amount')
        if not amount or float(amount) <= 0:
            flash('Please enter a valid amount greater than 0', 'error')
            return redirect(url_for('main.index'))

        # Validate category
        category = request.form.get('category')
        if not category:
            flash('Please select a category', 'error')
            return redirect(url_for('main.index'))

        # Validate type
        type = request.form.get('type')
        if type not in ['income', 'expense']:
            flash('Invalid transaction type', 'error')
            return redirect(url_for('main.index'))

        # Save new category if not in default or custom
        default_categories = [
            '🍔 Food', '🚌 Transport', '🏠 Rent', '🏥 Health', '🛍️ Shopping', '📚 Education'
        ]
        existing = Category.query.filter_by(user_id=current_user.id, name=category).first()
        if category not in default_categories and not existing:
            db.session.add(Category(name=category, user_id=current_user.id))
            db.session.commit()

        # Create and save transaction
        transaction = Transaction(
            amount=float(amount),
            category=category,
            type=type,
            note=request.form.get('note', ''),
            user_id=current_user.id,
            date=datetime.now()  # Explicitly set the date
        )
        
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        
    except ValueError:
        flash('Invalid amount format. Please enter a valid number.', 'error')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error adding transaction: {e}')
        current_app.logger.error(traceback.format_exc())
        flash('An error occurred while adding the transaction. Please try again.', 'error')
    
    return redirect(url_for('main.index'))

@main.route('/update_transaction', methods=['POST'])
@login_required
def update_transaction():
    transaction_id = request.form.get('transaction_id')
    amount = request.form.get('amount')
    category = request.form.get('category')
    type_ = request.form.get('type')
    note = request.form.get('note', '')

    if not transaction_id or not amount or not category or not type_:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    try:
        transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()
        if not transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'}), 404
        transaction.amount = float(amount)
        transaction.category = category
        transaction.type = type_
        transaction.note = note
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

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
    income_data = [[row[0], float(row[1])] for row in category_income]

    # Get monthly income and expense totals for the last 12 months
    monthly_totals = []
    for i in range(11, -1, -1):
        month_date = datetime(current_year, current_month, 1) - timedelta(days=30*i)
        year = month_date.year
        month = month_date.month
        # Income
        income = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'income',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar() or 0
        # Expense
        expense = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            extract('month', Transaction.date) == month,
            extract('year', Transaction.date) == year
        ).scalar() or 0
        monthly_totals.append({
            'month': month_date.strftime('%b'),
            'year': year,
            'income': float(income),
            'expense': float(expense)
        })

    # Current month income/expense for progress bar
    current_month_income = sum([row[1] for row in income_data])
    current_month_expense = sum([row[1] for row in expense_data])

    return render_template('chart.html',
        category_expenses=expense_data,
        category_income=income_data,
        current_month=datetime(current_year, current_month, 1).strftime('%B %Y'),
        monthly_totals=monthly_totals,
        current_month_income=current_month_income,
        current_month_expense=current_month_expense
    )

@main.route('/help')
def help():
    try:
        return render_template('help.html')
    except Exception as e:
        current_app.logger.error(f'Error in help route: {e}')
        current_app.logger.error(traceback.format_exc())
        flash('An error occurred while loading the help page. Please try again.', 'error')
        return redirect(url_for('main.index'))

@main.route('/feedback')
@login_required
def feedback():
    return render_template('feedback.html')

@main.route('/delete_transaction', methods=['POST'])
@login_required
def delete_transaction():
    transaction_id = request.form.get('transaction_id')
    
    if not transaction_id:
        return jsonify({'success': False, 'message': 'Transaction ID is required'}), 400
    
    try:
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            user_id=current_user.id
        ).first()
        
        if not transaction:
            return jsonify({'success': False, 'message': 'Transaction not found'}), 404
        
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    try:
        # Delete all transactions for the user
        Transaction.query.filter_by(user_id=current_user.id).delete()
        # Delete the user
        user = User.query.get(current_user.id)
        db.session.delete(user)
        db.session.commit()
        logout_user()
        flash('Your account and all associated data have been deleted.', 'success')
        return redirect(url_for('main.signup'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting account: {e}')
        current_app.logger.error(traceback.format_exc())
        flash('An error occurred while deleting your account. Please try again.', 'error')
        return redirect(url_for('main.index'))

# === TEMPORARY ADMIN ROUTES: REMOVE AFTER USE FOR SECURITY ===
@main.route('/admin/delete_all', methods=['POST'])
def admin_delete_all():
    from .models import db, User, Transaction
    Transaction.query.delete()
    User.query.delete()
    db.session.commit()
    return "All users and transactions deleted!"

@main.route('/admin/list_emails')
def admin_list_emails():
    from .models import User
    emails = [user.email for user in User.query.all()]
    return '<br>'.join(emails)
# === END TEMPORARY ADMIN ROUTES ===
