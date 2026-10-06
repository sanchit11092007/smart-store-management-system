import hashlib
from database.db_connection import get_db_connection


def hash_password(password: str) -> str:
    """Converts plain text password into a secure SHA-256 hash string."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def register_customer(full_name: str, email: str, phone: str, password: str):
    """
    Registers a new customer in MySQL.
    Returns: (success: bool, message: str)
    """
    if not full_name or not email or not phone or not password:
        return False, "All fields are required!"

    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    conn = get_db_connection()
    if not conn:
        return False, "Database connection failed."

    try:
        cursor = conn.cursor(dictionary=True)

        # Check if email is already taken
        cursor.execute("SELECT customer_id FROM customers WHERE email = %s", (email.lower().strip(),))
        if cursor.fetchone():
            return False, "An account with this email already exists."

        # Insert new customer with hashed password
        pwd_hash = hash_password(password)
        cursor.execute("""
            INSERT INTO customers (full_name, email, phone, password_hash)
            VALUES (%s, %s, %s, %s)
        """, (full_name.strip(), email.lower().strip(), phone.strip(), pwd_hash))

        conn.commit()
        return True, "Account created successfully! You can now log in."

    except Exception as e:
        return False, f"Registration failed: {e}"
    finally:
        cursor.close()
        conn.close()


def login_customer(email: str, password: str):
    """
    Checks email and password against the MySQL database.
    Returns: (success: bool, user_dict_or_None, message: str)
    """
    if not email or not password:
        return False, None, "Please enter both email and password."

    conn = get_db_connection()
    if not conn:
        return False, None, "Database connection failed."

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT customer_id, full_name, email, phone, password_hash 
            FROM customers 
            WHERE email = %s
        """, (email.lower().strip(),))

        user = cursor.fetchone()

        if not user:
            return False, None, "No account found with this email."

        # Compare password hash
        if user["password_hash"] != hash_password(password):
            return False, None, "Incorrect password. Please try again."

        # Return user details without the password hash
        del user["password_hash"]
        return True, user, f"Welcome back, {user['full_name']}!"

    except Exception as e:
        return False, None, f"Login failed: {e}"
    finally:
        cursor.close()
        conn.close()