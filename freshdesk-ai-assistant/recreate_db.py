#!/usr/bin/env python3
import os
import sys
import shutil
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.models import init_db

def backup_database():
    """Create a backup of the database file."""
    db_path = os.path.join(os.path.dirname(__file__), 'tickets.db')
    backup_path = os.path.join(os.path.dirname(__file__), f'tickets_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
    
    if os.path.exists(db_path):
        shutil.move(db_path, backup_path)
        print(f"Database moved to {backup_path}")
        return True
    else:
        print("No database file found to backup")
        return False

if __name__ == "__main__":
    print("Starting database recreation...")
    
    # Backup the database
    if backup_database():
        # Create a new database
        init_db()
        print("New database created successfully with the correct schema")
    else:
        print("Database backup failed, recreation aborted")
