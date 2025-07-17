from app import create_app, db
from app.models import db, User, Transaction, Category

if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
        print('Database tables created.')
