import os
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    'host': os.environ.get('SNAPKART_DB_HOST', 'localhost'),
    'user': os.environ.get('SNAPKART_DB_USER', 'root'),
    'password': os.environ.get('SNAPKART_DB_PASSWORD', 'Sanc@2007'),
    'database': os.environ.get('SNAPKART_DB_NAME', 'smart_store_db'),
    'autocommit': False,
    'connection_timeout': 10,
}


def get_db_connection():
    """
    Returns a new MySQL connection using config from environment or defaults.
    Callers must close the connection when done.
    Returns None if connection fails.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
    return None


def ensure_core_schema():
    """
    Ensures all required columns exist on the sales table.
    Safe to call multiple times; uses IF NOT EXISTS / information_schema checks.
    """
    conn = get_db_connection()
    if not conn:
        return

    try:
        cursor = conn.cursor(dictionary=True)

        # Ensure payment_method column exists on sales
        cursor.execute("""
            SELECT COUNT(*) AS col_exists
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'sales'
              AND COLUMN_NAME = 'payment_method';
        """, (DB_CONFIG['database'],))
        if cursor.fetchone()["col_exists"] == 0:
            cursor.execute("ALTER TABLE sales ADD COLUMN payment_method VARCHAR(20) DEFAULT 'Cash';")

        # Ensure customer_id column exists on sales
        cursor.execute("""
            SELECT COUNT(*) AS col_exists
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = %s
              AND TABLE_NAME = 'sales'
              AND COLUMN_NAME = 'customer_id';
        """, (DB_CONFIG['database'],))
        if cursor.fetchone()["col_exists"] == 0:
            cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INT NULL;")

        # Ensure customers table exists
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            customer_id INT AUTO_INCREMENT PRIMARY KEY,
            full_name VARCHAR(120) NOT NULL,
            email VARCHAR(120) NOT NULL UNIQUE,
            phone VARCHAR(20) NOT NULL,
            password_hash VARCHAR(64) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Ensure FK constraint (ignore if it already exists)
        try:
            cursor.execute("""
                SELECT COUNT(*) AS fk_exists
                FROM information_schema.TABLE_CONSTRAINTS
                WHERE TABLE_SCHEMA = %s
                  AND TABLE_NAME = 'sales'
                  AND CONSTRAINT_NAME = 'fk_sales_customer';
            """, (DB_CONFIG['database'],))
            if cursor.fetchone()["fk_exists"] == 0:
                cursor.execute("""
                    ALTER TABLE sales
                    ADD CONSTRAINT fk_sales_customer
                    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                    ON DELETE SET NULL;
                """)
        except Exception:
            pass  # FK might already exist under different name

        conn.commit()
        cursor.close()
    except Exception as e:
        print(f"Schema migration notice: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()