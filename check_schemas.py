"""Check database table schemas to understand what needs to be fixed"""
import pymysql
import os

def check_table_schemas():
    # Database connection
    connection = pymysql.connect(
        host='gulf-1.mysqlsvc.ns0.name',
        user='QATARTH_therapyuser',
        password='*RHDhndF-OLdnbBr', 
        database='QATARTH_therapy_booking',
        charset='utf8mb4'
    )
    
    try:
        cursor = connection.cursor()
        
        # List all tables
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print("Available tables:")
        for table in tables:
            print(f"  {table[0]}")
        
        print("\n" + "="*50 + "\n")
        
        # Check specific table structures
        for table_name in ['appointments', 'therapists', 'users', 'therapist_services']:
            try:
                print(f"Schema for {table_name}:")
                cursor.execute(f"DESC {table_name}")
                columns = cursor.fetchall()
                for column in columns:
                    print(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]}")
                print()
            except Exception as e:
                print(f"Error checking {table_name}: {e}")
                print()
                
    finally:
        connection.close()

if __name__ == "__main__":
    check_table_schemas()