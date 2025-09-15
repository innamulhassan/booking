#!/usr/bin/env python3
"""
MySQL Administration Helper Script
Helps connect to MySQL and perform administrative tasks
"""

import mysql.connector
from mysql.connector import Error
import getpass
import sys

class MySQLAdmin:
    """MySQL administration helper."""
    
    def __init__(self):
        self.connection = None
        self.config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True
        }
    
    def connect_with_password(self, password=None, database=None):
        """Connect to MySQL with password."""
        if password is None:
            password = getpass.getpass("Enter MySQL root password: ")
        
        self.config['password'] = password
        if database:
            self.config['database'] = database
        
        try:
            print(f"🔌 Connecting to MySQL server at {self.config['host']}:{self.config['port']}...")
            self.connection = mysql.connector.connect(**self.config)
            
            if self.connection.is_connected():
                print("✅ Successfully connected to MySQL!")
                return True
            else:
                print("❌ Failed to connect to MySQL!")
                return False
                
        except Error as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def show_databases(self):
        """Show all databases."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection")
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            
            print("\n📋 Available Databases:")
            print("-" * 25)
            for db in databases:
                print(f"  - {db[0]}")
            
            cursor.close()
            
        except Error as e:
            print(f"❌ Error showing databases: {e}")
    
    def create_database(self, database_name):
        """Create a database."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection")
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}`")
            print(f"✅ Database '{database_name}' created successfully!")
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ Error creating database: {e}")
            return False
    
    def change_root_password(self, new_password):
        """Change root password."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Method 1: ALTER USER (MySQL 5.7+)
            cursor.execute(f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{new_password}'")
            cursor.execute("FLUSH PRIVILEGES")
            
            print("✅ Root password changed successfully!")
            print("⚠️  Please remember your new password!")
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ Error changing password: {e}")
            
            # Method 2: Try older method
            try:
                cursor.execute(f"SET PASSWORD FOR 'root'@'localhost' = PASSWORD('{new_password}')")
                cursor.execute("FLUSH PRIVILEGES")
                print("✅ Root password changed successfully (using legacy method)!")
                cursor.close()
                return True
            except Error as e2:
                print(f"❌ Error with legacy method too: {e2}")
                return False
    
    def show_users(self):
        """Show MySQL users."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection")
            return
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT User, Host FROM mysql.user")
            users = cursor.fetchall()
            
            print("\n👥 MySQL Users:")
            print("-" * 20)
            for user in users:
                print(f"  - {user[0]}@{user[1]}")
            
            cursor.close()
            
        except Error as e:
            print(f"❌ Error showing users: {e}")
    
    def test_database_connection(self, database_name):
        """Test connection to specific database."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection")
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"USE `{database_name}`")
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Successfully connected to database '{database_name}'")
                cursor.close()
                return True
            else:
                print(f"❌ Failed to use database '{database_name}'")
                return False
                
        except Error as e:
            print(f"❌ Error testing database '{database_name}': {e}")
            return False
    
    def get_server_info(self):
        """Get MySQL server information."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection")
            return
        
        try:
            cursor = self.connection.cursor()
            
            print("\n🔍 MySQL Server Information:")
            print("-" * 35)
            
            # Version
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"Version: {version}")
            
            # Current user
            cursor.execute("SELECT USER()")
            user = cursor.fetchone()[0]
            print(f"Connected as: {user}")
            
            # Connection ID
            cursor.execute("SELECT CONNECTION_ID()")
            conn_id = cursor.fetchone()[0]
            print(f"Connection ID: {conn_id}")
            
            # Server uptime
            cursor.execute("SHOW STATUS LIKE 'Uptime'")
            uptime = cursor.fetchone()[1]
            uptime_hours = int(uptime) // 3600
            print(f"Server Uptime: {uptime_hours} hours")
            
            cursor.close()
            
        except Error as e:
            print(f"❌ Error getting server info: {e}")
    
    def close_connection(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Database connection closed")
    
    def interactive_menu(self):
        """Interactive menu for MySQL administration."""
        print("🚀 MySQL Administration Tool")
        print("=" * 40)
        
        # Connect first
        if not self.connect_with_password("Ishak@123"):
            print("❌ Failed to connect. Exiting...")
            return
        
        while True:
            print("\n📋 Available Actions:")
            print("1. Show databases")
            print("2. Create 'stock' database")
            print("3. Test 'stock' database connection")
            print("4. Change root password")
            print("5. Show MySQL users")
            print("6. Show server information")
            print("7. Exit")
            
            try:
                choice = input("\nEnter your choice (1-7): ").strip()
                
                if choice == "1":
                    self.show_databases()
                    
                elif choice == "2":
                    self.create_database("stock")
                    
                elif choice == "3":
                    self.test_database_connection("stock")
                    
                elif choice == "4":
                    new_password = getpass.getpass("Enter new root password: ")
                    confirm_password = getpass.getpass("Confirm new password: ")
                    
                    if new_password == confirm_password:
                        self.change_root_password(new_password)
                    else:
                        print("❌ Passwords don't match!")
                        
                elif choice == "5":
                    self.show_users()
                    
                elif choice == "6":
                    self.get_server_info()
                    
                elif choice == "7":
                    print("👋 Goodbye!")
                    break
                    
                else:
                    print("❌ Invalid choice! Please enter 1-7.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Exiting...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
        
        self.close_connection()


def main():
    """Main function."""
    admin = MySQLAdmin()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test-connection":
            # Just test connection
            if admin.connect_with_password("Ishak@123"):
                admin.get_server_info()
                admin.show_databases()
                admin.close_connection()
            
        elif sys.argv[1] == "--create-stock-db":
            # Create stock database
            if admin.connect_with_password("Ishak@123"):
                admin.create_database("stock")
                admin.close_connection()
    else:
        # Interactive mode
        admin.interactive_menu()


if __name__ == "__main__":
    main()
