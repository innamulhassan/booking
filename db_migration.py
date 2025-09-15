#!/usr/bin/env python3
"""
Database Migration Script for Therapy Booking System
Handles schema updates and data migrations
"""

import os
import sys
import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_environment():
    """Load environment variables from .env file"""
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    env_vars = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip().strip('"').strip("'")
        logger.info(f"Loaded environment from: {env_file}")
    else:
        logger.warning(f"Environment file not found: {env_file}")
    
    return env_vars

def get_database_config():
    """Get database configuration from environment"""
    env_vars = load_environment()
    
    config = {
        'host': env_vars.get('DB_HOST', 'localhost'),
        'port': int(env_vars.get('DB_PORT', '3306')),
        'user': env_vars.get('DB_USER', 'root'),
        'password': env_vars.get('DB_PASSWORD', ''),
        'database': env_vars.get('DB_NAME', 'booking')
    }
    
    return config

def check_migration_table(connection):
    """Check if migration tracking table exists and create if needed"""
    cursor = connection.cursor()
    
    try:
        # Check if migrations table exists
        cursor.execute("SHOW TABLES LIKE 'schema_migrations'")
        result = cursor.fetchone()
        
        if not result:
            logger.info("Creating schema_migrations table...")
            cursor.execute("""
                CREATE TABLE schema_migrations (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    version VARCHAR(255) NOT NULL UNIQUE,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT
                )
            """)
            connection.commit()
            logger.info("Schema migrations table created")
        
        return True
    except Error as e:
        logger.error(f"Error checking migration table: {e}")
        return False
    finally:
        cursor.close()

def is_migration_applied(connection, version):
    """Check if a migration has already been applied"""
    cursor = connection.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM schema_migrations WHERE version = %s", (version,))
        count = cursor.fetchone()[0]
        return count > 0
    except Error as e:
        logger.error(f"Error checking migration status: {e}")
        return False
    finally:
        cursor.close()

def apply_migration(connection, version, description, sql_commands):
    """Apply a migration and record it"""
    cursor = connection.cursor()
    
    try:
        logger.info(f"Applying migration {version}: {description}")
        
        # Execute migration commands
        for command in sql_commands:
            if command.strip():
                cursor.execute(command)
        
        # Record migration
        cursor.execute("""
            INSERT INTO schema_migrations (version, description) 
            VALUES (%s, %s)
        """, (version, description))
        
        connection.commit()
        logger.info(f"Migration {version} applied successfully")
        return True
        
    except Error as e:
        logger.error(f"Error applying migration {version}: {e}")
        connection.rollback()
        return False
    finally:
        cursor.close()

def migration_001_initial_indexes(connection):
    """Migration 001: Add performance indexes"""
    version = "001_initial_indexes"
    description = "Add performance indexes for common queries"
    
    if is_migration_applied(connection, version):
        logger.info(f"Migration {version} already applied, skipping")
        return True
    
    sql_commands = [
        "CREATE INDEX idx_users_phone ON users(phone_number)",
        "CREATE INDEX idx_users_role ON users(role)",
        "CREATE INDEX idx_conversations_user_type ON conversations(user_id, conversation_type)",
        "CREATE INDEX idx_messages_conversation ON messages(conversation_id)",
        "CREATE INDEX idx_messages_timestamp ON messages(timestamp)",
        "CREATE INDEX idx_appointments_client ON appointments(client_id)",
        "CREATE INDEX idx_appointments_therapist ON appointments(therapist_id)",
        "CREATE INDEX idx_appointments_datetime ON appointments(preferred_datetime)",
        "CREATE INDEX idx_appointments_status ON appointments(status)"
    ]
    
    return apply_migration(connection, version, description, sql_commands)

def migration_002_add_session_columns(connection):
    """Migration 002: Add session management columns"""
    version = "002_add_session_columns"
    description = "Add session management and tracking columns"
    
    if is_migration_applied(connection, version):
        logger.info(f"Migration {version} already applied, skipping")
        return True
    
    # Check if columns already exist
    cursor = connection.cursor()
    cursor.execute("DESCRIBE conversations")
    columns = [row[0] for row in cursor.fetchall()]
    cursor.close()
    
    sql_commands = []
    
    if 'last_activity' not in columns:
        sql_commands.append("ALTER TABLE conversations ADD COLUMN last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
    
    if 'session_data' not in columns:
        sql_commands.append("ALTER TABLE conversations ADD COLUMN session_data JSON")
    
    if sql_commands:
        return apply_migration(connection, version, description, sql_commands)
    else:
        # Mark as applied if no changes needed
        cursor = connection.cursor()
        try:
            cursor.execute("INSERT INTO schema_migrations (version, description) VALUES (%s, %s)", 
                         (version, description))
            connection.commit()
            logger.info(f"Migration {version} marked as applied (no changes needed)")
            return True
        except Error as e:
            logger.error(f"Error marking migration as applied: {e}")
            return False
        finally:
            cursor.close()

def migration_003_optimize_tables(connection):
    """Migration 003: Optimize table performance"""
    version = "003_optimize_tables"
    description = "Optimize tables for better performance"
    
    if is_migration_applied(connection, version):
        logger.info(f"Migration {version} already applied, skipping")
        return True
    
    sql_commands = [
        "OPTIMIZE TABLE users",
        "OPTIMIZE TABLE conversations", 
        "OPTIMIZE TABLE messages",
        "OPTIMIZE TABLE appointments",
        "OPTIMIZE TABLE therapist_availability"
    ]
    
    return apply_migration(connection, version, description, sql_commands)

def run_migrations():
    """Run all pending migrations"""
    logger.info("="*60)
    logger.info("THERAPY BOOKING SYSTEM - DATABASE MIGRATIONS")
    logger.info("="*60)
    
    config = get_database_config()
    
    try:
        connection = mysql.connector.connect(**config)
        logger.info(f"Connected to database: {config['database']}")
        
        # Ensure migration table exists
        if not check_migration_table(connection):
            logger.error("Failed to create migration table")
            return False
        
        # Run migrations in order
        migrations = [
            migration_001_initial_indexes,
            migration_002_add_session_columns,
            migration_003_optimize_tables
        ]
        
        success_count = 0
        for migration_func in migrations:
            if migration_func(connection):
                success_count += 1
            else:
                logger.error(f"Migration failed: {migration_func.__name__}")
                break
        
        connection.close()
        
        if success_count == len(migrations):
            logger.info("="*60)
            logger.info("✅ ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
            logger.info(f"Applied {success_count} migrations")
            logger.info("="*60)
            return True
        else:
            logger.error("❌ SOME MIGRATIONS FAILED")
            return False
        
    except Error as e:
        logger.error(f"Database connection error: {e}")
        return False

if __name__ == "__main__":
    try:
        success = run_migrations()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Migration process cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        sys.exit(1)