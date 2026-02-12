import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(complaints_complaint)')
cols = cursor.fetchall()

print("Columns in complaints_complaint table:")
print("=" * 60)
for row in cols:
    print(f"{row[0]:3d}: {row[1]:30s} {row[2]:10s} NOT NULL={row[3]} DEFAULT={row[4]}")

# Check if ai_language exists
ai_lang_exists = any(col[1] == 'ai_language' for col in cols)
print("\n" + "=" * 60)
print(f"ai_language column exists: {ai_lang_exists}")

conn.close()
