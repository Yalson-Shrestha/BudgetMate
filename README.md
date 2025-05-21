# BudgetMate

BudgetMate is a Flask-based web application for tracking monthly income and expenses, helping users manage their finances effectively.

## Features

- User authentication (signup/login)
- Track monthly income and expenses
- Categorize transactions
- View financial analytics and insights
- Responsive and user-friendly interface

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

## Installation

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

3. Install dependencies:
```bash
pip install -r requirements.txt
```


## Running the Application

1. Make sure your virtual environment is activated
2. Run the application:
```bash
python run.py
```
3. Open your web browser and navigate to `http://localhost:5000`

## Project Structure

```
BudgetMate/
├── app/
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   ├── static/
│   └── templates/
├── instance/
│   └── finance.db
├── .env
├── .gitignore
├── README.md
├── requirements.txt
└── run.py
```

## Database

The application uses SQLite as its database, which is automatically created in the `instance` folder when you first run the application. No additional database setup is required.

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to your branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any issues or have questions, please open an issue in the GitHub repository.