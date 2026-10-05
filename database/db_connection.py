import mysql.connector 
from mysql.connector import Error 

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Sanc@2007',
    'database': 'smart_store_db'
}

def get_db_connection():
    try: 
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection 
    except Error as e: 
        print(f"Error connecting to MySQL: {e}")
        return None 