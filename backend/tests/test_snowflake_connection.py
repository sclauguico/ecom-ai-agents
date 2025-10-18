import os
import snowflake.connector
import pandas as pd
from dotenv import load_dotenv

load_dotenv(override=True) 

def test_connection():
    conn = snowflake.connector.connect(
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_RAW_SCHEMA'),
        role=os.getenv('SNOWFLAKE_ROLE'),
        insecure_mode=True,
    )
    
    cursor = conn.cursor()
    
    # Test basic connection
    cursor.execute("SELECT CURRENT_VERSION()")
    print(f"Snowflake version: {cursor.fetchone()[0]}")
    
    # Check available tables
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print(f"Found {len(tables)} tables:")
    for table in tables[:5]:
        print(f"  - {table[1]}")
    
    # Test sample data from orders
    cursor.execute("SELECT COUNT(*) FROM ORDERS")
    order_count = cursor.fetchone()[0]
    print(f"Total orders: {order_count}")
    
    cursor.execute("SELECT * FROM ORDERS LIMIT 3")
    sample_orders = cursor.fetchall()
    print("\nSample orders:")
    for order in sample_orders:
        print(f"  Order ID: {order[0]}, Total: ${order[4]}")
    
    cursor.close()
    conn.close()
    print("Connection test successful!")

if __name__ == "__main__":
    test_connection()