# BudgetMate

A personal finance management application that helps you track your income and expenses, with monthly analysis and visualization.

## Features

- User authentication (signup/login)
- Track daily and monthly income and expenses
- Categorize transactions
- Visualize spending patterns with charts
- Monthly financial analysis
- Responsive design

## Setup Instructions

1. Clone the repository:
```bash
git clone https://github.com/yourusername/BudgetMate.git
cd BudgetMate
```

2. Create a virtual environment (recommended):
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Initialize the database:
```bash
python init_db.py
```

5. Run the application:
```bash
python run.py
```

6. Open your web browser and go to:
```
http://localhost:5000
```

## First Time Setup

When you first run the application:
1. The database will be automatically created in the `instance` folder
2. You'll need to create a new account using the signup page
3. After signing up, you can log in and start tracking your finances

## Project Structure

```
BudgetMate/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── templates/
│       ├── base.html
│       ├── dashboard.html
│       ├── login.html
│       └── signup.html
├── instance/          # Created automatically (gitignored)
├── requirements.txt
├── init_db.py
└── run.py
```

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is licensed under the MIT License - see the LICENSE file for details.