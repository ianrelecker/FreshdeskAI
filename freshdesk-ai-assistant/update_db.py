#!/usr/bin/env python3
import os
import sys
import sqlite3
import shutil
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def backup_database():
    """Create a backup of the database file."""
    db_path = os.path.join(os.path.dirname(__file__), 'tickets.db')
    backup_path = os.path.join(os.path.dirname(__file__), f'tickets_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"Database backed up to {backup_path}")
        return True
    else:
        print("No database file found to backup")
        return False

def update_responses_table():
    """Add the tech_instructions column to the responses table."""
    db_path = os.path.join(os.path.dirname(__file__), 'tickets.db')
    print(f"Using database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the responses table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='responses'")
        if not cursor.fetchone():
            print("The responses table does not exist in the database")
            conn.close()
            return False
        
        # Check if the tech_instructions column already exists
        cursor.execute("PRAGMA table_info(responses)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Existing columns in responses table: {column_names}")
        
        if 'tech_instructions' in column_names:
            print("The tech_instructions column already exists in the responses table")
            conn.close()
            return True
        
        # Create a new table with the correct schema
        cursor.execute("""
        CREATE TABLE responses_new (
            id INTEGER PRIMARY KEY,
            ticket_id INTEGER NOT NULL,
            draft_content TEXT,
            final_content TEXT,
            tech_instructions TEXT,
            is_final_solution BOOLEAN DEFAULT 0,
            is_sent BOOLEAN DEFAULT 0,
            created_at DATETIME,
            updated_at DATETIME,
            sent_at DATETIME,
            FOREIGN KEY (ticket_id) REFERENCES tickets (id)
        )
        """)
        
        # Check which columns exist in the current table
        cursor.execute("PRAGMA table_info(responses)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        print(f"Existing columns in responses table: {column_names}")
        
        # Prepare the SQL statements based on existing columns
        insert_columns = ["id", "ticket_id"]
        select_columns = ["id", "ticket_id"]
        
        # Add columns that exist in the current table
        for col in ["draft_content", "final_content", "is_sent", "created_at", "updated_at", "sent_at"]:
            if col in column_names:
                insert_columns.append(col)
                select_columns.append(col)
        
        print(f"Columns to insert: {insert_columns}")
        print(f"Columns to select: {select_columns}")
        
        # Build the SQL statement
        insert_sql = f"""
        INSERT INTO responses_new (
            {', '.join(insert_columns)}
        )
        SELECT 
            {', '.join(select_columns)}
        FROM responses
        """
        
        print(f"SQL to execute: {insert_sql}")
        
        # Execute the insert
        cursor.execute(insert_sql)
        
        # Drop the old table
        cursor.execute("DROP TABLE responses")
        
        # Rename the new table to the original name
        cursor.execute("ALTER TABLE responses_new RENAME TO responses")
        
        # Commit the changes
        conn.commit()
        print("Successfully added tech_instructions column to responses table")
        return True
    
    except Exception as e:
        conn.rollback()
        print(f"Error updating database: {str(e)}")
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting database update...")
    
    # Backup the database
    if backup_database():
        # Update the responses table
        if update_responses_table():
            print("Database update completed successfully")
        else:
            print("Database update failed")
    else:
        print("Database backup failed, update aborted")
