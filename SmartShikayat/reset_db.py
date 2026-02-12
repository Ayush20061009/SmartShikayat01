"""
Script to forcefully close database connections and reset the database.
This handles the case where the database file is locked by running processes.
"""
import os
import sys
import time
import subprocess
import sqlite3

DB_PATH = 'db.sqlite3'

print("=" * 60)
print("Database Reset Script")
print("=" * 60)

# Step 1: Kill Python processes
print("\n1. Stopping all Python processes...")
try:
    subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                   capture_output=True, check=False)
    time.sleep(2)
    print("   ✓ Python processes stopped")
except Exception as e:
    print(f"   ⚠ Warning: {e}")

# Step 2: Try to close any open connections
print("\n2. Closing database connections...")
try:
    if os.path.exists(DB_PATH):
        # Try to connect and close immediately
        conn = sqlite3.connect(DB_PATH)
        conn.close()
        print("   ✓ Database connections closed")
except Exception as e:
    print(f"   ⚠ Warning: {e}")

# Step 3: Delete database
print("\n3. Deleting database file...")
max_attempts = 5
for attempt in range(max_attempts):
    try:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
            print(f"   ✓ Database deleted successfully")
            break
        else:
            print(f"   ℹ Database file doesn't exist")
            break
    except PermissionError:
        if attempt < max_attempts - 1:
            print(f"   ⏳ Attempt {attempt + 1}/{max_attempts} failed, retrying...")
            time.sleep(1)
        else:
            print(f"   ✗ ERROR: Could not delete database after {max_attempts} attempts")
            print(f"   The file is still locked by another process.")
            print(f"\n   Manual steps:")
            print(f"   1. Close ALL terminal windows")
            print(f"   2. Open Task Manager and end all python.exe processes")
            print(f"   3. Delete db.sqlite3 manually")
            print(f"   4. Run: python manage.py migrate")
            sys.exit(1)

# Step 4: Run migrations
print("\n4. Running migrations...")
try:
    result = subprocess.run([sys.executable, 'manage.py', 'migrate'],
                          capture_output=True, text=True, check=True)
    print("   ✓ Migrations completed successfully")
except subprocess.CalledProcessError as e:
    print(f"   ✗ Migration failed: {e}")
    print(f"   Output: {e.output}")
    sys.exit(1)

# Step 5: Verify schema
print("\n5. Verifying database schema...")
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('PRAGMA table_info(complaints_complaint)')
    cols = cursor.fetchall()
    
    ai_lang = [c for c in cols if c[1] == 'ai_language']
    if ai_lang:
        col_info = ai_lang[0]
        if col_info[3] == 0:  # NOT NULL = 0 means it allows NULL
            print(f"   ✓ ai_language column is correctly configured (allows NULL)")
        else:
            print(f"   ✗ ERROR: ai_language still has NOT NULL constraint!")
            sys.exit(1)
    else:
        print(f"   ✗ ERROR: ai_language column not found!")
        sys.exit(1)
    
    conn.close()
except Exception as e:
    print(f"   ✗ Verification failed: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ SUCCESS! Database has been reset.")
print("=" * 60)
print("\nYou can now start the server:")
print("  python manage.py runserver")
print()
