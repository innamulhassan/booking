#!/usr/bin/env python3
"""
Database Conversion and Setup Script
Handles database initialization, migration, and cleanup for Therapy Booking System
"""

import os
import sys
import logging
import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Add the therapy_booking_app to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'therapy_booking_app'))

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
    
    logger.info(f"Database config - Host: {config['host']}, Port: {config['port']}, Database: {config['database']}")
    return config

def create_database_if_not_exists(config):
    """Create database if it doesn't exist"""
    try:
        # Connect without specifying database
        connection_config = config.copy()
        database_name = connection_config.pop('database')
        
        connection = mysql.connector.connect(**connection_config)
        cursor = connection.cursor()
        
        # Check if database exists
        cursor.execute(f"SHOW DATABASES LIKE '{database_name}'")
        result = cursor.fetchone()
        
        if not result:
            logger.info(f"Creating database: {database_name}")
            cursor.execute(f"CREATE DATABASE `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"Database '{database_name}' created successfully")
        else:
            logger.info(f"Database '{database_name}' already exists")
        
        cursor.close()
        connection.close()
        return True
        
    except Error as e:
        logger.error(f"Error creating database: {e}")
        return False

def clear_database_tables(config):
    """Clear all data from database tables but keep structure"""
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        logger.info("Clearing database tables...")
        
        # Disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        # Get all tables
        cursor.execute(f"SHOW TABLES FROM `{config['database']}`")
        tables = cursor.fetchall()
        
        # Clear each table
        for (table_name,) in tables:
            logger.info(f"Clearing table: {table_name}")
            cursor.execute(f"TRUNCATE TABLE `{table_name}`")
        
        # Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info(f"Successfully cleared {len(tables)} tables")
        return True
        
    except Error as e:
        logger.error(f"Error clearing database tables: {e}")
        return False

def initialize_database_tables():
    """Initialize database tables using the application models"""
    try:
        # Import the database initialization function from the app
        from app.models.database import create_tables, engine
        from sqlalchemy import text
        
        logger.info("Initializing database tables using application models...")
        
        # Initialize the database
        create_tables()
        
        # Test connection
        with engine.connect() as connection:
            result = connection.execute(text("SELECT DATABASE()"))
            current_db = result.fetchone()[0]
            logger.info(f"Connected to database: {current_db}")
        
        logger.info("Database tables initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")
        return False

def insert_default_data(config):
    """Insert default data for system operation"""
    try:
        connection = mysql.connector.connect(**config)
        cursor = connection.cursor()
        
        logger.info("Inserting default data...")
        
        # Check if therapist user exists
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'THERAPIST'")
        therapist_count = cursor.fetchone()[0]
        
        if therapist_count == 0:
            # Insert default therapist
            logger.info("Creating default therapist user...")
            cursor.execute("""
                INSERT INTO users (phone_number, name, role, is_active) 
                VALUES ('+97471669569', 'Dr. Smith', 'THERAPIST', TRUE)
            """)
            logger.info("Default therapist user created")
        else:
            logger.info("Therapist user already exists")
        
        # Insert default therapist availability (sample schedule)
        cursor.execute("SELECT COUNT(*) FROM therapist_availability")
        availability_count = cursor.fetchone()[0]
        
        if availability_count == 0:
            logger.info("Creating default therapist availability...")
            
            # Sample availability - Monday to Friday 9 AM to 6 PM
            # day_of_week: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
            availability_data = [
                (1, '09:00', '18:00', True),    # Monday
                (2, '09:00', '18:00', True),    # Tuesday
                (3, '09:00', '18:00', True),    # Wednesday
                (4, '09:00', '18:00', True),    # Thursday
                (5, '09:00', '18:00', True),    # Friday
                (6, '09:00', '14:00', True),    # Saturday
                (0, '00:00', '00:00', False)    # Sunday - Closed
            ]
            
            for day, start_time, end_time, is_available in availability_data:
                cursor.execute("""
                    INSERT INTO therapist_availability (therapist_id, day_of_week, start_time, end_time, is_available) 
                    VALUES (1, %s, %s, %s, %s)
                """, (day, start_time, end_time, is_available))
            
            logger.info("Default therapist availability created")
        else:
            logger.info("Therapist availability already exists")
        
        connection.commit()
        cursor.close()
        connection.close()
        
        logger.info("Default data insertion completed")
        return True
        
    except Error as e:
        logger.error(f"Error inserting default data: {e}")
        return False

def run_database_conversion():
    """Main database conversion process"""
    logger.info("="*60)
    logger.info("THERAPY BOOKING SYSTEM - DATABASE CONVERSION")
    logger.info("="*60)
    
    # Get database configuration
    config = get_database_config()
    
    # Step 1: Create database if needed
    logger.info("Step 1: Database Creation")
    if not create_database_if_not_exists(config):
        logger.error("Failed to create database. Exiting.")
        return False
    
    # Step 2: Clear existing data
    logger.info("Step 2: Clearing Existing Data")
    if not clear_database_tables(config):
        logger.warning("Could not clear existing tables (may not exist yet)")
    
    # Step 3: Initialize tables
    logger.info("Step 3: Table Initialization")
    if not initialize_database_tables():
        logger.error("Failed to initialize database tables. Exiting.")
        return False
    
    # Step 4: Insert default data
    logger.info("Step 4: Default Data Insertion")
    if not insert_default_data(config):
        logger.error("Failed to insert default data. Exiting.")
        return False
    
    logger.info("="*60)
    logger.info("✅ DATABASE CONVERSION COMPLETED SUCCESSFULLY!")
    logger.info("="*60)
    logger.info("Database is ready for Therapy Booking System operation.")
    logger.info(f"Database: {config['database']} on {config['host']}:{config['port']}")
    logger.info("You can now start the system with START-ALL.bat")
    logger.info("="*60)
    
    return True

if __name__ == "__main__":
    try:
        success = run_database_conversion()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Database conversion cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during database conversion: {e}")
        sys.exit(1)