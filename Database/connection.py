import pymysql

# Database connection details
db_config = {
    'host': 'flappybird.cvy8sgyqqqr.us-east-2.rds.amazonaws.com', 
    'user': 'admin',  
    'password': 'Flappybird',  
    'database': 'Flappy_Base',  
}

# Function to connect to the database
def connect_to_database():
    try:
        connection = pymysql.connect(**db_config)
        print("Connected to the database successfully!")
        return connection
    except Exception as e:
        print(f"Failed to connect to the database: {e}")
        return None

# Example usage
connection = connect_to_database()

if connection:
    # Create a cursor to execute queries
    cursor = connection.cursor()

    # Example: Show tables
    cursor.execute("SHOW TABLES;")
    tables = cursor.fetchall()
    print("Tables in the database:", tables)

    # Close the connection
    connection.close()
