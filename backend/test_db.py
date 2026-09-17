from database import test_database_connection

if __name__ == "__main__":
    if test_database_connection():
        print("Database connection successful")
    else:
        print("Database connection failed")