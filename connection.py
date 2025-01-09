import mysql.connector

def test_db_connection():
    connection = mysql.connector.connect(
        host="flappybird.cvy8sgyqqqqr.us-east-2.rds.amazonaws.com",
        user="admin",  # Replace with your username
        password="your_password"  # Replace with your password
    )
    cursor = connection.cursor()
    cursor.execute("SHOW DATABASES;")
    for db in cursor:
        print(db)
    connection.close()

if __name__ == "__main__":
    test_db_connection()
