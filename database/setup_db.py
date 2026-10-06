import os
import mysql.connector
from mysql.connector import Error

ROOT_CONFIG = {
    'host': os.environ.get('SNAPKART_DB_HOST', 'localhost'),
    'user': os.environ.get('SNAPKART_DB_USER', 'root'),
    'password': os.environ.get('SNAPKART_DB_PASSWORD', os.environ.get('SNAPKART_DB_PASSW', 'Sanc@2007'))
}


def create_database_and_tables():
    cursor = None
    conn = None
    try:
        conn = mysql.connector.connect(**ROOT_CONFIG)
        cursor = conn.cursor()

        # Create Database
        cursor.execute("CREATE DATABASE IF NOT EXISTS smart_store_db;")
        cursor.execute("USE smart_store_db;")
        print("Database 'smart_store_db' created/selected successfully.")

        # Create store_hours Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS store_hours (
            day_name VARCHAR(10) PRIMARY KEY,
            open_time TIME NOT NULL,
            close_time TIME NOT NULL,
            is_closed_today BOOLEAN DEFAULT FALSE
        );
        """)

        # Default operating hours: 09:00 AM to 09:00 PM
        default_hours = [
            ('Monday', '09:00:00', '21:00:00', False),
            ('Tuesday', '09:00:00', '21:00:00', False),
            ('Wednesday', '09:00:00', '21:00:00', False),
            ('Thursday', '09:00:00', '21:00:00', False),
            ('Friday', '09:00:00', '21:00:00', False),
            ('Saturday', '09:00:00', '21:00:00', False),
            ('Sunday', '10:00:00', '18:00:00', False)
        ]
        cursor.executemany("""
            INSERT INTO store_hours (day_name, open_time, close_time, is_closed_today)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE day_name=day_name;
        """, default_hours)

        # Create inventory Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            item_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            category VARCHAR(80) NOT NULL,
            price DECIMAL(10, 2) NOT NULL,
            stock_quantity INT NOT NULL
        );
        """)

        # Create customers Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            phone VARCHAR(20),
            password_hash VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Create sales Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            sale_id INT AUTO_INCREMENT PRIMARY KEY,
            sale_datetime DATETIME NOT NULL,
            total_amount DECIMAL(10, 2) NOT NULL,
            payment_method VARCHAR(50) DEFAULT 'UPI',
            customer_id INT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
        );
        """)

        # Create sale_items Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sale_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sale_id INT NOT NULL,
            item_id INT NOT NULL,
            quantity INT NOT NULL,
            unit_price DECIMAL(10, 2) NOT NULL,
            subtotal DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
            FOREIGN KEY (item_id) REFERENCES inventory(item_id) ON DELETE CASCADE
        );
        """)

        conn.commit()
        print("All tables created successfully!")

    except Error as e:
        print(f"Error during setup: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    create_database_and_tables()