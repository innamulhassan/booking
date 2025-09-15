import mysql.connector
from mysql.connector import Error
import sys
import os
from dotenv import load_dotenv

class MySQLConnectionTester:
    """Test MySQL database connection and basic operations."""
    
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
        
        # Get database configuration from environment variables
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 3306)),
            'database': os.getenv('DB_NAME', 'booking'),
            'user': os.getenv('DB_USER', 'root'),
            'password': os.getenv('DB_PASSWORD', ''),
            'charset': 'utf8mb4',
            'use_unicode': True,
            'autocommit': True
        }
        self.connection = None
        
        # Print loaded configuration for verification (without password)
        print("📋 Database Configuration Loaded from .env:")
        print(f"   Host: {self.config['host']}")
        print(f"   Port: {self.config['port']}")
        print(f"   Database: {self.config['database']}")
        print(f"   User: {self.config['user']}")
        print(f"   Password: {'*' * len(self.config['password']) if self.config['password'] else 'Not Set'}")
        print()
    
    def test_connection(self):
        """Test basic database connection."""
        print("🔍 Testing MySQL Connection...")
        print("-" * 50)
        
        try:
            # Test connection
            self.connection = mysql.connector.connect(**self.config)
            
            if self.connection.is_connected():
                print("✅ Database connection successful!")
                return True
            else:
                print("❌ Database connection failed!")
                return False
                
        except Error as e:
            print(f"❌ Connection error: {e}")
            self._suggest_solutions(e)
            return False
    
    def test_basic_query(self):
        """Test basic SQL query execution."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection for query test")
            return False
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1 as test_value, NOW() as `current_time`")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Basic query test passed (Result: {result[0]}, Time: {result[1]})")
                cursor.close()
                return True
            else:
                print("❌ Basic query test failed - no result")
                return False
                
        except Error as e:
            print(f"❌ Query execution error: {e}")
            return False
    
    def display_connection_info(self):
        """Display database and connection information."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection for info display")
            return
        
        try:
            cursor = self.connection.cursor()
            
            print("\n📊 Connection Information:")
            print("-" * 30)
            
            # Server version
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()[0]
            print(f"MySQL Version: {version}")
            
            # Current database
            cursor.execute("SELECT DATABASE()")
            database = cursor.fetchone()[0]
            print(f"Current Database: {database}")
            
            # Connection ID
            cursor.execute("SELECT CONNECTION_ID()")
            conn_id = cursor.fetchone()[0]
            print(f"Connection ID: {conn_id}")
            
            # Current user
            cursor.execute("SELECT USER()")
            user = cursor.fetchone()[0]
            print(f"Connected as: {user}")
            
            # Check if database exists and show tables
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            if tables:
                print(f"Tables in '{database}' database:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print(f"No tables found in '{database}' database")
            
            cursor.close()
            
        except Error as e:
            print(f"❌ Error getting connection info: {e}")
    
    def test_database_operations(self):
        """Test basic database operations (CREATE, INSERT, SELECT, DROP)."""
        if not self.connection or not self.connection.is_connected():
            print("❌ No active connection for operations test")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            print("\n🔧 Testing Database Operations:")
            print("-" * 35)
            
            # Create test table
            create_table_query = """
            CREATE TABLE IF NOT EXISTS test_connection_table (
                id INT AUTO_INCREMENT PRIMARY KEY,
                test_message VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            cursor.execute(create_table_query)
            print("✅ Test table created/verified")
            
            # Insert test data
            insert_query = "INSERT INTO test_connection_table (test_message) VALUES (%s)"
            test_message = "Connection test successful"
            cursor.execute(insert_query, (test_message,))
            print("✅ Test data inserted")
            
            # Select test data
            cursor.execute("SELECT * FROM test_connection_table ORDER BY id DESC LIMIT 1")
            result = cursor.fetchone()
            
            if result:
                print(f"✅ Test data retrieved: ID={result[0]}, Message='{result[1]}', Time={result[2]}")
            
            # Clean up - drop test table
            cursor.execute("DROP TABLE IF EXISTS test_connection_table")
            print("✅ Test table cleaned up")
            
            cursor.close()
            return True
            
        except Error as e:
            print(f"❌ Database operations error: {e}")
            return False
    
    def _suggest_solutions(self, error):
        """Suggest solutions based on error type."""
        error_msg = str(error).lower()
        
        print("\n💡 Troubleshooting Suggestions:")
        print("-" * 32)
        
        if "access denied" in error_msg:
            print("• Check username and password")
            print("• Verify user has proper privileges")
            print("• Ensure user can connect from localhost")
            
        elif "unknown database" in error_msg:
            print("• Create the 'booking' database if it doesn't exist")
            print("• Check database name spelling")
            print("• Run: CREATE DATABASE booking;")
            
        elif "can't connect" in error_msg or "connection refused" in error_msg:
            print("• Check if MySQL server is running")
            print("• Verify host and port (localhost:3306)")
            print("• Check firewall settings")
            print("• On Windows, check MySQL service in Services")
            
        elif "no such file" in error_msg or "socket" in error_msg:
            print("• MySQL server may not be installed")
            print("• Check MySQL installation")
            print("• Verify MySQL service is running")
            
        print("• Try manual connection: mysql -u root -p -h localhost -P 3306")
    
    def close_connection(self):
        """Close database connection."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✅ Database connection closed")
    
    def run_all_tests(self):
        """Run all connection tests."""
        print("🚀 MySQL Connection Test Suite")
        print("=" * 50)
        
        success_count = 0
        total_tests = 3
        
        # Test 1: Basic connection
        if self.test_connection():
            success_count += 1
            
            # Test 2: Basic query
            if self.test_basic_query():
                success_count += 1
            
            # Test 3: Database operations
            if self.test_database_operations():
                success_count += 1
            
            # Display connection info
            self.display_connection_info()
        
        # Summary
        print(f"\n📋 Test Summary:")
        print("-" * 15)
        print(f"Passed: {success_count}/{total_tests}")
        
        if success_count == total_tests:
            print("🎉 All tests passed! MySQL connection is working perfectly.")
        elif success_count > 0:
            print("⚠️  Some tests passed. Check the failures above.")
        else:
            print("❌ All tests failed. Please check your MySQL configuration.")
        
        self.close_connection()
        return success_count == total_tests


def main():
    """Main function to run the tests."""
    # Check if mysql-connector-python is installed
    try:
        import mysql.connector
    except ImportError:
        print("❌ mysql-connector-python not found!")
        print("Install it with: pip install mysql-connector-python")
        sys.exit(1)
    
    # Run tests
    tester = MySQLConnectionTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()