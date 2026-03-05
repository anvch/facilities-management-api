import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv(override=True)

# .env file overrides system environment variables
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("HOST"),
        port=3306,
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD"),
        database=os.getenv("DATABASE"),
    )