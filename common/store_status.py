from datetime import datetime, time, timedelta
from database.db_connection import get_db_connection


def check_store_status():
    """
    Checks if the store is currently open based on MySQL 'store_hours' table
    and the current system day and time.

    Returns:
        tuple: (is_open: bool, message: str)
    """
    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed. Please check MySQL server."

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)

        now = datetime.now()
        current_day = now.strftime("%A")       # e.g., 'Monday'
        current_time = now.time()               # e.g., 10:24:00

        query = """
            SELECT day_name, open_time, close_time, is_closed_today
            FROM store_hours
            WHERE day_name = %s
        """
        cursor.execute(query, (current_day,))
        record = cursor.fetchone()

        if not record:
            return False, f"No business hours found in database for {current_day}."

        # Check emergency or manual holiday closure
        if record["is_closed_today"]:
            return False, f"The store is marked CLOSED for today ({current_day})."

        # Convert timedelta to time object if MySQL returns a timedelta
        open_time = record["open_time"]
        close_time = record["close_time"]

        if isinstance(open_time, timedelta):
            total_sec = int(open_time.total_seconds())
            open_time = time(total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60)

        if isinstance(close_time, timedelta):
            total_sec = int(close_time.total_seconds())
            close_time = time(total_sec // 3600, (total_sec % 3600) // 60, total_sec % 60)

        # Compare current time with operating hours
        if open_time <= current_time <= close_time:
            return True, f"Store is OPEN. Operating hours today ({current_day}): {open_time.strftime('%I:%M %p')} - {close_time.strftime('%I:%M %p')}."
        else:
            return False, f"Store is CLOSED right now. Today's hours ({current_day}): {open_time.strftime('%I:%M %p')} to {close_time.strftime('%I:%M %p')}."

    except Exception as e:
        return False, f"Error checking business hours: {e}"

    finally:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if conn and conn.is_connected():
            conn.close()


if __name__ == "__main__":
    is_open, msg = check_store_status()
    print("Is Store Open?:", is_open)
    print("Status Message:", msg)