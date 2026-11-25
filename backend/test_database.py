
from database import get_connection

connection = get_connection()

try:
    cursor = connection.cursor()

    cursor.execute("PRAGMA table_info(reports)")
    columns = cursor.fetchall()

    print("Reports table columns:")

    for column in columns:
        print(f"{column['name']} - {column['type']}")

finally:
    connection.close()
