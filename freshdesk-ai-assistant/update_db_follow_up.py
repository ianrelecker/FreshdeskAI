#!/usr/bin/env python3
import os
import sys
import sqlite3
import logging

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def update_database():
    """Update the database schema to add the follow_up_questions column to the responses table."""
    # Get the database path
    db_path = os.path.join(os.path.dirname(__file__), 'tickets.db')
    
    # Check if the database exists
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    try:
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(responses)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'follow_up_questions' not in column_names:
            # Add the new column
            logger.info("Adding follow_up_questions column to responses table")
            cursor.execute("ALTER TABLE responses ADD COLUMN follow_up_questions TEXT")
            conn.commit()
            logger.info("Database schema updated successfully")
        else:
            logger.info("follow_up_questions column already exists in responses table")
        
        # Close the connection
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error updating database schema: {str(e)}")
        return False

if __name__ == "__main__":
    if update_database():
        print("Database schema updated successfully.")
    else:
        print("Failed to update database schema. Check the logs for details.")
