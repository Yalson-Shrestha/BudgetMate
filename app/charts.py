from app.models import Expense, Category
from app import db

def category_expense_summary():
    results = db.session.query(Category.name, db.func.sum(Expense.amount))\
        .join(Expense).group_by(Category.name).all()
    return {name: float(amount) for name, amount in results}
