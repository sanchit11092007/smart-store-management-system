from database.db_connection import get_db_connection


def create_customer_table():
    conn = get_db_connection()
    if not conn:
        print("Cannot connect to MySQL database.")
        return

    cursor = None
    try:
        cursor = conn.cursor()

        # 1. Create customers table
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
        print("Table 'customers' created or already exists.")

        # 2. Add customer_id column to sales table if not already added
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = 'smart_store_db' 
              AND TABLE_NAME = 'sales' 
              AND COLUMN_NAME = 'customer_id';
        """)
        exists = cursor.fetchone()[0]

        if exists == 0:
            cursor.execute("ALTER TABLE sales ADD COLUMN customer_id INT NULL;")
            cursor.execute("""
                ALTER TABLE sales 
                ADD CONSTRAINT fk_sales_customer 
                FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
                ON DELETE SET NULL;
            """)
            print("Added 'customer_id' column to 'sales' table.")

        conn.commit()
        print("Database update completed successfully!")

    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    create_customer_table()