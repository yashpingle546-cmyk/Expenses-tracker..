import sqlite3
import os
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(__file__), 'expenses.db')


def create_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with create_connection() as conn:
        conn.execute(
            '''CREATE TABLE IF NOT EXISTS expenses (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date TEXT NOT NULL,
                   category TEXT NOT NULL,
                   amount REAL NOT NULL,
                   description TEXT
               )'''
        )


def parse_date(input_text, default_date=None):
    text = input(input_text).strip() or (default_date or '')
    if not text:
        return None
    for fmt in ('%Y-%m-%d', '%d-%m-%Y', '%d/%m/%Y'):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    print('Invalid date format. Use YYYY-MM-DD, DD-MM-YYYY, or DD/MM/YYYY.')
    return parse_date(input_text, default_date)


def format_currency(value):
    return f'₹{value:,.2f}' if value is not None else '₹0.00'


def add_expense():
    print('\n=== Add Expense ===')
    date = parse_date('Enter date [YYYY-MM-DD] (leave blank for today): ', datetime.today().date())
    category = input('Category: ').strip()
    if not category:
        print('Category is required.')
        return
    amount_text = input('Amount: ').strip()
    try:
        amount = float(amount_text)
    except ValueError:
        print('Invalid amount.')
        return
    description = input('Description (optional): ').strip()
    with create_connection() as conn:
        conn.execute(
            'INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)',
            (date.isoformat(), category, amount, description)
        )
    print('Expense recorded successfully.')


def list_expenses(rows):
    if not rows:
        print('No expenses found.')
        return
    print('-' * 80)
    print(f"{'ID':<4} {'Date':<12} {'Category':<15} {'Amount':<12} Description")
    print('-' * 80)
    for row in rows:
        print(f"{row['id']:<4} {row['date']:<12} {row['category']:<15} {format_currency(row['amount']):<12} {row['description']}")
    print('-' * 80)


def view_expenses():
    print('\n=== View All Expenses ===')
    with create_connection() as conn:
        rows = conn.execute('SELECT * FROM expenses ORDER BY date DESC, id DESC').fetchall()
    list_expenses(rows)


def filter_expenses():
    print('\n=== Filter Expenses ===')
    start_date = parse_date('Start date [YYYY-MM-DD]: ')
    end_date = parse_date('End date [YYYY-MM-DD]: ')
    category = input('Category (optional): ').strip()
    query = 'SELECT * FROM expenses WHERE 1=1'
    params = []
    if start_date:
        query += ' AND date >= ?'
        params.append(start_date.isoformat())
    if end_date:
        query += ' AND date <= ?'
        params.append(end_date.isoformat())
    if category:
        query += ' AND category LIKE ?'
        params.append(f'%{category}%')
    query += ' ORDER BY date DESC, id DESC'
    with create_connection() as conn:
        rows = conn.execute(query, params).fetchall()
    list_expenses(rows)


def delete_expense():
    print('\n=== Delete Expense ===')
    expense_id = input('Enter expense ID to delete: ').strip()
    if not expense_id.isdigit():
        print('Enter a valid numeric ID.')
        return
    with create_connection() as conn:
        cursor = conn.execute('SELECT * FROM expenses WHERE id = ?', (expense_id,)).fetchone()
        if not cursor:
            print('No expense found with that ID.')
            return
        conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    print('Expense deleted successfully.')


def generate_report():
    print('\n=== Expense Report ===')
    start_date = parse_date('Start date [YYYY-MM-DD]: ')
    end_date = parse_date('End date [YYYY-MM-DD]: ')
    if not start_date or not end_date:
        print('Both start and end dates are required for report generation.')
        return
    if start_date > end_date:
        print('Start date cannot be after end date.')
        return
    with create_connection() as conn:
        expenses = conn.execute(
            'SELECT * FROM expenses WHERE date BETWEEN ? AND ? ORDER BY date ASC',
            (start_date.isoformat(), end_date.isoformat())
        ).fetchall()
        total = conn.execute(
            'SELECT SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ?',
            (start_date.isoformat(), end_date.isoformat())
        ).fetchone()['total']
        category_totals = conn.execute(
            'SELECT category, SUM(amount) as total FROM expenses WHERE date BETWEEN ? AND ? GROUP BY category ORDER BY total DESC',
            (start_date.isoformat(), end_date.isoformat())
        ).fetchall()
    list_expenses(expenses)
    print('\nReport summary:')
    print(f'Date range: {start_date.isoformat()} to {end_date.isoformat()}')
    print(f'Total spent: {format_currency(total or 0)}')
    print('\nSpending by category:')
    if category_totals:
        for row in category_totals:
            print(f"  {row['category']:<15} {format_currency(row['total'])}")
    else:
        print('  No category totals available.')


def main_menu():
    init_db()
    while True:
        print('\nExpense Tracker')
        print('1. Add expense')
        print('2. View all expenses')
        print('3. Filter expenses')
        print('4. Generate report')
        print('5. Delete expense')
        print('6. Exit')
        choice = input('Choose an option: ').strip()
        if choice == '1':
            add_expense()
        elif choice == '2':
            view_expenses()
        elif choice == '3':
            filter_expenses()
        elif choice == '4':
            generate_report()
        elif choice == '5':
            delete_expense()
        elif choice == '6':
            print('Goodbye!')
            break
        else:
            print('Invalid choice. Please try again.')


if __name__ == '__main__':
    main_menu()
