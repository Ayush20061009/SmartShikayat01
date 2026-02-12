import sqlite3

# Connect to the database
conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Query the accounts_user table
cursor.execute("""
    SELECT id, username, email, phone, role, vehicle_number 
    FROM accounts_user 
    ORDER BY id
""")

rows = cursor.fetchall()

print("=" * 100)
print("ACCOUNTS_USER TABLE - EMAIL DATA")
print("=" * 100)
print(f"\nTotal Records: {len(rows)}\n")

# Print header
print(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Vehicle':<15} {'Phone':<15}")
print("-" * 100)

# Print data
for row in rows:
    id_val, username, email, phone, role, vehicle = row
    email = email or "(empty)"
    vehicle = vehicle or "N/A"
    phone = phone or "N/A"
    print(f"{id_val:<5} {username:<20} {email:<30} {role:<10} {vehicle:<15} {phone:<15}")

print("\n" + "=" * 100)

# Save to file
with open('db_accounts_user.txt', 'w', encoding='utf-8') as f:
    f.write("=" * 100 + "\n")
    f.write("ACCOUNTS_USER TABLE - EMAIL DATA\n")
    f.write("=" * 100 + "\n")
    f.write(f"\nTotal Records: {len(rows)}\n\n")
    f.write(f"{'ID':<5} {'Username':<20} {'Email':<30} {'Role':<10} {'Vehicle':<15} {'Phone':<15}\n")
    f.write("-" * 100 + "\n")
    
    for row in rows:
        id_val, username, email, phone, role, vehicle = row
        email = email or "(empty)"
        vehicle = vehicle or "N/A"
        phone = phone or "N/A"
        f.write(f"{id_val:<5} {username:<20} {email:<30} {role:<10} {vehicle:<15} {phone:<15}\n")
    
    f.write("\n" + "=" * 100 + "\n")

print("\nData saved to db_accounts_user.txt")

conn.close()
