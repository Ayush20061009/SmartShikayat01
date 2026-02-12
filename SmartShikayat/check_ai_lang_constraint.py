import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(complaints_complaint)')
cols = cursor.fetchall()

ai_lang = [c for c in cols if c[1] == 'ai_language'][0]
print(f'ai_language column details:')
print(f'  Type: {ai_lang[2]}')
print(f'  NOT NULL: {ai_lang[3]}')
print(f'  Default: {ai_lang[4]}')
print()

if ai_lang[3] == 0:
    print('✓ SUCCESS: Column allows NULL values')
else:
    print('✗ ERROR: Column still has NOT NULL constraint')

conn.close()
