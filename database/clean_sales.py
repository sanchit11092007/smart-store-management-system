from database.db_connection import get_db_connection


def remove_dummy_sales():
    conn = get_db_connection()
    if not conn:
        print("Database connection failed.")
        return

    try:
        cursor = conn.cursor()
        # Delete dummy sales records
        cursor.execute("DELETE FROM sale_items;")
        cursor.execute("DELETE FROM sales;")
        cursor.execute("ALTER TABLE sales AUTO_INCREMENT = 1;")
        cursor.execute("ALTER TABLE sale_items AUTO_INCREMENT = 1;")
        conn.commit()
        print("Successfully wiped all sample sales! Your database is now clean.")
    except Exception as e:
        print(f"Error during cleanup: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    remove_dummy_sales()