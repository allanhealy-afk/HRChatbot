import sqlite3

def create_sample_database(db_path="database.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create Customers Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        country TEXT NOT NULL
    )
    ''')
    
    # Create Orders Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        product TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    ''')
    
    # Create Products Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    )
    ''')

    # Create Employees Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        job_title TEXT NOT NULL,
        salary REAL NOT NULL,
        address TEXT NOT NULL
    )
    ''')

    # Insert Sample Data
    cursor.executemany("""
    INSERT INTO customers (name, email, country) VALUES (?, ?, ?)
    """, [
        ("Alice Johnson", "alice@example.com", "USA"),
        ("Bob Smith", "bob@example.com", "UK"),
        ("Charlie Lee", "charlie@example.com", "Canada")
    ])

    cursor.executemany("""
    INSERT INTO products (name, category, price) VALUES (?, ?, ?)
    """, [
        ("Laptop", "Electronics", 1200.99),
        ("Headphones", "Electronics", 199.99),
        ("Coffee Machine", "Home Appliances", 89.99)
    ])

    # Insert Sample Employee Data
    cursor.executemany("""
    INSERT INTO employees (name, job_title, salary, address) VALUES (?, ?, ?, ?)
    """, [
        ("Diana Prince", "HR Manager", 85000, "123 Themyscira Ave, Washington DC"),
        ("Clark Kent", "Software Engineer", 95000, "344 Clinton St, Metropolis"),
        ("Bruce Wayne", "CTO", 150000, "1007 Mountain Drive, Gotham")
    ])

    cursor.executemany("""
    INSERT INTO orders (customer_id, product, quantity, price) VALUES (?, ?, ?, ?)
    """, [
        (1, "Laptop", 1, 1200.99),
        (2, "Headphones", 2, 399.98),
        (3, "Coffee Machine", 1, 89.99)
    ])

    conn.commit()
    conn.close()
    print(f"Database '{db_path}' created successfully!")

if __name__ == "__main__":
    create_sample_database()